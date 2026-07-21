// W2 — 스케줄 뷰: 잉여전력 곡선(area) 위 충·방전(bar) + SoC(line)
import {
  ComposedChart, Area, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

export default function ScheduleView({ schedule }) {
  const data = schedule.hourly.map((h) => ({
    ...h,
    discharge_neg: -h.discharge_mwh,
    label: `${h.hour}시`,
  }));
  const m = schedule.meta;

  return (
    <div className="card">
      <h2>W2 · 충·방전 최적 스케줄 — {m.date} (EV {m.ev_count}대)</h2>
      <p className="desc">
        예측모델 {m.model} (수요 MAPE {m.metrics.mape}% · R² {m.metrics.r2}) + MILP 최적화 ·
        낮 잉여전력 흡수(충전) → 저녁 피크 방전
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#f0e8d5" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} tickLine={false} interval={2} />
          <YAxis yAxisId="mw" tick={{ fontSize: 12 }} tickLine={false} axisLine={false}
            label={{ value: "MW · MWh", angle: -90, position: "insideLeft", fontSize: 11, fill: "#6b5d42" }} />
          <YAxis yAxisId="soc" orientation="right" domain={[0, 100]} hide />
          <Tooltip
            formatter={(v, name) => {
              const n = typeof v === "number" ? Math.abs(v).toFixed(1) : v;
              return [n, name];
            }}
            labelStyle={{ fontWeight: 700 }}
            contentStyle={{ borderRadius: 10, border: "1px solid #eadfc8", fontSize: 13 }}
          />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          <Area yAxisId="mw" dataKey="surplus_mw" name="예측 잉여전력(제어 예상)"
            fill="#ffcd4a" fillOpacity={0.35} stroke="#c47f17" strokeWidth={2} />
          <Bar yAxisId="mw" dataKey="charge_mwh" name="충전(흡수)" fill="#c47f17" radius={[4, 4, 0, 0]} barSize={14} />
          <Bar yAxisId="mw" dataKey="discharge_neg" name="방전(피크 지원)" fill="#3f7fbf" radius={[4, 4, 0, 0]} barSize={14} />
          <Line yAxisId="soc" dataKey="soc_pct" name="차량군 SoC(%)" stroke="#2f9e8f" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
      <div className="legend">
        참여 권장 시간대: <b>{schedule.recommendation.best_hours.map((h) => `${h}시`).join(" · ")}</b>
        <span style={{ marginLeft: "auto" }}>{schedule.recommendation.message}</span>
      </div>
    </div>
  );
}
