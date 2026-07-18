// M1 — 오늘의 최적 참여시간 + 예상 수익 (schedule.json 기반)
import {
  AreaChart, Area, XAxis, Tooltip, ResponsiveContainer, ReferenceArea,
} from "recharts";

export default function Home({ schedule, history }) {
  const rec = schedule.recommendation;
  const chart = schedule.hourly.map((h) => ({ label: `${h.hour}시`, hour: h.hour, surplus: h.surplus_mw }));
  const best = rec.best_hours;
  const monthTotal = history.reduce((a, b) => a + b.won, 0);

  return (
    <>
      <div className="app-top">
        <span className="jar">🍯</span>
        <div>
          <h1>꿀차지</h1>
          <div className="copy">주차하고 꿀 받으세요</div>
        </div>
      </div>

      <div className="hero">
        <div className="t">오늘 참여하면</div>
        <div className="big">+{rec.expected_revenue_won.toLocaleString()}원 예상</div>
        <div className="msg">{rec.message}</div>
        <div className="hours">
          {best.map((h) => (
            <span key={h}>⚡ {h}:00</span>
          ))}
        </div>
      </div>

      <div className="sec">
        <h2>오늘의 잉여전력 흐름</h2>
        <ResponsiveContainer width="100%" height={150}>
          <AreaChart data={chart} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
            <XAxis dataKey="label" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} interval={3} />
            <Tooltip
              formatter={(v) => [`${v.toFixed(1)} MW`, "잉여전력"]}
              contentStyle={{ borderRadius: 10, border: "1px solid #eadfc8", fontSize: 12 }}
            />
            {best.length > 0 && (
              <ReferenceArea x1={`${best[0]}시`} x2={`${best[best.length - 1]}시`} fill="#ffcd4a" fillOpacity={0.25} />
            )}
            <Area dataKey="surplus" stroke="#c47f17" strokeWidth={2} fill="#ffcd4a" fillOpacity={0.45} />
          </AreaChart>
        </ResponsiveContainer>
        <div className="chart-note">노란 구간 = 꿀시간(참여 권장) · 잉여전력이 많을수록 보상이 커져요</div>
      </div>

      <div className="sec">
        <h2>이번 달 내 꿀단지</h2>
        <div className="honey-count">
          <span className="n">{monthTotal.toLocaleString()}</span>
          <span>원 적립</span>
        </div>
        <div className="chart-note">방전 {history.reduce((a, b) => a + b.kwh, 0).toFixed(0)} kWh · 제주 출력제어 완화에 기여 중 🌱</div>
      </div>
    </>
  );
}
