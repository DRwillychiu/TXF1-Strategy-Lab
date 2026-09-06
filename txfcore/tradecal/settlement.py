"""結算日行事曆 —— 由 1 分 K 資料反推，非靜態規則。

**為什麼不用靜態規則。**

五份 `.pla` 都用同一條判定：

    v_Settlement_Day = DayOfWeek = 3 and DayOfMonth in [15, 21]

五份規格表都把「第三個週三遇休市會標錯」列為已知風險 D-6。
2026-09-06 用 208 萬列的 1 分 K 實測，把它量化了：

    資料反推的結算日   92 天
    靜態規則標的       90 天
    規則漏標            2 天   2023-01-30（一）· 2026-02-23（一）
    規則誤標            0 天

兩天都是農曆年後的週一 —— **結算因假期遞延**。

**反推方法**：TXF 近月合約在結算日 13:30 停止交易，其餘交易日到 13:45。
所以「日盤末根戳記 = 1330」就是結算日。90 天全中、零例外，
比靜態規則可靠。

**期間**：2019-01-02 ~ 2026-09-05（資料涵蓋範圍）。
超出範圍時退回靜態規則，並應告警 —— 與 Holiday_Tail 的
Registry_Valid_Until fail-safe 同一個原則：走出已驗證的地圖要 fail safe。
"""

from __future__ import annotations

from txfcore.types.mctime import DayOfWeek, day_of_month, day_of_week

# 日盤提前收盤時刻（結算日）
SETTLEMENT_CLOSE = 1330
NORMAL_DAY_CLOSE = 1345

# 由資料反推，民國年格式 YYYMMDD
SETTLEMENT_DAYS: tuple[int, ...] = (
    1190116, 1190220, 1190320, 1190417, 1190515, 1190619, 1190717, 1190821,
    1190918, 1191016, 1191120, 1191218, 1200115, 1200219, 1200318, 1200415,
    1200520, 1200617, 1200715, 1200819, 1200916, 1201021, 1201118, 1201216,
    1210120, 1210217, 1210317, 1210421, 1210519, 1210616, 1210721, 1210818,
    1210915, 1211020, 1211117, 1211215, 1220119, 1220216, 1220316, 1220420,
    1220518, 1220615, 1220720, 1220817, 1220921, 1221019, 1221116, 1221221,
    1230130, 1230215, 1230315, 1230419, 1230517, 1230621, 1230719, 1230816,
    1230920, 1231018, 1231115, 1231220, 1240117, 1240221, 1240320, 1240417,
    1240515, 1240619, 1240717, 1240821, 1240918, 1241016, 1241120, 1241218,
    1250115, 1250219, 1250319, 1250416, 1250521, 1250618, 1250716, 1250820,
    1250917, 1251015, 1251119, 1251217, 1260121, 1260223, 1260318, 1260415,
    1260520, 1260617, 1260715, 1260819,
)

SETTLEMENT_SET = frozenset(SETTLEMENT_DAYS)

# 來源檔案的 SHA-256。資料換版時這個值會變，屆時必須重新反推日曆。
SOURCE_SHA256 = "cd42303b1fb5300ab39aec0d9c2b3435ac95b9b91364ab9b31629891e91fbd90"
SOURCE_ROWS = 2_098_922

# 資料涵蓋範圍。超出即無法反推，須退回靜態規則並告警。
VERIFIED_FROM = 1190102
VERIFIED_UNTIL = 1260905

# 靜態規則漏標的日期（農曆年後遞延）。列出來當文件，不參與運算。
RULE_MISSED = (1230130, 1260223)


def static_rule(mc_date: int) -> bool:
    """五份 .pla 使用的靜態判定。保留供對帳時重現 MC 的行為。"""
    return (
        day_of_week(mc_date) is DayOfWeek.WED
        and 15 <= day_of_month(mc_date) <= 21
    )


def is_settlement_day(mc_date: int) -> bool:
    """實際結算日。已驗證範圍內用資料，範圍外退回靜態規則。"""
    if VERIFIED_FROM <= mc_date <= VERIFIED_UNTIL:
        return mc_date in SETTLEMENT_SET
    return static_rule(mc_date)


def is_verified(mc_date: int) -> bool:
    """該日是否落在已驗證範圍內。False 時呼叫端應告警。"""
    return VERIFIED_FROM <= mc_date <= VERIFIED_UNTIL


def day_close_time(mc_date: int) -> int:
    """該日的日盤收盤戳記。結算日 1330，其餘 1345。"""
    return SETTLEMENT_CLOSE if is_settlement_day(mc_date) else NORMAL_DAY_CLOSE


def day_minutes(mc_date: int) -> int:
    """該日的日盤分鐘數。結算日 285，其餘 300。

    網格切分靠它 —— 60M 在結算日會產生一根 45 分鐘的殘棒（戳 1330）。
    """
    return 285 if is_settlement_day(mc_date) else 300
