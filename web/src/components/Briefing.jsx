// W5 — Claude API 정책 브리핑: 현재 슬라이더 상태를 입력으로 생성, 실패 시 fallback
import { useState } from "react";
import { generateBriefing, getApiKey, setApiKey } from "../lib/claude.js";

// 마크다운 경량 렌더링 (외부 의존성 없이 데모용)
function renderMd(text) {
  return text
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/^\- (.*)$/gm, "• $1")
    .replace(/^\d+\. /gm, (m) => `<b>${m}</b>`);
}

export default function Briefing({ scenario, scenariosData, siting, fallback }) {
  const [key, setKey] = useState(getApiKey());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [source, setSource] = useState(null); // "api" | "fallback"

  async function onGenerate() {
    setBusy(true);
    setApiKey(key.trim());
    try {
      const r = await generateBriefing({
        scenario,
        scenariosMeta: scenariosData.meta,
        siting,
      });
      setResult(r);
      setSource("api");
    } catch {
      // 시연 안정성: 어떤 실패든 사전 생성 브리핑으로 대체
      setResult(fallback);
      setSource("fallback");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h2>W5 · AI 정책 브리핑 (Claude)</h2>
      <p className="desc">
        현재 시나리오(EV {scenario.ev_count.toLocaleString()}대)와 입지 분석 결과를 Claude에 전달해 정책
        브리핑을 생성합니다. API 실패 시 사전 생성 브리핑을 표시합니다.
      </p>
      <div className="key-input">
        <input
          type="password"
          placeholder="Anthropic API 키 (sk-ant-...) — 미입력 시 사전 생성 브리핑 사용"
          value={key}
          onChange={(e) => setKey(e.target.value)}
        />
        <button className="btn" onClick={onGenerate} disabled={busy}>
          {busy ? "생성 중..." : "브리핑 생성"}
        </button>
      </div>
      {result && (
        <>
          <div
            className="briefing-box"
            dangerouslySetInnerHTML={{ __html: renderMd(result.text) }}
          />
          <div className="badge-src">
            {source === "api"
              ? `Claude API 실시간 생성 (${result.model})`
              : "사전 생성 브리핑 (fallback) — API 키를 입력하면 현재 시나리오 기반으로 실시간 생성됩니다"}
          </div>
        </>
      )}
    </div>
  );
}
