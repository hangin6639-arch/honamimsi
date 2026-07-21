"""Module 3 — MILP 충·방전 스케줄 최적화.

forecast.json(시연 대표일 예측)을 입력으로 EV 대수별 24시간 충·방전 스케줄을
PuLP(CBC)로 최적화하고, SCHEMA.md v1.0에 맞춰
  ../data/scenarios.json  (EV 대수별 시나리오)
  ../data/schedule.json   (기준 시나리오 스케줄 시계열)
을 생성한다.

목적함수: 출력제어 회피 편익 + 피크 방전 편익 − 배터리 열화비용 (최대화)
제약: SoC 범위·동특성, 충전기 용량(유휴 차량 수 연동), 충·방전 동시 금지,
      익일 운행 전 목표 충전량(07시 SoC ≥ 60%), 일말 SoC ≥ 시작치.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pulp

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "out"
DATA = BASE.parent / "data"

# ---- 경제·기술 가정 (CLAUDE.md 스펙 준거)
BATTERY_KWH = 70
CHARGER_KW = 50
SOC_MIN, SOC_MAX, SOC_START = 0.20, 0.90, 0.45
SOC_MORNING = 0.60  # 07시 목표 충전량 제약
EFF = 0.92  # 왕복 효율(편도 적용)
SMP = 150  # 원/kWh — 회피 편익 단가
SMP_PEAK = 180  # 원/kWh — 저녁 피크 방전 편익
DEG = 45  # 원/kWh — 배터리 열화비용(방전 기준)
OWNER_SHARE = 0.6  # 편익 중 차주 배분율
ESS_CAPEX_PER_MWH = 4_200_000  # 원/MWh·월 — ESS 대체 투자 이연 환산
EV_COUNTS = [100, 300, 500, 1000, 2000]
BASE_EV = 500  # schedule.json 기준 시나리오


def optimize_day(hourly: list[dict], ev_count: int) -> dict:
    T = range(24)
    surplus = [max(h["curtail_mwh_pred"], 0.0) for h in hourly]
    idle = [h["idle_share_pred"] for h in hourly]
    cap_mwh = ev_count * BATTERY_KWH / 1000.0

    prob = pulp.LpProblem(f"v2g_{ev_count}", pulp.LpMaximize)
    ch = [pulp.LpVariable(f"ch_{t}", lowBound=0) for t in T]  # 잉여 흡수 충전 MWh
    gch = [pulp.LpVariable(f"gch_{t}", lowBound=0) for t in T]  # 일반 계통 충전 MWh(비용)
    dis = [pulp.LpVariable(f"dis_{t}", lowBound=0) for t in T]
    soc = [
        pulp.LpVariable(
            f"soc_{t}", lowBound=SOC_MIN * cap_mwh, upBound=SOC_MAX * cap_mwh
        )
        for t in T
    ]
    y = [pulp.LpVariable(f"y_{t}", cat="Binary") for t in T]  # 1=충전 모드

    big = ev_count * CHARGER_KW / 1000.0
    for t in T:
        conn = idle[t] * big  # 접속(유휴) 차량 충전기 용량 MW
        prob += ch[t] <= surplus[t]  # 잉여전력 내에서만 흡수
        prob += ch[t] + gch[t] <= conn * y[t]
        prob += dis[t] <= conn * (1 - y[t])  # 동시 충·방전 금지
        prev = SOC_START * cap_mwh if t == 0 else soc[t - 1]
        prob += soc[t] == prev + (ch[t] + gch[t]) * EFF - dis[t] / EFF
    prob += soc[7] >= SOC_MORNING * cap_mwh  # 익일 운행 보장(07시)
    prob += soc[23] >= SOC_START * cap_mwh  # 일말 SoC 복원
    for t in T:  # 방전은 저녁 피크(18~22시)만
        if not (18 <= t <= 22):
            prob += dis[t] == 0

    prob += pulp.lpSum(
        ch[t] * SMP * 1000
        + dis[t] * SMP_PEAK * 1000
        - dis[t] * DEG * 1000
        - gch[t] * SMP * 1000
        for t in T
    )
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    assert pulp.LpStatus[prob.status] == "Optimal", pulp.LpStatus[prob.status]

    return {
        "charge": [round(ch[t].value(), 3) for t in T],
        "discharge": [round(dis[t].value(), 3) for t in T],
        "soc_pct": [round(soc[t].value() / cap_mwh * 100, 1) for t in T],
        "objective_won": round(pulp.value(prob.objective)),
    }


def main() -> None:
    forecast = json.loads((OUT / "forecast.json").read_text(encoding="utf-8"))
    metrics = json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))
    hourly_in = forecast["hourly"]

    # 월 환산 계수: 2023년 실측 기준 월평균 제어 발생일 수
    df = pd.read_parquet(OUT / "dataset.parquet")
    d23 = df.loc["2023", "curtail_mwh"].resample("D").sum()
    curtail_days_per_month = round(float((d23 > 10).sum()) / 12, 1)

    total_curtail_month = float(df.loc["2023", "curtail_mwh"].sum()) / 12  # 월평균 제어량

    scenarios = []
    results = {}
    for n in EV_COUNTS:
        r = optimize_day(hourly_in, n)
        results[n] = r
        absorbed_day = sum(r["charge"])
        discharged_day = sum(r["discharge"])
        absorbed_month = absorbed_day * curtail_days_per_month
        benefit = (
            absorbed_month * SMP * 1000
            + discharged_day * curtail_days_per_month * SMP_PEAK * 1000
        )
        deg_cost = discharged_day * curtail_days_per_month * DEG * 1000
        savings = benefit - deg_cost
        # 활용률: 잉여전력이 발생한 시간대의 접속가능 용량 대비 실제 흡수량
        theoretical = sum(
            h["idle_share_pred"] * n * CHARGER_KW / 1000.0
            for h in hourly_in
            if h["curtail_mwh_pred"] > 0.5
        )
        util = absorbed_day / theoretical if theoretical else 0
        scenarios.append(
            {
                "ev_count": n,
                "curtailment_avoided_mwh": round(absorbed_month, 1),
                "curtailment_avoided_pct": round(
                    absorbed_month / total_curtail_month * 100, 1
                ),
                "savings_won": round(savings),
                "degradation_cost_won": round(deg_cost),
                "deferred_investment_won": round(absorbed_month * ESS_CAPEX_PER_MWH),
                "owner_revenue_won_per_ev": round(savings * OWNER_SHARE / n),
                "utilization_pct": round(util * 100, 1),
            }
        )
        print(
            f"EV {n:5d}: 일 흡수 {absorbed_day:6.1f} MWh, 월 회피 {absorbed_month:7.1f} MWh "
            f"({scenarios[-1]['curtailment_avoided_pct']}%), 월 절감 {savings/1e6:6.1f}백만원"
        )

    demo_date = forecast["meta"]["demo_date"]
    scenarios_json = {
        "meta": {
            "version": "1.0",
            "generated_at": pd.Timestamp.now(tz="Asia/Seoul").isoformat(
                timespec="seconds"
            ),
            "region": "제주",
            "period": {"start": "2023-01-01", "end": "2023-12-31"},
            "demo_date": demo_date,
            "assumptions": {
                "battery_kwh_per_ev": BATTERY_KWH,
                "charger_kw": CHARGER_KW,
                "degradation_won_per_kwh": DEG,
                "smp_won_per_kwh": SMP,
                "smp_peak_won_per_kwh": SMP_PEAK,
                "owner_share": OWNER_SHARE,
                "curtail_days_per_month": curtail_days_per_month,
                "monthly_curtailment_mwh": round(total_curtail_month, 1),
            },
        },
        "scenarios": scenarios,
    }

    # ---- schedule.json (기준 500대)
    r = results[BASE_EV]
    best_model = metrics["demand_mw"]["best"]
    sched_hourly = []
    for t, h in enumerate(hourly_in):
        renewable = h["solar_mw_pred"] + h["wind_mw_pred"]
        sched_hourly.append(
            {
                "hour": t,
                "surplus_mw": round(h["curtail_mwh_pred"], 1),
                "demand_mw": round(h["demand_mw_pred"], 1),
                "renewable_mw": round(renewable, 1),
                "charge_mwh": r["charge"][t],
                "discharge_mwh": r["discharge"][t],
                "soc_pct": r["soc_pct"][t],
                "idle_ev_count": round(h["idle_share_pred"] * BASE_EV),
            }
        )
    charge_hours = sorted(
        [t for t in range(24) if r["charge"][t] > 0.01],
        key=lambda t: -r["charge"][t],
    )[:4]
    best_hours = sorted(charge_hours)
    daily_revenue = (
        (sum(r["charge"]) * SMP + sum(r["discharge"]) * (SMP_PEAK - DEG))
        * 1000
        * OWNER_SHARE
        / BASE_EV
    )

    def ampm(h):
        return f"오전 {h}시" if h < 12 else ("오후 12시" if h == 12 else f"오후 {h-12}시")

    schedule_json = {
        "meta": {
            "version": "1.0",
            "date": demo_date,
            "ev_count": BASE_EV,
            "model": best_model,
            "metrics": {
                "mape": metrics["demand_mw"][best_model]["mape"],
                "r2": metrics["demand_mw"][best_model]["r2"],
                "by_target": {
                    k: {"best": v["best"], **v[v["best"]]} for k, v in metrics.items()
                },
            },
        },
        "hourly": sched_hourly,
        "recommendation": {
            "best_hours": best_hours,
            "expected_revenue_won": round(daily_revenue, -1),
            "message": f"{ampm(best_hours[0])}~{ampm(best_hours[-1])}, 잉여전력이 가장 많아요"
            if best_hours
            else "오늘은 참여 권장 시간이 없어요",
        },
    }

    DATA.mkdir(exist_ok=True)
    (DATA / "scenarios.json").write_text(
        json.dumps(scenarios_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA / "schedule.json").write_text(
        json.dumps(schedule_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nscenarios.json / schedule.json 갱신 완료 (기준일 {demo_date}, {BASE_EV}대)")


if __name__ == "__main__":
    main()
