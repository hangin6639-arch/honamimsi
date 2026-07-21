# 🍯 HoneyComb (허니콤)

제주·호남 재생에너지 출력제어 완화를 위한 **V2G 충·방전 스케줄링 플랫폼**.
실측 공공데이터(2019~2026) 기반 예측(LightGBM/XGBoost) + MILP 최적화 + 입지 분석 결과를
정부용 정책 대시보드와 차주용 앱 **꿀차지**로 제공한다.

## 구조

```
/data           스키마 계약(SCHEMA.md) + 산출 정적 데이터 (scenarios·schedule·siting·briefing)
/pipeline       Python — 전처리 → 예측 → MILP → 입지 (raw/ 에 수집 원본, README 참고)
/honeycomb      Django 프로젝트 설정
/dashboard      정부용 정책 대시보드 (Django 앱)
/honeycharge    차주용 꿀차지 웹앱 (Django 앱)
/api            Claude API 브리핑 엔드포인트
/static         정적 파일 (CSS, JS, Leaflet, Chart.js, 데이터)
/tools          data → static/ 동기화 스크립트
```

## 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 데이터베이스 마이그레이션
python manage.py migrate

# 3. 개발 서버 실행 (localhost:8000)
python manage.py runserver

# 접속 URL:
# - 정부 대시보드: http://localhost:8000/dashboard/
# - 꿀차지 앱: http://localhost:8000/honeycharge/
# - 입지 지도: http://localhost:8000/dashboard/map/
# - 스케줄 뷰: http://localhost:8000/dashboard/schedule/
# - 시나리오 비교: http://localhost:8000/dashboard/scenario/
```

파이프라인 재실행(정적 데이터 재생성)은 [pipeline/README.md](pipeline/README.md) 참고.
데이터 인터페이스 계약은 [data/SCHEMA.md](data/SCHEMA.md) — 변경 시 팀 합의 필수.

## 주요 기능

### 정부용 대시보드 (`/dashboard/`)
- **입지 지도 (W1)**: Leaflet 기반 보로노이 셀 적합도 시각화 (GeoJSON)
- **스케줄 뷰 (W2)**: Chart.js 기반 시간별 충·방전 스케줄 차트
- **EV 슬라이더 (W3)**: 전기차 대수별 절감액·회피량 실시간 재계산
- **시나리오 비교 (W4)**: 정책 시나리오별 비용/편익 분석 테이블
- **Claude AI 브리핑 (W5)**: 생성형 AI 기반 정책 브리핑 자동 생성

### 차주용 꿀차지 앱 (`/honeycharge/`)
- **홈 (M1)**: 오늘의 최적 참여시간 + 예상 수익 안내
- **수익 대시보드 (M2)**: 누적 방전량·정산액·배터리 기여도 차트
- **꿀 지갑 (M3)**: 꿀 적립·지역 쿠폰·주차권 + 가맹점/충전소 지도

## 시연 안정화 메모

- 모든 화면은 정적 JSON만 소비 → **Django 템플릿 + 정적 데이터로 동작**
  (예외: 지도 배경 타일(OSM)은 인터넷 필요. 오프라인 시 셀/마커는 표시되고 배경만 회색)
- W5 Claude 브리핑은 API 키 미입력·호출 실패 시 **사전 생성 브리핑 fallback** 자동 표시
- 데모 클릭 순서는 [DEMO.md](DEMO.md)

## 기술 스택

- **Backend**: Django 4.2
- **Frontend**: Tailwind CSS, Leaflet (지도), Chart.js (차트)
- **Data**: 정적 JSON/GeoJSON (사전 계산된 예측·최적화 결과)
- **AI**: Claude API (정책 브리핑 생성)

## 핵심 수치 (2023년 제주 실측 기준)

| EV 대수 | 월 출력제어 회피 | 월 절감액 | 대당 월 수익 |
|---|---|---|---|
| 500 | 100.6 MWh (4.6%) | 3,160만원 | 약 3.8만원 |
| 2,000 | 388.2 MWh (17.8%) | 1.24억원 | 약 3.7만원 |

예측 성능: 태양광 R² 0.91 · 풍력 R² 0.86 · 수요 MAPE 5.9% (시계열 분할 검증)
