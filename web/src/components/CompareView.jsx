// W4 — 시나리오 비교: 대수별 비용/편익 테이블 + 차트
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";
import { fmt } from "../lib/data.js";

export default function CompareView({ scenariosData, evCount }) {
  const list = scenariosData.scenarios;
  const chartData = list.map((s) => ({
    name: `${s.ev_count}대`,
    절감액_백만원: +(s.savings_won / 1e6).toFixed(1),
    열화비용_백만원: +(s.degradation_cost_won / 1e6).toFixed(1),
    회피율: s.curtailment_avoided_pct,
  }));
  // 현재 슬라이더와 가장 가까운 시나리오 강조
  const nearest = list.reduce((a, b) =>
    Math.abs(b.ev_count - evCount) < Math.abs(a.ev_count - evCount) ? b : a
  );

  return (
    <div className="card">
      <h2>W4 · 정책 시나리오 비교</h2>
      <p className="desc">EV 대수별 비용·편익 — 규모 확대 타당성 판단 근거</p>
      <div className="grid-2">
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#f0e8d5" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
            <YAxis yAxisId="won" tick={{ fontSize: 12 }} tickLine={false} axisLine={false}
              label={{ value: "백만원/월", angle: -90, position: "insideLeft", fontSize: 11, fill: "#6b5d42" }} />
            <YAxis yAxisId="pct" orientation="right" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} unit="%" />
            <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #eadfc8", fontSize: 13 }} />
            <Legend wrapperStyle={{ fontSize: 13 }} />
            <Bar yAxisId="won" dataKey="절감액_백만원" name="월 절감액" fill="#c47f17" radius={[4, 4, 0, 0]} barSize={22} />
            <Bar yAxisId="won" dataKey="열화비용_백만원" name="열화비용" fill="#9a5fb5" radius={[4, 4, 0, 0]} barSize={22} />
            <Line yAxisId="pct" dataKey="회피율" name="제어 회피율(%)" stroke="#2f9e8f" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
        <div style={{ overflowX: "auto" }}>
          <table className="compare">
            <thead>
              <tr>
                <th>EV 대수</th>
                <th>회피량</th>
                <th>절감액</th>
                <th>투자 이연</th>
                <th>대당 수익</th>
              </tr>
            </thead>
            <tbody>
              {list.map((s) => (
                <tr key={s.ev_count} className={s.ev_count === nearest.ev_count ? "hl" : ""}>
                  <td>{s.ev_count.toLocaleString()}대</td>
                  <td>{fmt.mwh(s.curtailment_avoided_mwh)}</td>
                  <td>{fmt.won(s.savings_won)}</td>
                  <td>{fmt.won(s.deferred_investment_won)}</td>
                  <td>{fmt.won(s.owner_revenue_won_per_ev)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
