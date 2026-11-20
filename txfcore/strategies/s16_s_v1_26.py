"""S16_S MACrossShort v1.26.0 —— Python 移植（研究用，對 MC12 逐筆）。

兩個 build：
  260820  `S16_S_MACrossShort_v1.26.0.pla.bak_20260821`（28 型擋人濾網版）
          考題：MC12 報表 161 筆（ReEntry_Filt_Mode = 1），tests/test_port_s16_v1_26.py
  260825  `S16_S_MACrossShort_v1.26.0.pla`（現行：濾網刪除、33 型、KB_Entry_Mode/BullExit 預設 0）

TODO（11/20 期限後）：照專案規則拆進 txfcore/modules、參數搬 config/strategies/*.toml、
改用 runtime/backtest 的通用撮合。現在是單檔自帶撮合，理由：S16 同根有買停損＋買限價＋
引擎停損，通用 runner 的同根多單處理未對 S16 驗證過；單檔可逐條對 .pla 行號審查。

撮合假設（MC12 傳統模式、IOG 關），由 161 筆逐筆考題實證：
  - 訊號在 K 棒收盤產生，下一根成交；市價單＝下一根開盤價
  - 停損／限價價位進位到整點（買停損往上、買限價往下、賣停損往下）
  - 開盤已越過觸發價 → 成交在開盤價
  - 同根多張出場單：市價優先；否則依 K 棒路徑（開盤離高點近 → 先高後低，反之先低後高）
  - SetStopLoss 只在空手時呼叫 → 引擎停損只在進場那根有效，標籤 "Stop Loss"
  - 成本：每口每邊 1,000 元（市價、停損），限價單不計；2 口、1 點 200 元
"""
from __future__ import annotations

import math
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[2]
PLA_DIR = ROOT / "strategies/research/S16_MACrossShort"
PLA_260820 = PLA_DIR / "S16_S_MACrossShort_v1.26.0.pla.bak_20260821"
PLA_260825 = PLA_DIR / "S16_S_MACrossShort_v1.26.0.pla"
PLA_261118 = PLA_DIR / "S16_S_MACrossShort_v1.27.0_candidate.pla"   # 研究候選：260825 ＋ Vol_Gate_Pct
PLA_2611181 = PLA_DIR / "S16_S_MACrossShort_v1.28.0_candidate.pla"  # 研究候選：＋同時段門檻 TOD_Gate_Days／Q
PLA_2611191 = PLA_DIR / "S16_S_MACrossShort_v1.28.1_candidate.pla"  # 研究候選：B 預設（90 日）＋2027 假日表
PLA_L6_V100 = PLA_DIR.parent / "L6_MACrossShort/L6_v1.0.0/L6_MACrossShort_v1.0.0.pla"  # 上架候選：＝v1.28.1 B，Build 2611193
PLA_2611192 = PLA_DIR / "S16_S_MACrossShort_v1.29.0_candidate.pla"  # 研究候選：大殺盤 6 個 input（全 0 ＝ v1.28.1）

BPV = 200.0
QTY = 2
SLIP_PER_LOT_SIDE = 1000.0
MAX_BARS_BACK = 100
BAR_MIN = 5


# ---------------------------------------------------------------- 參數
def pla_params(path: Path) -> dict:
    """依宣告順序解析 inputs（去註解）。布林字串轉 bool，其餘 float。"""
    txt = re.sub(r"\{[^}]*\}", "", path.read_text(encoding="utf-8", errors="replace"))
    m = re.search(r"\binputs\s*:(.*?);", txt, re.S | re.I)
    out: dict = {}
    for name, val in re.findall(r"(\w+)\s*\(\s*([^)]*?)\s*\)", m.group(1)):
        v = val.strip()
        out[name] = (v.lower() == "true") if v.lower() in ("true", "false") else float(v)
    return out


def holiday_tail(path: Path) -> set[int]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    return {int(d) for d in re.findall(r"Holiday_Tail\[\d+\]\s*=\s*(\d+)\s*;", txt)}


def params_from_mc_vector(path: Path, vector: str) -> dict:
    """MC 設定頁的參數向量 "(260820, 25, ...)" 依宣告順序對到 inputs。數量必須相等。"""
    p = pla_params(path)
    vals = [v.strip() for v in vector.strip().strip("()").split(",")]
    if len(vals) != len(p):
        raise ValueError(f"參數向量 {len(vals)} 個，.pla inputs {len(p)} 個")
    out = {}
    for (k, d), v in zip(p.items(), vals):
        out[k] = (v.lower() == "true") if isinstance(d, bool) else float(v)
    return out


# ---------------------------------------------------------------- 資料
@dataclass(slots=True)
class Bar5:
    dt: datetime          # 收盤戳記
    o: float
    h: float
    l: float
    c: float
    v: float

    @property
    def mc_date(self) -> int:
        return (self.dt.year - 1900) * 10000 + self.dt.month * 100 + self.dt.day

    @property
    def mc_time(self) -> int:
        return self.dt.hour * 100 + self.dt.minute


def _in_session(mins: int) -> bool:
    """1 分 K 收盤戳記（當日分鐘數）是否在交易時段：日盤 08:46–13:45、夜盤 15:01–05:00。"""
    return (526 <= mins <= 825) or mins >= 901 or mins <= 300


def aggregate_5m(minutes: Iterable, start: datetime | None = None,
                 end: datetime | None = None) -> list[Bar5]:
    """1 分 K（txfcore Bar）→ 5 分 K。收盤戳記往上取到 5 分；23:56–24:00 戳 隔日 00:00。

    與 txfcore.quotes.bars.aggregate_bars 同語意（半開半閉、以收盤戳記），只是用算術取格，
    一分鐘一次查表太慢（7 年 230 萬根）。tests 裡有一個月份的等價比對。
    """
    out: list[Bar5] = []
    cur_key = None
    for m in minutes:
        d = m.mc_date
        dd = date(1900 + d // 10000, d // 100 % 100, d % 100)
        t = m.mc_time
        mins = (t // 100) * 60 + t % 100
        if not _in_session(mins):
            continue
        dt = datetime(dd.year, dd.month, dd.day, t // 100, t % 100)
        if start and dt < start:
            continue
        if end and dt > end:
            break
        up = -(-mins // BAR_MIN) * BAR_MIN
        key = datetime(dd.year, dd.month, dd.day) + timedelta(minutes=up)
        if key != cur_key:
            out.append(Bar5(key, m.open, m.high, m.low, m.close, m.volume))
            cur_key = key
        else:
            b = out[-1]
            b.h = max(b.h, m.high)
            b.l = min(b.l, m.low)
            b.c = m.close
            b.v += m.volume
    return out


# ---------------------------------------------------------------- 交易紀錄
@dataclass(slots=True)
class Trade:
    entry_dt: datetime
    entry_label: str
    entry_px: float
    exit_dt: datetime | None = None
    exit_label: str = ""
    exit_px: float = 0.0
    entry_slip: float = 0.0
    exit_slip: float = 0.0
    sig_i: int = -1          # 研究用：訊號那根的 bars 索引（不影響撮合）

    @property
    def net_ntd(self) -> float:
        return (self.entry_px - self.exit_px) * BPV * QTY - self.entry_slip - self.exit_slip


@dataclass(slots=True)
class Order:
    kind: str        # MKT / STP / LMT
    side: str        # SS (sell short) / BC (buy to cover)
    label: str
    price: float = 0.0


def _tick(price: float, kind: str, side: str) -> float:
    if kind == "MKT":
        return price
    up = (side == "BC" and kind == "STP")          # 買停損往上；買限價、賣停損往下
    return float(math.ceil(price - 1e-9)) if up else float(math.floor(price + 1e-9))


def _dow_mc(d: datetime) -> int:     # MC DayOfWeek：0 = 週日
    return (d.weekday() + 1) % 7


def _t2m(t: int) -> int:
    return (t // 100) * 60 + t % 100


def _m2t(m: int) -> int:
    m %= 1440
    return (m // 60) * 100 + m % 60


# ---------------------------------------------------------------- 策略
@dataclass
class S16Result:
    trades: list[Trade] = field(default_factory=list)
    build: int = 0


def run(bars: list[Bar5], params: dict, holidays: set[int], veto=None, on_signal=None,
        reentry_veto=None) -> S16Result:
    """研究掛鉤，預設 None ＝ 與 MC 逐筆相同。
    veto(i, trades) 回 True ＝ 擋掉第 i 根的死亡交叉進場；on_signal(i, mp) 在每個合格死亡交叉訊號呼叫（含持倉中）；
    reentry_veto(i, trades) 回 True ＝ 擋掉第 i 根掛出的再進場停損單（研究用，.pla 沒有對應）。"""
    p = params
    build = int(p["Build_ID"])
    new = "KB_Entry_Mode" in p                    # 260825 起
    if new:
        assert p["KB_Entry_Mode"] == 0 and p["BullExit_Mode"] == 0, "只移植預設 0（未啟用的路徑）"
    assert p["ML_On"] == 0 and p["Trail_On"] == 0 and p["Tier2_On"] == 0 and p["Slope_Form"] == 2
    assert p["UpGap_Gate_On"] == 0 and p["Slope_Require_Adjacent"] == 0

    O = [b.o for b in bars]; H = [b.h for b in bars]; L = [b.l for b in bars]; C = [b.c for b in bars]
    res = S16Result(build=build)

    fast_lag = int((p["ZLEMA_Fast"] - 1) / 2)
    slow_lag = int((p["ZLEMA_Slow"] - 1) / 2)
    kf, ks = 2.0 / (p["ZLEMA_Fast"] + 1), 2.0 / (p["ZLEMA_Slow"] + 1)
    atr_len = int(p["ATR_Len"])
    tod_days = int(min(p.get("TOD_Gate_Days", 0), 120))   # v1.28.0 候選；0 或不存在 ＝ 關
    tod_q = p.get("TOD_Gate_Q", 0.0)
    tod_buf: dict[int, deque] = {}
    # v1.29.0 候選（大殺盤，2026-11-19）：全部預設 0 ＝ 關 ＝ v1.28.1 逐筆相同
    c30 = p.get("Crash30_Pct", 0.0)          # 1. 本盤 30 分鐘內最高到收盤跌 ≥ X% → 放空
    c60 = p.get("Crash60_Pct", 0.0)          # 2. 本盤 60 分鐘內 ≥ Y%
    dtr = p.get("DayTrend_Pct", 0.0)         # 3. 日盤從開盤跌 ≥ Z% 且收盤創日盤新低
    cday = p.get("CrashDay_Pct", 0.0)        # 4. 本盤從開盤已跌 ≥ D% 時不掛 2.3% 停利
    cont_on = p.get("ContRe_On", 0.0) != 0   # 5. 獲利出場後同一盤跌破交易期間最低點 → 停損單再空
    crash_struct = p.get("Crash_Struct", 0.0) != 0   # 第 2 版：1–3 只在 ZLEMA 快線 < 慢線時
    fired30 = fired60 = fired_dt = False
    sess_low = 0.0                           # 本盤到上一根為止的最低價（0 ＝ 本盤還沒有前一根）
    trade_low = 0.0
    cont_armed = False
    cont_px = 0.0

    # 跨根變數（MC 的 variables）
    zf = zs = None
    zf1 = zs1 = 0.0
    in_day1 = in_night1 = False
    bars_in_sess = 0
    gap_pct = 0.0
    f_o = f_h = f_l = f_c = 0.0
    first_rise = 0.0
    kb_type = 0
    slope_age = clean_age = 999
    kb = dict(R2=0.0, B2=0.0, T2=0.0, M2=0.0, S2=0.0, N2=0.0, L2=False,
              R3=0.0, R4=0.0, B3=0.0, B4=0.0, L3=False, L4=False)
    re_armed = False
    re_price = 0.0
    last_entry = 0.0
    is_reentry = False
    sl_locked = False
    frozen_atr = orig_frozen_atr = 0.0
    sl_level = 0.0
    entry_bar = 0
    qs_fired = be_active = struct_active = False
    max_profit = 0.0
    struct_lock = 0.0
    prev_mp = 0

    pos = 0
    trade: Trade | None = None
    entry_px = 0.0
    pending: list[Order] = []
    guard_dist_for_next = 0.0

    def close_trade(dt, label, px, slip):
        nonlocal pos, trade
        trade.exit_dt, trade.exit_label, trade.exit_px, trade.exit_slip = dt, label, px, slip
        res.trades.append(trade)
        trade = None
        pos = 0

    for i in range(len(bars)):
        b = bars[i]
        # ======== 撮合：上一根收盤掛的單，在這一根成交 ========
        if i > 0 and pending:
            orders, pending = pending, []
            if pos == 0:
                e = orders[0]
                fill = None
                if e.kind == "MKT":
                    fill = (b.o, "open")
                else:                                   # 賣出停損（再進場）
                    px = _tick(e.price, "STP", "SS")
                    if b.o <= px:
                        fill = (b.o, "open")
                    elif b.l <= px:
                        fill = (px, "intrabar")
                if fill:
                    pos, entry_px = -1, fill[0]
                    trade = Trade(b.dt, e.label, entry_px, entry_slip=SLIP_PER_LOT_SIDE * QTY, sig_i=i - 1)
                    # 引擎停損（SetStopLoss，進場那根有效）
                    stop = _tick(entry_px + guard_dist_for_next, "STP", "BC")
                    if fill[1] == "open":
                        hit = b.h >= stop
                    else:                               # 盤中進場：之後的路徑
                        high_first = (b.h - b.o) <= (b.o - b.l)
                        hit = (b.c >= stop) if high_first else (b.h >= stop)
                    if hit:
                        close_trade(b.dt, "Stop Loss", stop, SLIP_PER_LOT_SIDE * QTY)
            elif pos == -1:
                mkt = [o for o in orders if o.kind == "MKT"]
                if mkt:
                    close_trade(b.dt, mkt[0].label, b.o, SLIP_PER_LOT_SIDE * QTY)
                else:
                    stops = [(o, _tick(o.price, "STP", "BC")) for o in orders if o.kind == "STP"]
                    lims = [(o, _tick(o.price, "LMT", "BC")) for o in orders if o.kind == "LMT"]
                    done = False
                    gs = [s for s in stops if b.o >= s[1]]
                    if gs:
                        close_trade(b.dt, gs[0][0].label, b.o, SLIP_PER_LOT_SIDE * QTY); done = True
                    gl = [s for s in lims if b.o <= s[1]]
                    if not done and gl:
                        close_trade(b.dt, gl[0][0].label, b.o, 0.0); done = True
                    if not done:
                        high_first = (b.h - b.o) <= (b.o - b.l)
                        hs = sorted([s for s in stops if b.h >= s[1]], key=lambda s: s[1])
                        hl = sorted([s for s in lims if b.l <= s[1]], key=lambda s: -s[1])
                        first, second = ((hs, "S"), (hl, "L")) if high_first else ((hl, "L"), (hs, "S"))
                        for grp, k in (first, second):
                            if grp:
                                o, px = grp[0]
                                close_trade(b.dt, o.label, px, SLIP_PER_LOT_SIDE * QTY if k == "S" else 0.0)
                                break
        cb = i - MAX_BARS_BACK + 1        # MC CurrentBar
        if cb < 1:
            continue
        mp = pos
        t = b.mc_time
        dte = b.mc_date

        # ======== SECTION 3 合規 ========
        registry_expired = dte > p["Registry_Valid_Until"]
        holiday = (t <= 500 and dte in holidays) or registry_expired
        settle = _dow_mc(b.dt) == 3 and 15 <= b.dt.day <= 21

        # ======== SECTION 4 ZLEMA ========
        pf = 2 * C[i] - C[i - fast_lag]
        ps_ = 2 * C[i] - C[i - slow_lag]
        zf1, zs1 = (zf if zf is not None else 0.0), (zs if zs is not None else 0.0)
        zf = pf if zf is None else zf + kf * (pf - zf)
        zs = ps_ if zs is None else zs + ks * (ps_ - zs)

        # ======== SECTION 4.5 時段 ========
        in_day = 845 < t <= 1345
        in_night = t > 1500 or t <= 500
        gap_min = 0
        if cb > 1:
            gap_min = (b.dt.date() - bars[i - 1].dt.date()).days * 1440 + \
                      (_t2m(t) - _t2m(bars[i - 1].mc_time))
        gap_seen = p["Sess_GapReset_On"] != 0 and cb > 1 and gap_min > BAR_MIN
        day_first = night_first = False
        if cb > 1:
            day_first = in_day and (not in_day1 or gap_seen)
            night_first = in_night and (not in_night1 or gap_seen)
        sess_first = day_first or night_first
        if sess_first:
            bars_in_sess = 1
        elif in_day or in_night:
            bars_in_sess += 1
        else:
            bars_in_sess = 0
        sess_last = (in_day and t == p["Sess_Day_End"]) or (in_night and t == p["Sess_Night_End"])
        if sess_first:
            fired30 = fired60 = fired_dt = False
            sess_low = 0.0
            cont_armed = False
        if sess_first:
            gap_pct = (O[i] - C[i - 1]) / C[i - 1] * 100 if C[i - 1] > 0 else 0.0
            f_o, f_h, f_l, f_c = O[i], H[i], L[i], C[i]
            first_rise = (C[i] - O[i]) / O[i] * 100 if O[i] > 0 else 0.0
            rng = f_h - f_l
            up = f_c > f_o
            if rng <= 0:
                kb_type = 0
            else:
                body = abs(f_c - f_o) / rng
                ush = (f_h - max(f_o, f_c)) / rng
                dsh = (min(f_o, f_c) - f_l) / rng
                sr = p["KB_Shadow_Ratio"]
                if body >= p["KB_Body_Long"]:
                    kb_type = 1 if up else 2
                elif body >= p["KB_Body_Mid"]:
                    kb_type = (3 if up else 4) if dsh >= sr * ush else (5 if up else 6) if ush >= sr * dsh else (7 if up else 8)
                elif body >= p["KB_Body_Small"]:
                    kb_type = (9 if up else 10) if dsh >= sr * ush else (11 if up else 12) if ush >= sr * dsh else (13 if up else 14)
                else:
                    kb_type = 15 if dsh >= sr * ush else 16 if ush >= sr * dsh else 17

        gap_block = False
        if p["Gap_Filter_On"] != 0 and 1 <= bars_in_sess <= p["Gap_Scope_Bars"]:
            if (in_day and p["Gap_Day_On"] != 0) or (in_night and p["Gap_Night_On"] != 0):
                if gap_pct <= -p["Gap_Down_Min_Pct"] and first_rise >= p["Gap_Rise_Min_Pct"]:
                    gap_block = True
        g = p["Gap_KB_Group"]
        in_group = kb_type in ((5, 6, 11, 12, 16) if g == 2 else (7, 8, 13, 14, 17) if g == 3 else (3, 4, 9, 10, 15))
        if p["Gap_KB_Gate_On"] != 0 and 1 <= bars_in_sess <= p["Gap_KB_Scope_Bars"] \
                and gap_pct <= -p["Gap_Down_Min_Pct"] and in_group:
            gap_block = True
        last_block = p["Sess_LastBar_Block_On"] != 0 and sess_last
        tail_cut = _m2t(_t2m(int(p["Tail_NoEntry_From"])) - int(p["Tail_Signal_Lead_Bars"]) * BAR_MIN)
        day_cut = _m2t(_t2m(int(p["Tail_DayNoEntry_From"])) - int(p["Tail_Signal_Lead_Bars"]) * BAR_MIN)
        tail_ok = (in_day and t <= day_cut) or (in_night and (t <= tail_cut or t > 500))

        # ======== SECTION 5 交叉 ========
        death = zf1 >= zs1 and zf < zs
        golden = zf1 <= zs1 and zf > zs

        # ======== SECTION 5.5 再進場狀態 ========
        if prev_mp == -1 and mp == 0:
            re_armed, re_price = True, last_entry
            if cont_on and res.trades and res.trades[-1].exit_px < res.trades[-1].entry_px:
                cont_armed, cont_px = True, min(trade_low, L[i])
        if cont_armed and (golden or zf >= zs):
            cont_armed = False
        if re_armed and (golden or zf >= zs):
            re_armed, re_price = False, 0.0
        if death:
            re_armed, re_price = False, 0.0

        # ======== SECTION 6–7 ATR、凍結停損、引擎停損距離 ========
        atr = 0.0
        for k in range(atr_len):
            j = i - k
            atr += max(H[j], C[j - 1]) - min(L[j], C[j - 1])
        atr /= atr_len
        if mp == -1:
            last_entry = entry_px
            trade_low = L[i] if prev_mp != -1 else min(trade_low, L[i])
            cont_armed = False
            if not sl_locked:
                if is_reentry and orig_frozen_atr > 0:
                    frozen_atr = orig_frozen_atr
                else:
                    frozen_atr = orig_frozen_atr = atr
                sl_level = entry_px + frozen_atr * p["StopATRMult"]
                if p["SL_Pct"] > 0:
                    sl_level = min(sl_level, entry_px + entry_px * p["SL_Pct"] / 100)
                sl_locked = True
                entry_bar = cb
                qs_fired = be_active = struct_active = False
                max_profit = 0.0
                struct_lock = 0.0
        else:
            sl_locked = False
            sl_level = 0.0
            entry_bar = 0
            qs_fired = be_active = struct_active = False
            max_profit = 0.0
            struct_lock = 0.0
        guard = atr * p["StopATRMult"]
        if p["SL_Pct"] > 0:
            guard = min(guard, C[i] * p["SL_Pct"] / 100)
        if mp >= 0:
            guard_dist_for_next = guard

        # ======== SECTION 8.5 斜率 ========
        if cb > 1:
            el = _t2m(t) - _t2m(bars[i - 1].mc_time)
            if el <= 0:
                el += 1440
        else:
            el = 0
        slope_rate = ((C[i - 1] - C[i]) / C[i] * 100) / el if (C[i] != 0 and el > 0) else 0.0
        slope_pass = slope_rate > p["MinSlope_Rate"]

        # ======== SECTION 8.6 K 棒型態 ========
        code = _kb_code(p, new, O, H, L, C, i, bars_in_sess, kb)

        # ======== SECTION 8.7 / 9 進場 ========
        if new:
            bull_now = (16 <= code <= 28) or (p["KB_Gap_Pat"] != 0 and 31 <= code <= 33)
            filt_pass = (not bull_now) and death and slope_pass
            re_filt_ok = not bull_now
            dc_gate = filt_pass
        else:
            block = code != 0
            if slope_pass:
                slope_age = 0
            elif bars_in_sess <= 1:
                slope_age = 999
            else:
                slope_age += 1
            if not block:
                clean_age = 0
            elif bars_in_sess <= 1:
                clean_age = 999
            else:
                clean_age += 1
            mode, win = p["KB_Filter_Mode"], p["KB_Filter_Win"]
            if mode == 1:
                filt_pass = slope_age <= win and clean_age == 0
            elif mode == 2:
                filt_pass = clean_age <= win and slope_age == 0
            elif mode == 3:
                filt_pass = (slope_age <= win and clean_age == 0) or (clean_age <= win and slope_age == 0)
            else:
                filt_pass = slope_age == 0 and clean_age == 0
            re_filt_ok = filt_pass if p["ReEntry_Filt_Mode"] != 0 else (not block)
            dc_gate = death and filt_pass

        common = (tail_ok and not settle and not holiday and not registry_expired
                  and not p["Manual_Kill_Switch"] and not gap_block and not last_block)
        new_orders: list[Order] = []
        if dc_gate and common and on_signal is not None:
            on_signal(i, mp)
        vg = p.get("Vol_Gate_Pct", 0)                 # v1.27.0 候選（261118）；0 或不存在 ＝ 260825
        vol_ok = vg <= 0 or (C[i] > 0 and atr / C[i] * 100 >= vg)
        # v1.28.0 候選（2611181）SECTION 8.9 同時段波動門檻：先用同一 HH:MM 過去的值算門檻，再存這一根
        # v1.29.0 候選：三種下殺發動（不需要死亡交叉）
        crash_lab = ""
        if (mp == 0 and (c30 > 0 or c60 > 0 or dtr > 0) and bars_in_sess >= 2 and (not new or not bull_now)
                and (not crash_struct or zf < zs)):
            for on, k, lab in ((c30 > 0 and not fired30, 6, "SE_MA_Crash30"), (c60 > 0 and not fired60, 12, "SE_MA_Crash60")):
                if on and not crash_lab:
                    w = min(k, bars_in_sess)
                    hi = max(H[i - w + 1:i + 1])
                    if hi > 0 and (hi - C[i]) / hi * 100 >= (c30 if k == 6 else c60):
                        crash_lab = lab
            if (not crash_lab and dtr > 0 and not fired_dt and in_day and f_o > 0 and sess_low > 0
                    and (f_o - C[i]) / f_o * 100 >= dtr and C[i] < sess_low):
                crash_lab = "SE_MA_DayTrend"
        tod_ok = True
        if tod_days > 0 and C[i] > 0:
            ap_now = atr / C[i] * 100
            hist = tod_buf.setdefault((t // 100) * 12 + (t % 100) // 5, deque(maxlen=tod_days))
            if mp == 0 and (dc_gate or crash_lab) and len(hist) >= tod_days // 2:
                srt = sorted(hist)
                # 百分位索引取「數學上的」IntPortion(N×Q)：90×0.70 在浮點是 62.999…，MC 報表顯示 MC 取 63
                # （2026-11-19 對 MC v1281c 報表逐筆查到 2021-05-25 12:15 一筆），所以加 1e-9 再取整
                tod_ok = ap_now >= srt[min(len(srt) - 1, int(len(srt) * tod_q + 1e-9))]
            hist.append(ap_now)
        if mp == 0 and dc_gate and common and vol_ok and tod_ok and (veto is None or not veto(i, res.trades)):
            is_reentry = False
            new_orders.append(Order("MKT", "SS", "SE_MA_DeathCross"))
        elif mp == 0 and crash_lab and common and tod_ok:
            is_reentry = False
            new_orders.append(Order("MKT", "SS", crash_lab))
            fired30 = fired30 or crash_lab == "SE_MA_Crash30"
            fired60 = fired60 or crash_lab == "SE_MA_Crash60"
            fired_dt = fired_dt or crash_lab == "SE_MA_DayTrend"
        if mp == 0 and cont_armed and zf < zs and common and not new_orders:
            is_reentry = False
            new_orders.append(Order("STP", "SS", "SE_MA_ContRe", cont_px))
        if (mp == 0 and p["ReEntry_On"] != 0 and re_armed
                and (p["ReEntry_Structure_Gate"] == 0 or zf < zs)
                and (p["ReEntry_Slope_Gate"] == 0 or slope_pass)
                and re_filt_ok
                and (p["ReEntry_Close_Gate"] == 0 or C[i] >= re_price)
                and common
                and (reentry_veto is None or not reentry_veto(i, res.trades))):
            is_reentry = True
            new_orders.append(Order("STP", "SS", "SE_MA_ReEntry", re_price))

        # ======== SECTION 10 出場鏈 ========
        if mp == -1:
            fired = False
            bars_since = cb - entry_bar
            loss = C[i] - entry_px
            profit = entry_px - C[i]
            if p["Manual_Kill_Switch"]:
                new_orders.append(Order("MKT", "BC", "SX_MA_Kill")); fired = True
            if not fired and registry_expired:
                new_orders.append(Order("MKT", "BC", "SX_MA_Registry")); fired = True
            if not fired and holiday and t >= p["Holiday_Flat_Time"]:
                new_orders.append(Order("MKT", "BC", "SX_MA_Holiday")); fired = True
            if not fired and settle and t >= p["Settlement_Flat_Time"]:
                new_orders.append(Order("MKT", "BC", "SX_MA_Settlement")); fired = True
            if not fired and t >= p["Tail_ForceExit_Time"] and t <= 500:
                new_orders.append(Order("MKT", "BC", "SX_MA_TailFlat")); fired = True
            if not fired and p["QuickStop_On"] != 0 and not qs_fired:
                if p["QS_Loss_On"] != 0 and loss > entry_px * p["QS_MaxLoss_Pct"] / 100:
                    new_orders.append(Order("MKT", "BC", "SX_MA_QuickStop_Loss"))
                    qs_fired = fired = True
                if not fired and p["QS_Time_On"] != 0 and bars_since >= p["QuickStop_MaxBars"] \
                        and C[i] >= entry_px:
                    new_orders.append(Order("MKT", "BC", "SX_MA_QuickStop_Time"))
                    qs_fired = fired = True
            if profit > max_profit:
                max_profit = profit
            if p["BE_On"] != 0 and profit >= entry_px * p["BE_Trigger_Pct"] / 100:
                be_active = True
            if p["Struct_On"] != 0 and max_profit >= entry_px * p["Struct_Trigger_Pct"] / 100:
                struct_active = True
            protect = 0.0
            s_bind = False
            if p["BE_On"] != 0 and be_active:
                protect = p["BE_Cost_Pts"]
            if p["Struct_On"] != 0 and struct_active:
                w = max(1, min(int(p["Struct_Lookback"]), bars_since + 1))
                ref = max(C[i - w + 1:i + 1]) if p["Struct_UseClose"] != 0 else max(H[i - w + 1:i + 1])
                raw = entry_px - (ref + p["Struct_Buffer_Pts"])
                if raw > struct_lock:
                    struct_lock = raw
                if struct_lock > protect:
                    protect = struct_lock
                    s_bind = True
            if not fired and protect > 0:
                new_orders.append(Order("STP", "BC", "SX_MA_Struct" if s_bind else "SX_MA_BE",
                                        entry_px - protect))
            if not fired and golden:
                new_orders.append(Order("MKT", "BC", "SX_MA_GoldenCross")); fired = True
            if not fired and p["M8_On"] != 0:
                crash_day = cday > 0 and f_o > 0 and (f_o - C[i]) / f_o * 100 >= cday
                if p["M8_Form"] == 2 and not crash_day:
                    new_orders.append(Order("LMT", "BC", "SX_MA_TimeStop_Pct",
                                            entry_px - entry_px * p["MaxHold_Pct"] / 100))
                if bars_since >= p["MaxHoldingBars"]:
                    new_orders.append(Order("MKT", "BC", "SX_MA_TimeStop")); fired = True
            if not fired and sl_locked:
                new_orders.append(Order("STP", "BC", "SX_MA_SL", sl_level))

        pending = new_orders
        if bars_in_sess >= 1:
            sess_low = L[i] if sess_low <= 0 else min(sess_low, L[i])
        in_day1, in_night1 = in_day, in_night
        prev_mp = mp
    return res


def _kb_code(p, new, O, H, L, C, i, n, kb) -> int:
    """SECTION 8.6。`kb` 保存只在較長窗口才重算的變數（MC 變數跨根保留）。"""
    if n < 2:
        return 0
    if not new and not (p["KB_Block_Support"] or p["KB_Block_Oppose"] or p["KB_Block_Neutral"]):
        return 0
    o0, o1, h0, h1, l0, l1, c0, c1 = O[i], O[i - 1], H[i], H[i - 1], L[i], L[i - 1], C[i], C[i - 1]
    LB, MR = p["KB_Pat_LongBody"], p["KB_Pat_MinRange"]
    R0, R1 = h0 - l0, h1 - l1
    B0, B1 = abs(c0 - o0), abs(c1 - o1)
    T0, T1 = max(o0, c0), max(o1, c1)
    M0, M1 = min(o0, c0), min(o1, c1)
    S0, S1 = h0 - T0, h1 - T1
    Lg0 = R0 > 0 and R0 >= MR and B0 / max(R0, 1) >= LB
    Lg1 = R1 > 0 and R1 >= MR and B1 / max(R1, 1) >= LB
    D0 = (R0 >= p["KB_Pat_DojiMinRange"] and B0 / max(R0, 1) < p["KB_Pat_DojiRatio"]
          and S0 >= p["KB_Pat_DojiMinShadow"] and M0 - l0 >= p["KB_Pat_DojiMinShadow"])
    if n >= 3:
        kb["R2"] = H[i - 2] - L[i - 2]
        kb["B2"] = abs(C[i - 2] - O[i - 2])
        kb["T2"] = max(O[i - 2], C[i - 2])
        kb["M2"] = min(O[i - 2], C[i - 2])
        kb["S2"] = H[i - 2] - kb["T2"]
        kb["N2"] = kb["M2"] - L[i - 2]
        kb["L2"] = kb["R2"] > 0 and kb["R2"] >= MR and kb["B2"] / max(kb["R2"], 1) >= LB
    if n >= 5:
        kb["R3"], kb["R4"] = H[i - 3] - L[i - 3], H[i - 4] - L[i - 4]
        kb["B3"], kb["B4"] = abs(C[i - 3] - O[i - 3]), abs(C[i - 4] - O[i - 4])
        kb["L3"] = kb["R3"] > 0 and kb["R3"] >= MR and kb["B3"] / max(kb["R3"], 1) >= LB
        kb["L4"] = kb["R4"] > 0 and kb["R4"] >= MR and kb["B4"] / max(kb["R4"], 1) >= LB
    B2, B3, B4, S2, N2 = kb["B2"], kb["B3"], kb["B4"], kb["S2"], kb["N2"]
    Lg2, Lg3, Lg4 = kb["L2"], kb["L3"], kb["L4"]
    O2 = O[i - 2] if n >= 3 else 0; C2 = C[i - 2] if n >= 3 else 0
    H2 = H[i - 2] if n >= 3 else 0; L2_ = L[i - 2] if n >= 3 else 0
    T1v = T1; M1v = M1

    def g(k):  # 安全取值（只在守衛成立時用到）
        return O[i - k], H[i - k], L[i - k], C[i - k]

    code = 0
    sup = new or p["KB_Block_Support"] != 0
    opp = new or p["KB_Block_Oppose"] != 0
    neu = new or p["KB_Block_Neutral"] != 0

    # ---- 1–13 pro-short ----
    if sup:
        if code == 0 and c1 > o1 and c0 < o0 and o0 >= c1 and c0 <= o1 and B0 > B1: code = 1
        if code == 0 and c1 > o1 and Lg1 and c0 < o0 and T0 <= c1 and M0 >= o1: code = 2
        if code == 0 and c1 > o1 and Lg1 and D0 and T0 <= c1 and M0 >= o1: code = 3
        if code == 0 and h0 == h1 and c1 > o1 and c0 < o0: code = 4
        if code == 0 and c1 > o1 and Lg1 and c0 > o0 and o0 > o1 and c0 == c1: code = 5
        if n >= 3:
            if code == 0 and C2 < O2 and c1 < o1 and c0 < o0 and Lg2 and Lg1 and Lg0 \
                    and c1 < C2 and c0 < c1 and o1 < O2 and o1 > C2 and o0 < o1 and o0 > c1: code = 6
            if code == 0 and C2 > O2 and Lg2 and c1 < o1 and T1v <= C2 and M1v >= O2 \
                    and c0 < o0 and c0 < c1: code = 7
            if code == 0 and C2 > O2 and c1 < o1 and o1 >= C2 and c1 <= O2 and B1 > B2 \
                    and c0 < o0 and c0 < c1: code = 8
            if code == 0 and C2 < O2 and c1 < o1 and c0 < o0 and Lg2 and Lg1 and Lg0 \
                    and o1 == C2 and o0 == c1 and c1 < C2 and c0 < c1: code = 9
            if code == 0 and C2 > O2 and c1 > o1 and c0 > o0 and c1 > C2 and c0 > c1 \
                    and B1 < B2 and B0 < B1 and S1 > 0 and S0 > 0 and S0 > S2: code = 10
            if code == 0 and C2 > O2 and c1 > o1 and c0 > o0 and Lg2 and Lg1 \
                    and c1 > C2 and c0 > c1 and B0 < B1 / 2 and o0 >= c1: code = 11
        if code == 0 and n >= 5:
            o4, h4, l4, c4 = g(4); o3, h3, l3, c3 = g(3)
            if c4 < o4 and Lg4 and c3 > o3 and C2 > O2 and c1 > o1 and B3 < B4 and B2 < B4 and B1 < B4 \
                    and h3 <= h4 and l3 >= l4 and H2 <= h4 and L2_ >= l4 and h1 <= h4 and l1 >= l4 \
                    and c0 < o0 and Lg0 and o0 > c1 and c0 < c4: code = 12
        if code == 0 and n >= 4:
            o3, h3, l3, c3 = g(3)
            if c3 > o3 and C2 > O2 and c1 > o1 and O2 > o3 and o1 > O2 and C2 > c3 and c1 > C2 \
                    and c0 < o0 and o0 > c1 and c0 < o3: code = 13
        if new:
            if code == 0 and n >= 5:
                o4, h4, l4, c4 = g(4); o3, h3, l3, c3 = g(3)
                if h3 <= h4 and l3 >= l4 and H2 > h3 and L2_ > l3 and l0 < l3: code = 14
            if code == 0 and c1 > o1 and c0 > o0 and T0 <= c1 and M0 >= o1 and B0 < B1: code = 15

    # ---- anti-short（舊 14–26／新 16–28）----
    base = 15 if new else 13
    if opp:
        if code == 0 and c1 < o1 and c0 > o0 and o0 <= c1 and c0 >= o1 and B0 > B1: code = base + 1
        if code == 0 and c1 < o1 and Lg1 and c0 > o0 and T0 <= o1 and M0 >= c1: code = base + 2
        if code == 0 and c1 < o1 and Lg1 and D0 and T0 <= o1 and M0 >= c1: code = base + 3
        if code == 0 and l0 == l1 and c1 < o1 and c0 > o0: code = base + 4
        if code == 0 and c1 < o1 and Lg1 and c0 < o0 and o0 < o1 and c0 == c1: code = base + 5
        if n >= 3:
            if code == 0 and C2 > O2 and c1 > o1 and c0 > o0 and Lg2 and Lg1 and Lg0 \
                    and c1 > C2 and c0 > c1 and o1 > O2 and o1 < C2 and o0 > o1 and o0 < c1: code = base + 6
            if code == 0 and C2 < O2 and Lg2 and c1 > o1 and T1v <= O2 and M1v >= C2 \
                    and c0 > o0 and c0 > c1: code = base + 7
            if code == 0 and C2 < O2 and c1 > o1 and o1 <= C2 and c1 >= O2 and B1 > B2 \
                    and c0 > o0 and c0 > c1: code = base + 8
            if code == 0 and C2 < O2 and c1 < o1 and c0 < o0 and Lg2 and N2 > 0 \
                    and o1 < O2 and o1 > C2 and l1 > L2_ and B1 < B2 \
                    and h0 <= h1 and l0 >= l1 and B0 < B1: code = base + 9
            if code == 0 and C2 < O2 and Lg2 and c1 < o1 and o1 <= O2 and o1 >= C2 and l1 < L2_ \
                    and c1 > C2 and c0 > o0 and B0 < B1 and c0 < c1: code = base + 10
        if code == 0 and n >= 5:
            o4, h4, l4, c4 = g(4); o3, h3, l3, c3 = g(3)
            if c4 > o4 and Lg4 and c3 < o3 and C2 < O2 and c1 < o1 and B3 < B4 and B2 < B4 and B1 < B4 \
                    and h3 <= h4 and l3 >= l4 and H2 <= h4 and L2_ >= l4 and h1 <= h4 and l1 >= l4 \
                    and c0 > o0 and Lg0 and o0 < c1 and c0 > c4: code = base + 11
        if code == 0 and n >= 5:
            o4, h4, l4, c4 = g(4); o3, h3, l3, c3 = g(3)
            if c4 < o4 and c3 < o3 and C2 < O2 and Lg4 and Lg3 and Lg2 and o3 < o4 and O2 < o3 \
                    and c3 < c4 and C2 < c3 and c1 < o1 and S1 >= B1 and c0 > o0 and o0 > o1: code = base + 12
        if code == 0 and n >= 4:
            o3, h3, l3, c3 = g(3)
            if c3 < o3 and C2 < O2 and c1 < o1 and O2 < o3 and o1 < O2 and C2 < c3 and c1 < C2 \
                    and c0 > o0 and o0 < c1 and c0 > o3: code = base + 13

    # ---- neutral（舊 27–28／新 29–30）----
    nb = 28 if new else 26
    if neu:
        if code == 0 and h0 <= h1 and l0 >= l1: code = nb + 1
        if code == 0 and h0 >= h1 and l0 <= l1: code = nb + 2

    if new:
        if code == 0 and n >= 5:
            o4, h4, l4, c4 = g(4); o3, h3, l3, c3 = g(3)
            if h3 <= h4 and l3 >= l4 and H2 < h3 and L2_ < l3 and c0 > h3: code = 31
        if code == 0 and c1 < o1 and c0 < o0 and T0 <= o1 and M0 >= c1 and B0 < B1: code = 32
        if code == 0 and n >= 3 and C2 < O2 and c1 > o1 and c0 < o0 and c0 == C2 and c1 > C2: code = 33
    return code


def summarize(trades: list[Trade]) -> dict:
    net = sum(t.net_ntd for t in trades)
    gp = sum(t.net_ntd for t in trades if t.net_ntd > 0)
    gl = -sum(t.net_ntd for t in trades if t.net_ntd < 0)
    eq = peak = 0.0
    mdd = 0.0
    streak = best = 0
    for t in trades:
        eq += t.net_ntd
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
        streak = streak + 1 if t.net_ntd < 0 else 0
        best = max(best, streak)
    return {"trades": len(trades), "net": net, "pf": gp / gl if gl else float("inf"),
            "mdd_closed": mdd, "max_loss_streak": best,
            "win_rate": sum(1 for t in trades if t.net_ntd > 0) / len(trades) if trades else 0.0}
