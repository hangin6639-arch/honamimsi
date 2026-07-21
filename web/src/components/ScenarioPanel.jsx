// W3 — EV 슬라이더: scenarios.json 보간 → 절감액·회피량·투자 이연액 카드 갱신
import { fmt } from "../lib/data.js";

export default function ScenarioPanel({ scenariosData, evCount, setEvCount, scenario }) {
  const list = scenariosData.scenarios;
  const min = list[0].ev_count;
  const max = list[list.length - 1].ev_count;

  return (
    <div className="card">
      <h2>W3 · EV 참여 규모 시뮬레이터</h2>
      <p className="desc">
        사전 계산된 MILP 시나리오({list.map((s) => s.ev_count).join("·")}대)를 선형 보간해 실시간 재계산
      </p>
      <div className="slider-row">
        <span style={{ fontSize: 13, color: "var(--ink-2)" }}>{min}대</span>
        <input
          type="range"
          min={min}
          max={max}
          step={50}
          value={evCount}
          onChange={(e) => setEvCount(Number(e.target.value))}
        />
        <span style={{ fontSize: 13, color: "var(--ink-2)" }}>{max}대</span>
        <div className="ev-badge">EV {evCount.toLocaleString()}대</div>
      </div>
      <div className="kpi-row">
        <div className="kpi">
          <div className="label">월간 출력제어 회피</div>
          <div className="value">
            {fmt.mwh(scenario.curtailment_avoided_mwh)}{" "}
            <small>({fmt.pct(scenario.curtailment_avoided_pct)})</small>
          </div>
        </div>
        <div className="kpi">
          <div className="label">월간 절감액 (편익−열화비용)</div>
          <div className="value">{fmt.won(scenario.savings_won)}</div>
        </div>
        <div className="kpi">
          <div className="label">ESS 투자 이연 환산</div>
          <div className="value">{fmt.won(scenario.deferred_investment_won)}</div>
        </div>
        <div className="kpi">
          <div className="label">차주 1대당 월 수익</div>
          <div className="value">{fmt.won(scenario.owner_revenue_won_per_ev)}</div>
        </div>
        <div className="kpi">
          <div className="label">유휴시간 활용률</div>
          <div className="value">{fmt.pct(scenario.utilization_pct)}</div>
        </div>
      </div>
    </div>
  );
}
