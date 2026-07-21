# /pipeline — 전처리·예측·최적화 (Python)

## 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 구조와 실행 순서

| 순서 | 스크립트 | 모듈 | 입력 | 출력 |
|---|---|---|---|---|
| 1 | `preprocess/build_dataset.py` | Module 1 | `raw/` KPX·기상·수요 CSV | `out/dataset.parquet` |
| 2 | `forecast/train_forecast.py` | Module 2 | `out/dataset.parquet` | `out/forecast.json`, `out/metrics.json` |
| 3 | `optimize/run_milp.py` | Module 3 | `out/forecast.json` | `../data/scenarios.json`, `../data/schedule.json` |
| 4 | `siting/build_siting.py` | Module 4 | `raw/sanggwon_jeju.csv` | `../data/siting.geojson` (스키마 검증 포함) |

- 원본 CSV는 `pipeline/raw/`에 넣는다 (git에는 미포함 권장).
- 최종 산출물 스키마는 반드시 [/data/SCHEMA.md](../data/SCHEMA.md) v1.0을 따를 것.
