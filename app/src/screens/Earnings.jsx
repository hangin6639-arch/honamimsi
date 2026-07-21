// M2 — 누적 수익 대시보드: 방전량·정산액·배터리 기여도
import {
  BarChart, Bar, XAxis, Tooltip, ResponsiveContainer,
} from "recharts";

export default function Earnings({ schedule, history }) {
  const totalWon = history.reduce((a, b) => a + b.won, 0);
  const totalKwh = history.reduce((a, b) => a + b.kwh, 0);
  const co2 = totalKwh * 0.45; // kgCO2, 전력 배출계수 근사

  return (
    <>
      <div className="app-top">
        <span className="jar">📈</span>
        <div>
          <h1>수익 대시보드</h1>
          <div className="copy">최근 30일 정산 내역</div>
        </div>
      </div>

      <div className="row2" style={{ marginBottom: 14 }}>
        <div className="stat">
          <div className="l">누적 정산액</div>
          <div className="v">{totalWon.toLocaleString()}원</div>
        </div>
        <div className="stat">
          <div className="l">누적 방전량</div>
          <div className="v">{totalKwh.toFixed(1)} <small>kWh</small></div>
        </div>
        <div className="stat">
          <div className="l">출력제어 회피 기여</div>
          <div className="v">{(totalKwh / 1000).toFixed(2)} <small>MWh</small></div>
        </div>
        <div className="stat">
          <div className="l">CO₂ 저감 환산</div>
          <div className="v">{co2.toFixed(0)} <small>kg</small></div>
        </div>
      </div>

      <div className="sec">
        <h2>일별 적립 추이</h2>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={history} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
            <XAxis dataKey="day" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} interval={4} />
            <Tooltip
              formatter={(v) => [`${v.toLocaleString()}원`, "적립"]}
              labelFormatter={(d) => `${d}일차`}
              contentStyle={{ borderRadius: 10, border: "1px solid #eadfc8", fontSize: 12 }}
            />
            <Bar dataKey="won" fill="#c47f17" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="sec">
        <h2>배터리 건강도</h2>
        <div className="row2">
          <div className="stat">
            <div className="l">V2G 사용 SoC 범위</div>
            <div className="v">20~90<small>%</small></div>
          </div>
          <div className="stat">
            <div className="l">열화 보상 반영</div>
            <div className="v">45<small>원/kWh</small></div>
          </div>
        </div>
        <div className="chart-note">
          스케줄 최적화가 배터리 열화비용을 목적함수에 반영해, 무리한 방전 없이 수익을 계산합니다.
        </div>
      </div>
    </>
  );
}
