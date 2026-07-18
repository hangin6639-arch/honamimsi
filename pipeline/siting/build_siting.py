"""Module 4 — 입지 분석 → data/siting.geojson.

QGIS 분석 파이프라인의 파이썬 대체 구현(동일 방법론):
  1. 제주 상가업소(소진공, 57k개) 좌표를 KMeans로 군집 → 군집중심 = 후보 충전소
  2. 후보지 보로노이 분할(제주 본섬 bbox 클리핑) = 쿠폰 낙수 범위 셀
  3. 적합도 점수 (컬럼 분리 저장 — SCHEMA.md 필수 4컬럼)
     - surplus_score : 주요 풍력단지 근접도 (잉여전력 접근성)
     - commerce_score: 셀 내 상가업소 수 (상권 밀도)
     - access_score  : 도시 중심(제주시청·서귀포시청) 접근성
     - total_score   : 0.5 / 0.3 / 0.2 가중합
출력: EPSG:4326 GeoJSON, < 1MB.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box, mapping
from sklearn.cluster import KMeans

BASE = Path(__file__).resolve().parent.parent
DATA = BASE.parent / "data"

N_CELLS = 18
W_SURPLUS, W_COMMERCE, W_ACCESS = 0.5, 0.3, 0.2

# 제주 주요 풍력단지(잉여전력 발생원) 좌표 — 동부 구좌·성산, 서부 한경·한림, 남부 표선
WIND_FARMS = [
    (126.17, 33.33), (126.24, 33.41), (126.75, 33.55),
    (126.79, 33.55), (126.90, 33.44), (126.83, 33.32),
]
CITY_CENTERS = [(126.5312, 33.4996), (126.5646, 33.2541)]  # 제주시청, 서귀포시청
JEJU_BBOX = box(126.14, 33.18, 126.98, 33.58)


def km(lon1, lat1, lon2, lat2):
    return np.hypot((lon1 - lon2) * 92.5, (lat1 - lat2) * 111.0)  # 제주 위도 근사


def scale100(x: np.ndarray) -> np.ndarray:
    lo, hi = x.min(), x.max()
    return np.full_like(x, 50.0) if hi == lo else (x - lo) / (hi - lo) * 100


def main() -> None:
    df = pd.read_csv(
        BASE / "raw" / "sanggwon_jeju.csv", usecols=["상호명", "행정동명", "경도", "위도"]
    ).dropna()
    df = df[(df["경도"].between(126.1, 127.0)) & (df["위도"].between(33.1, 33.6))]

    kb = KMeans(n_clusters=N_CELLS, n_init=10, random_state=42).fit(df[["경도", "위도"]])
    df["cell"] = kb.labels_
    centers = kb.cluster_centers_

    # 보로노이: 외곽 무한 셀 방지용 더미 포인트 추가 후 bbox 클리핑
    pad = [(125.5, 32.7), (125.5, 34.0), (127.6, 32.7), (127.6, 34.0), (126.5, 34.2), (126.5, 32.4)]
    vor = Voronoi(np.vstack([centers, pad]))

    counts = df.groupby("cell").size().to_numpy(float)
    surplus = scale100(
        np.array([
            -min(km(c[0], c[1], w[0], w[1]) for w in WIND_FARMS) for c in centers
        ])
    )
    access = scale100(
        np.array([
            -min(km(c[0], c[1], a[0], a[1]) for a in CITY_CENTERS) for c in centers
        ])
    )
    commerce = scale100(counts)
    total = W_SURPLUS * surplus + W_COMMERCE * commerce + W_ACCESS * access
    order = (-total).argsort().argsort() + 1  # rank

    # 셀 대표 지명: 셀 내 최빈 행정동
    names = df.groupby("cell")["행정동명"].agg(lambda s: s.mode().iat[0])

    features = []
    for i in range(N_CELLS):
        region = vor.regions[vor.point_region[i]]
        if -1 in region or not region:
            continue
        poly = Polygon(vor.vertices[region]).intersection(JEJU_BBOX)
        if poly.is_empty:
            continue
        poly = poly.simplify(0.002)
        # 도보권(500m) 가맹점 수
        d = df[df["cell"] == i]
        walk = int((km(d["경도"], d["위도"], centers[i][0], centers[i][1]) <= 0.5).sum())
        features.append({
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": {
                "cell_id": f"JJ-{i+1:03d}",
                "name": str(names[i]),
                "station_lon": round(float(centers[i][0]), 5),
                "station_lat": round(float(centers[i][1]), 5),
                "surplus_score": round(float(surplus[i]), 1),
                "commerce_score": round(float(commerce[i]), 1),
                "access_score": round(float(access[i]), 1),
                "total_score": round(float(total[i]), 1),
                "rank": int(order[i]),
                "charger_count": max(2, int(counts[i] // 1500)),  # 추정치(충전소 실데이터 미수집)
                "merchant_count": walk,
            },
        })

    gj = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    # ---- 스키마 검증 (Module 4 요구사항)
    required = {"surplus_score", "commerce_score", "access_score", "total_score"}
    for f in gj["features"]:
        missing = required - set(f["properties"])
        assert not missing, f"필수 점수 컬럼 누락: {missing}"

    out = DATA / "siting.geojson"
    out.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    kb_size = out.stat().st_size / 1024
    print(f"siting.geojson: 셀 {len(features)}개, {kb_size:.0f} KB (제주 상가 {len(df):,}개 기반)")
    top = sorted(gj["features"], key=lambda f: f["properties"]["rank"])[:5]
    for f in top:
        p = f["properties"]
        print(f"  {p['rank']}위 {p['name']:10s} total {p['total_score']:5.1f} "
              f"(잉여 {p['surplus_score']:5.1f} / 상권 {p['commerce_score']:5.1f} / 접근 {p['access_score']:5.1f})")


if __name__ == "__main__":
    main()
