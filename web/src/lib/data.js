// 정적 데이터 로더 + EV 대수 보간 (SCHEMA.md v1.0)

export async function loadJson(name) {
  const res = await fetch(`${import.meta.env.BASE_URL}data/${name}`);
  if (!res.ok) throw new Error(`데이터 로딩 실패: ${name}`);
  return res.json();
}

export async function loadAll() {
  const [scenarios, schedule, siting, briefingFallback] = await Promise.all([
    loadJson("scenarios.json"),
    loadJson("schedule.json"),
    loadJson("siting.geojson"),
    loadJson("briefing_fallback.json"),
  ]);
  return { scenarios, schedule, siting, briefingFallback };
}

const NUM_FIELDS = [
  "curtailment_avoided_mwh",
  "curtailment_avoided_pct",
  "savings_won",
  "degradation_cost_won",
  "deferred_investment_won",
  "owner_revenue_won_per_ev",
  "utilization_pct",
];

/** 슬라이더 값이 시나리오 사이면 선형 보간 (SCHEMA 계약) */
export function interpolateScenario(scenarios, evCount) {
  const list = scenarios.scenarios;
  if (evCount <= list[0].ev_count) return { ...list[0], ev_count: evCount };
  const last = list[list.length - 1];
  if (evCount >= last.ev_count) return { ...last, ev_count: evCount };

  let lo = list[0];
  let hi = last;
  for (let i = 0; i < list.length - 1; i++) {
    if (evCount >= list[i].ev_count && evCount <= list[i + 1].ev_count) {
      lo = list[i];
      hi = list[i + 1];
      break;
    }
  }
  const t = (evCount - lo.ev_count) / (hi.ev_count - lo.ev_count);
  const out = { ev_count: evCount };
  for (const f of NUM_FIELDS) out[f] = lo[f] + (hi[f] - lo[f]) * t;
  // 대당 수익은 보간이 아닌 재계산이 정확
  out.owner_revenue_won_per_ev =
    (out.savings_won * 0.6) / Math.max(evCount, 1);
  return out;
}

export const fmt = {
  won(v) {
    if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(1)}억원`;
    if (Math.abs(v) >= 1e4) return `${Math.round(v / 1e4).toLocaleString()}만원`;
    return `${Math.round(v).toLocaleString()}원`;
  },
  mwh(v) {
    return `${v.toFixed(1)} MWh`;
  },
  pct(v) {
    return `${v.toFixed(1)}%`;
  },
};
