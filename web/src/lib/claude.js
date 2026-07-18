// W5 — Claude API 정책 브리핑 생성.
// API 키는 사용자가 입력해 localStorage에 보관(데모용). 실패 시 사전 생성 브리핑 fallback.

const KEY_STORAGE = "honeycomb_api_key";

export function getApiKey() {
  return localStorage.getItem(KEY_STORAGE) || "";
}
export function setApiKey(key) {
  localStorage.setItem(KEY_STORAGE, key);
}

export async function generateBriefing({ scenario, scenariosMeta, siting }) {
  const apiKey = getApiKey();
  if (!apiKey) throw new Error("NO_KEY");

  const topCells = siting.features
    .map((f) => f.properties)
    .sort((a, b) => a.rank - b.rank)
    .slice(0, 5)
    .map(
      (p) =>
        `${p.rank}위 ${p.name} (종합 ${p.total_score}: 잉여 ${p.surplus_score}/상권 ${p.commerce_score}/접근 ${p.access_score})`
    )
    .join(", ");

  const prompt = `당신은 에너지 정책 분석관입니다. 아래 V2G(Vehicle-to-Grid) 충·방전 스케줄링 분석 결과를 바탕으로, 정부 담당자에게 제출할 정책 브리핑을 마크다운으로 작성하세요.

[분석 개요]
- 대상: 제주 재생에너지 출력제어 완화를 위한 EV 배터리 V2G 활용
- 데이터: 2019~2026 실측(KPX 출력제어·수요·발전량, 기상), LightGBM 예측 + MILP 최적화
- 월평균 출력제어량: ${scenariosMeta.assumptions.monthly_curtailment_mwh} MWh

[현재 선택된 시나리오: EV ${scenario.ev_count}대]
- 월간 출력제어 회피량: ${scenario.curtailment_avoided_mwh.toFixed(1)} MWh (전체의 ${scenario.curtailment_avoided_pct.toFixed(1)}%)
- 월간 절감액: ${Math.round(scenario.savings_won).toLocaleString()}원
- 배터리 열화비용: ${Math.round(scenario.degradation_cost_won).toLocaleString()}원
- ESS 투자 이연 환산: ${Math.round(scenario.deferred_investment_won).toLocaleString()}원
- 차주 1대당 월 수익: ${Math.round(scenario.owner_revenue_won_per_ev).toLocaleString()}원

[입지 적합도 상위 5개 셀]
${topCells}

요구사항: ① 핵심 요약 ② 시나리오 해석(경제성·확대 타당성) ③ 입지 기반 정책 제언 3가지, 총 400자 내외 간결하게. 제목은 "# V2G 정책 브리핑"으로 시작.`;

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: "claude-opus-4-8",
      max_tokens: 1500,
      messages: [{ role: "user", content: prompt }],
    }),
  });
  if (!res.ok) throw new Error(`API_${res.status}`);
  const data = await res.json();
  const text = data.content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("\n");
  if (!text) throw new Error("EMPTY");
  return { text, model: data.model, generated_at: new Date().toISOString() };
}
