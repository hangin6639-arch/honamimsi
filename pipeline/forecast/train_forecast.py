"""Module 2 — 예측 모델 학습·검증.

타깃 4종(태양광·풍력 발전량, 수요, 풍력 출력제어량) + 유휴차량 비율(시뮬레이션)을
LightGBM·XGBoost로 각각 학습하고 시계열 분할로 MAPE·R²를 비교한다.

출력:
  out/metrics.json   — 모델 비교표 (발표 검증 슬라이드 근거)
  out/forecast.json  — 시연 대표일(테스트 구간 내 최대 제어일)의 시간별 예측
"""

from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import r2_score

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "out"

WEATHER = [
    c
    for prefix in ("temp", "rad", "rad_direct", "cloud", "ws10", "ws100", "wdir")
    for c in [f"{prefix}_jeju", f"{prefix}_hallim", f"{prefix}_seongsan"]
]
CALENDAR = ["hour", "dow", "month", "is_weekend", "doy"]

TARGETS = {
    "solar_mw": WEATHER + CALENDAR,
    "wind_mw": WEATHER + CALENDAR,
    "demand_mw": ["temp_jeju", "cloud_jeju"] + CALENDAR,
    "curtail_mwh": WEATHER + CALENDAR + ["demand_lag24"],
    "idle_share": ["temp_jeju", "rad_jeju"] + CALENDAR,
}


def mape(y, p):
    """0 근접 구간(야간 태양광 등)을 제외한 MAPE(%)."""
    y, p = np.asarray(y), np.asarray(p)
    mask = np.abs(y) > max(np.abs(y).mean() * 0.1, 1e-6)
    return float(np.mean(np.abs((y[mask] - p[mask]) / y[mask])) * 100)


def simulate_idle(df: pd.DataFrame, seed=42) -> pd.Series:
    """차량 유휴 비율 시뮬레이션 (실증 부재 → 스펙상 시뮬레이션 허용).

    야간 높음, 출퇴근 시간 낮음, 주말 완만, 악천후 시 소폭 상승 + 잡음.
    """
    rng = np.random.default_rng(seed)
    h = df["hour"].to_numpy()
    base = 0.88 - 0.30 * np.exp(-((h - 8.5) ** 2) / 4) - 0.28 * np.exp(-((h - 18.5) ** 2) / 5)
    base = base - 0.06 * np.sin((h - 12) / 24 * 2 * np.pi)
    base = np.where(df["is_weekend"].to_numpy() == 1, base * 0.96 + 0.02, base)
    base = base + 0.03 * (df["cloud_jeju"].to_numpy() / 100)
    return pd.Series(np.clip(base + rng.normal(0, 0.025, len(df)), 0.3, 0.98), index=df.index)


def main() -> None:
    df = pd.read_parquet(OUT / "dataset.parquet")
    df["demand_lag24"] = df["demand_mw"].shift(24)
    df["idle_share"] = simulate_idle(df)

    metrics: dict = {}
    models: dict = {}
    for target, feats in TARGETS.items():
        d = df.dropna(subset=[target] + feats)
        split = int(len(d) * 0.8)
        tr, te = d.iloc[:split], d.iloc[split:]
        Xtr, ytr, Xte, yte = tr[feats], tr[target], te[feats], te[target]

        cand = {
            "LightGBM": lgb.LGBMRegressor(
                n_estimators=600, learning_rate=0.05, num_leaves=63, verbose=-1, random_state=42
            ),
            "XGBoost": xgb.XGBRegressor(
                n_estimators=600, learning_rate=0.05, max_depth=7, verbosity=0, random_state=42
            ),
        }
        metrics[target] = {}
        best_name, best_r2 = None, -np.inf
        for name, model in cand.items():
            model.fit(Xtr, ytr)
            pred = model.predict(Xte)
            if target != "curtail_mwh":  # 제어량 외에는 음수 없음
                pred = np.clip(pred, 0, None)
            m = {"mape": round(mape(yte, pred), 2), "r2": round(float(r2_score(yte, pred)), 4)}
            metrics[target][name] = m
            if m["r2"] > best_r2:
                best_name, best_r2 = name, m["r2"]
        metrics[target]["best"] = best_name
        models[target] = cand[best_name]
        print(f"{target:12s} test={len(te):6d}  " + "  ".join(
            f"{k}: MAPE {v['mape']:6.2f}% R2 {v['r2']:.3f}" for k, v in metrics[target].items() if k != "best"
        ) + f"  -> {best_name}")

    # ---- 시연 대표일: 테스트 구간(제어 데이터 있는 최근 20%) 중 일간 제어량 최대일
    d = df.dropna(subset=["curtail_mwh"])
    test_start = d.index[int(len(d) * 0.8)]
    daily = d.loc[d.index >= test_start, "curtail_mwh"].resample("D").sum()
    demo_day = daily.idxmax().date()
    day = df.loc[str(demo_day)].copy()

    hourly = []
    for ts, row in day.iterrows():
        rec = {"hour": int(ts.hour)}
        for target, feats in TARGETS.items():
            x = row[feats].to_frame().T.astype(float)
            v = float(models[target].predict(x)[0])
            rec[f"{target}_pred"] = round(max(v, 0.0), 3)
            if target in row and pd.notna(row[target]):
                rec[f"{target}_actual"] = round(float(row[target]), 3)
        hourly.append(rec)

    forecast = {
        "meta": {
            "demo_date": str(demo_day),
            "daily_curtail_actual_mwh": round(float(daily.max()), 1),
            "note": "테스트 구간 내 일간 풍력 제어량 최대일 기준 예측",
        },
        "hourly": hourly,
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUT / "forecast.json").write_text(json.dumps(forecast, indent=2), encoding="utf-8")
    print(f"\n시연 대표일: {demo_day} (실측 일간 제어량 {daily.max():.1f} MWh)")


if __name__ == "__main__":
    main()
