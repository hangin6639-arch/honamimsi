# 🍯 HoneyComb (허니콤)

제주·호남 재생에너지 출력제어 완화를 위한 **V2G 충·방전 스케줄링 플랫폼**.
실측 공공데이터(2019~2026) 기반 예측(LightGBM/XGBoost) + MILP 최적화 + 입지 분석 결과를
정부용 정책 대시보드와 차주용 앱 **꿀차지**로 제공한다.

## 구조

```
/data       스키마 계약(SCHEMA.md) + 산출 정적 데이터 (scenarios·schedule·siting·briefing)
/pipeline   Python — 전처리 → 예측 → MILP → 입지 (raw/ 에 수집 원본, README 참고)
/web        정부용 정책 대시보드 (React+Vite, Leaflet, Recharts)
/app        차주용 앱 꿀차지 (React 모바일 웹뷰)
/tools      data → web·app public/ 동기화 스크립트
```

## 실행

```bash
# 대시보드 (localhost:5173)
cd web && npm install && npm run dev

# 꿀차지 앱 (localhost:5174)
cd app && npm install && npm run dev

# 배포 빌드 → dist/ (정적 호스팅 어디든 가능, 상대경로 빌드)
npm run build
```

파이프라인 재실행(정적 데이터 재생성)은 [pipeline/README.md](pipeline/README.md) 참고.
데이터 인터페이스 계약은 [data/SCHEMA.md](data/SCHEMA.md) — 변경 시 팀 합의 필수.

## 시연 안정화 메모

- 모든 화면은 정적 JSON만 소비 → **서버·인터넷 없이 dist/ 만으로 동작**
  (예외: 지도 배경 타일(OSM)은 인터넷 필요. 오프라인 시 셀/마커는 표시되고 배경만 회색)
- W5 Claude 브리핑은 API 키 미입력·호출 실패 시 **사전 생성 브리핑 fallback** 자동 표시
- 데모 클릭 순서는 [DEMO.md](DEMO.md)

## 핵심 수치 (2023년 제주 실측 기준)

| EV 대수 | 월 출력제어 회피 | 월 절감액 | 대당 월 수익 |
|---|---|---|---|
| 500 | 100.6 MWh (4.6%) | 3,160만원 | 약 3.8만원 |
| 2,000 | 388.2 MWh (17.8%) | 1.24억원 | 약 3.7만원 |

예측 성능: 태양광 R² 0.91 · 풍력 R² 0.86 · 수요 MAPE 5.9% (시계열 분할 검증)
