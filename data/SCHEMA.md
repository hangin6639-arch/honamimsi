# HoneyComb 데이터 스키마 계약 (v1.0)

> 파이프라인 팀(임유정·Fatima) ↔ 프론트 팀(박재성) 인터페이스 계약.
> 변경 시 반드시 양측 합의 후 이 문서의 버전을 올릴 것.

공통 규칙
- 모든 시각은 `KST` 기준 ISO 8601 문자열 (`"2026-07-19T13:00:00+09:00"`) 또는 `hour` 정수(0~23).
- 전력량 단위: **MWh**, 전력 단위: **MW**, 금액 단위: **원(KRW)**.
- 좌표계: **EPSG:4326** (경도, 위도 순).
- 파일 인코딩: UTF-8.

---

## 1. `scenarios.json` — EV 대수별 시나리오 (Module 3 산출)

W3 EV 슬라이더·W4 시나리오 비교·W5 브리핑의 입력.

```jsonc
{
  "meta": {
    "version": "1.0",
    "generated_at": "2026-07-19T00:00:00+09:00",
    "region": "제주",                    // 분석 대상 지역
    "period": { "start": "2026-07-01", "end": "2026-07-31" },
    "assumptions": {
      "battery_kwh_per_ev": 70,          // 대당 배터리 용량
      "charger_kw": 50,                  // 충전기 출력
      "degradation_won_per_kwh": 45,     // 배터리 열화비용 단가
      "smp_won_per_kwh": 150             // 전력 판매 단가(SMP 평균)
    }
  },
  "scenarios": [
    {
      "ev_count": 100,                   // 시나리오 키 (100/300/500/1000/...)
      "curtailment_avoided_mwh": 12.4,   // 월간 출력제어 회피량
      "curtailment_avoided_pct": 3.1,    // 전체 출력제어량 대비 %
      "savings_won": 1860000,            // 월간 절감액(편익-열화비용)
      "degradation_cost_won": 390000,    // 배터리 열화비용
      "deferred_investment_won": 52000000, // ESS 투자 이연액 환산
      "owner_revenue_won_per_ev": 18600, // 차주 1대당 월 예상 수익
      "utilization_pct": 62.5            // 유휴시간 대비 활용률
    }
    // ... ev_count 별 반복. 슬라이더 중간값은 프론트에서 선형 보간.
  ]
}
```

- `scenarios` 배열은 `ev_count` 오름차순 정렬 필수.
- 프론트 보간 규칙: 슬라이더 값이 두 시나리오 사이면 모든 수치 필드를 선형 보간.

---

## 2. `schedule.json` — 잉여전력 곡선 + 충·방전 스케줄 (Module 2+3 산출)

W2 스케줄 뷰, 앱 M1(최적 참여시간)의 입력.

```jsonc
{
  "meta": {
    "version": "1.0",
    "date": "2026-07-19",               // 대표 시연일
    "ev_count": 500,                     // 이 스케줄의 기준 시나리오
    "model": "LightGBM",                // 예측에 사용된 최적 모델
    "metrics": { "mape": 7.2, "r2": 0.91 } // 발표 검증용
  },
  "hourly": [
    {
      "hour": 0,                         // 0~23
      "surplus_mw": 0.0,                 // 예측 잉여전력(출력제어 예상량)
      "demand_mw": 412.5,                // 예측 수요
      "renewable_mw": 380.2,             // 예측 재생에너지 발전량
      "charge_mwh": 3.5,                 // 최적화 결과: 충전량 (≥0)
      "discharge_mwh": 0.0,              // 최적화 결과: 방전량 (≥0)
      "soc_pct": 48.0,                   // 차량군 평균 SoC
      "idle_ev_count": 431               // 예측 유휴 차량 수
    }
    // ... 24개 (hour 0~23)
  ],
  "recommendation": {                    // 앱 M1용 요약
    "best_hours": [11, 12, 13, 14],      // 참여 권장 시간대(충전=꿀시간)
    "expected_revenue_won": 3200,        // 오늘 참여 시 대당 예상 수익
    "message": "오전 11시~오후 2시, 태양광 잉여전력이 가장 많아요"
  }
}
```

- `hourly`는 반드시 24개, `hour` 오름차순.
- 같은 hour에 `charge_mwh`와 `discharge_mwh`가 동시에 양수일 수 없음(MILP 제약).

---

## 3. `siting.geojson` — 입지 적합도 보로노이 셀 (Module 4 / QGIS 산출)

W1 입지 지도, 앱 M3(가맹점/충전소 지도)의 입력.

```jsonc
{
  "type": "FeatureCollection",
  "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [ /* 보로노이 셀 */ ] },
      "properties": {
        "cell_id": "JJ-014",             // 고유 ID (지역코드-일련번호)
        "name": "제주시 연동",            // 표시명
        "station_lon": 126.49,           // 셀 중심 충전소 좌표
        "station_lat": 33.49,
        "surplus_score": 82.0,           // 잉여전력 접근성 점수 (0~100)
        "commerce_score": 67.5,          // 상권 밀도 점수 (0~100)
        "access_score": 74.0,            // 교통 접근성 점수 (0~100)
        "total_score": 76.3,             // 가중합 (가중치는 meta 참고)
        "rank": 3,                        // 전체 셀 중 순위 (1이 최적)
        "charger_count": 6,              // 기존 충전기 수
        "merchant_count": 42             // 도보권 내 쿠폰 가맹점 수
      }
    }
  ]
}
```

- 4개 점수 컬럼(`surplus_score`, `commerce_score`, `access_score`, `total_score`) 필수 — 누락 시 Module 4 검증 실패 처리.
- 웹 로딩용으로 simplify 적용, 파일 크기 1MB 이하 권장.
- `total_score` 가중치(예: 0.5/0.3/0.2)는 QGIS 분석 문서에 기록.

---

## 파일 위치

| 파일 | 경로 | 생산자 | 소비자 |
|---|---|---|---|
| scenarios.json | `/data/scenarios.json` | Module 3 (pipeline) | W3, W4, W5 |
| schedule.json | `/data/schedule.json` | Module 2+3 (pipeline) | W2, 앱 M1 |
| siting.geojson | `/data/siting.geojson` | Module 4 (QGIS) | W1, 앱 M3 |

웹/앱 빌드 시 `/data`의 파일을 각 프로젝트 `public/data/`로 복사해 사용한다.
