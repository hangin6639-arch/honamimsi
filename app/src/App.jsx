import { useEffect, useMemo, useState } from "react";
import Home from "./screens/Home.jsx";
import Earnings from "./screens/Earnings.jsx";
import Wallet from "./screens/Wallet.jsx";

async function loadJson(name) {
  const res = await fetch(`${import.meta.env.BASE_URL}data/${name}`);
  if (!res.ok) throw new Error(name);
  return res.json();
}

const TABS = [
  { id: "home", label: "홈", ic: "🏠" },
  { id: "earn", label: "수익", ic: "📈" },
  { id: "wallet", label: "꿀 지갑", ic: "🍯" },
];

export default function App() {
  const [tab, setTab] = useState("home");
  const [data, setData] = useState(null);

  useEffect(() => {
    Promise.all([loadJson("schedule.json"), loadJson("siting.geojson")])
      .then(([schedule, siting]) => setData({ schedule, siting }))
      .catch(() => setData({ error: true }));
  }, []);

  // 데모용 누적 이력: schedule 기반으로 결정적으로 생성 (매일 소폭 변동)
  const history = useMemo(() => {
    if (!data?.schedule) return [];
    const daily = data.schedule.recommendation.expected_revenue_won;
    return Array.from({ length: 30 }, (_, i) => {
      const wave = 0.65 + 0.35 * Math.abs(Math.sin((i + 3) * 1.7));
      return {
        day: i + 1,
        won: Math.round((daily * wave) / 10) * 10,
        kwh: +(daily * wave / 150).toFixed(1),
      };
    });
  }, [data]);

  if (!data) return <div className="phone"><div className="loading">🍯 꿀 채우는 중...</div></div>;
  if (data.error) return <div className="phone"><div className="loading">데이터 로딩 실패</div></div>;

  return (
    <div className="phone">
      <div className="screen">
        {tab === "home" && <Home schedule={data.schedule} history={history} />}
        {tab === "earn" && <Earnings schedule={data.schedule} history={history} />}
        {tab === "wallet" && <Wallet siting={data.siting} history={history} />}
      </div>
      <nav className="tabbar">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? "on" : ""} onClick={() => setTab(t.id)}>
            <span className="ic">{t.ic}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
