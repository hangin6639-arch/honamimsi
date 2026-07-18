import { useEffect, useMemo, useState } from "react";
import { loadAll, interpolateScenario } from "./lib/data.js";
import MapView from "./components/MapView.jsx";
import ScheduleView from "./components/ScheduleView.jsx";
import ScenarioPanel from "./components/ScenarioPanel.jsx";
import CompareView from "./components/CompareView.jsx";
import Briefing from "./components/Briefing.jsx";

const TABS = [
  { id: "siting", label: "입지 지도" },
  { id: "schedule", label: "스케줄" },
  { id: "scenario", label: "시나리오" },
  { id: "briefing", label: "AI 브리핑" },
];

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("siting");
  const [evCount, setEvCount] = useState(500);

  useEffect(() => {
    loadAll().then(setData).catch((e) => setError(e.message));
  }, []);

  const scenario = useMemo(
    () => (data ? interpolateScenario(data.scenarios, evCount) : null),
    [data, evCount]
  );

  if (error) return <div className="loading">데이터 로딩 실패: {error}</div>;
  if (!data) return <div className="loading">🍯 HoneyComb 데이터 로딩 중...</div>;

  return (
    <>
      <header className="app-header">
        <div className="logo">🍯</div>
        <div>
          <h1>HoneyComb 허니콤</h1>
          <div className="sub">V2G 충·방전 스케줄링 정책 대시보드 · 제주</div>
        </div>
        <nav>
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "active" : ""}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="layout">
        {tab === "siting" && <MapView siting={data.siting} />}
        {tab === "schedule" && <ScheduleView schedule={data.schedule} />}
        {(tab === "scenario" || tab === "briefing") && (
          <ScenarioPanel
            scenariosData={data.scenarios}
            evCount={evCount}
            setEvCount={setEvCount}
            scenario={scenario}
          />
        )}
        {tab === "scenario" && (
          <CompareView scenariosData={data.scenarios} evCount={evCount} />
        )}
        {tab === "briefing" && (
          <Briefing
            scenario={scenario}
            scenariosData={data.scenarios}
            siting={data.siting}
            fallback={data.briefingFallback}
          />
        )}
      </main>
    </>
  );
}
