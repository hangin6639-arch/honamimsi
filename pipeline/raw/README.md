# /pipeline/raw — 수집 원본 데이터 인벤토리

수집일: 2026-07-19. 모든 공공데이터포털 파일은 로그인 없이 다운로드한 공개 파일데이터.
인코딩 주의: 공공데이터포털 CSV는 EUC-KR(CP949)과 UTF-8이 섞여 있음 — pandas 로딩 시 `encoding` 확인 필수.

## 1. 출력제어 (타깃 변수) — [data.go.kr/15108268](https://www.data.go.kr/data/15108268/fileData.do)

시간별 제주 태양광·풍력 제어량(MWh)·제어횟수. 최신본은 3행짜리 요약이라 **과거 버전들이 본체**.

| 파일 | 기간 | 형식 |
|---|---|---|
| `jeju_curtail_20221118.csv` | 2015 ~ 2022-11 | 구분,연도,일자(MDD),시행회차,1~24시,총제어량 |
| `jeju_curtail_20230319.csv` | 2017 ~ 2023-03 | 구분,기준일(YYYY-MM-DD),시행회차,1~24시,총제어량 |
| `jeju_curtail_20231208.csv` | 2023-01 ~ 2023-12 | 〃 |
| `jeju_curtail_20240331/` (zip 해제) | 2024 Q1 | 태양광 횟수 / 풍력 제어량·횟수 분리 |
| `jeju_curtail_20240531/` (zip 해제) | ~2024-05 | 〃 |
| `curtailment_counts_2025.zip` | 2025 | 육지 태양광·풍력 제어횟수만 (보조) |

※ 제어가 없는 날짜는 행 자체가 없음(결측 아님 → 0으로 채울 것). 태양광은 제어량 미산정(횟수만).

## 2. 전력수요 — [data.go.kr/15065239](https://www.data.go.kr/data/15065239/fileData.do)

`demand/demand_YYYYMMDD.csv` 14개. 형식: 날짜,1시~24시 (MWh, 발전단 수요).
커버리지: **2007-01-01 ~ 2026-06-30** (파일 간 기간 중복 있음 → 병합 시 dedupe).

## 3. 재생에너지 발전량

| 파일 | 출처 | 기간 | 비고 |
|---|---|---|---|
| `jeju_gen_hourly_2019_2023/` (zip 해제) | [15127502](https://www.data.go.kr/data/15127502/fileData.do) | 2019-12 ~ 2023-12 | 제주 태양광/풍력 시간단위 실적 (전력시장 참여설비) |
| `regional_solar_wind_hourly_2025.csv` | [15065269](https://www.data.go.kr/data/15065269/fileData.do) | 2025 | 거래일,거래시간,지역,연료원,전력거래량 → 제주 필터 |
| `gen_regional/regional_solar_wind_2024.csv` | 〃 과거버전 | 2024 | 〃 |
| `gen_regional/regional_solar_wind_20231130.csv` | 〃 | ~2023-11 | 〃 |
| `gen_regional/regional_solar_20230228.csv` | 〃 | ~2023-02 | 태양광만 |
| `gen_regional/regional_solar_2020.csv`, `_2021.csv` | 〃 | 2020, 2021 | 태양광만 |
| `jeju_fuel_trade_hourly_2025.csv` | [15100214](https://www.data.go.kr/data/15100214/fileData.do) | 2025 | 제주 연료원별 시간별 거래량 (UTF-8) |

## 4. 기상 — Open-Meteo Historical API (무료, 키 불요)

`weather/weather_{jeju_city,hallim_west,seongsan_east}.csv`
- 기간: 2019-01-01 ~ 2026-06-30, 시간별(KST)
- 항목: 기온, 일사량(shortwave/direct), 운량, 풍속(10m/100m), 풍향
- 3지점: 제주시(수요·태양광), 한림(서부 풍력), 성산(동부 풍력)
- 기상청 ASOS로 교체하려면 공공데이터포털 API 키 필요 (미발급 상태)

## 5. 상권 (Module 4 입지분석) — [data.go.kr/15083033](https://www.data.go.kr/data/15083033/fileData.do)

`sanggwon_{jeju,gwangju,jeonnam,jeonbuk}.csv` — 2026-03 기준 상가업소(상호·업종·주소·경위도).
QGIS 상권밀도(commerce_score) 산출용.

## 미수집 (추후 확보 필요)

- **EV 충전소 위치** ([15125002](https://www.data.go.kr/data/15125002/fileData.do)) — 수집 당시 페이지 접속 차단, 재시도 필요. 대안: 무공해차 통합누리집(로그인 필요)
- **EV 등록 현황** (국토부 자동차등록현황, 시군구별) — 월별 통계 파일
- **차량 대여·유휴 패턴** — 실증 데이터 없으면 시뮬레이션으로 생성 (스펙 허용)
- 기상청 ASOS 실측 (선택) — API 키 발급 시
