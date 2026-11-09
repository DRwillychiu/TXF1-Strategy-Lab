"""策略設定檔（config/strategies/*.toml）讀取與 .pla 預設值比對（規則手冊 R6）。"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_strategy(key: str, check: bool = True) -> dict:
    """讀 `config/strategies/{key}.toml`，回傳 {meta..., 'params': {...}}。

    check＝True（預設）時立刻比對 .pla 預設值，不一致直接拋錯（規則手冊 R6：載入即紅燈）。
    """
    with open(ROOT / "config" / "strategies" / f"{key}.toml", "rb") as f:
        cfg = tomllib.load(f)
    if check:
        bad = check_against_pla(cfg)
        if bad:
            raise ValueError(f"{key} 設定檔與 .pla 不一致：{bad}")
    return cfg


def pla_inputs(pla_path: str | Path) -> dict:
    """解析 .pla 的 Inputs 區塊（先去掉 {} 註解）。布林轉 bool，其餘轉 float。"""
    txt = (ROOT / pla_path).read_text(encoding="utf-8", errors="replace")
    low = txt.lower()
    block = txt[low.index("inputs:"):low.index("variables:")]
    block = re.sub(r"\{[^}]*\}", "", block)
    out = {}
    for name, val in re.findall(r"(\w+)\s*\(\s*([^)]+?)\s*\)", block):
        v = val.strip()
        out[name] = (v.lower() == "true") if v.lower() in ("true", "false") else float(v)
    return out


def check_against_pla(cfg: dict) -> list[str]:
    """設定檔參數 vs .pla 預設值；回傳不一致清單（空 ＝ 一致）。"""
    pla = pla_inputs(cfg["pla"])
    params = cfg["params"]
    bad = [f"缺 {k}" for k in pla if k not in params]
    bad += [f"多 {k}" for k in params if k not in pla]
    bad += [f"{k}: 設定 {params[k]} ≠ .pla {v}" for k, v in pla.items()
            if k in params and (params[k] != v if isinstance(v, bool) else float(params[k]) != v)]
    return bad
