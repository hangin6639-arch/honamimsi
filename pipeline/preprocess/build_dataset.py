"""Module 1 — 데이터 전처리 파이프라인.

raw/ 의 출력제어·수요·발전량·기상 CSV(포맷·인코딩·단위 이질)를 시간별로 정규화해
out/dataset.parquet 하나로 병합한다.

시간 규약: '1시'~'24시' 컬럼은 각 시간의 종료 기준 → hour n시는 타임스탬프 (n-1):00 에 매핑.
단위 규약: 전력량은 전부 MWh (시간별이므로 평균 MW와 동치로 취급).
"""

from __future__ import annotations

import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw"
OUT = BASE / "out"

HOUR_COLS = [f"{h}시" for h in range(1, 25)]


def read_csv_any(path, **kw):
    """EUC-KR / UTF-8(BOM) 혼재 CSV 로더."""
    for enc in ("utf-8-sig", "cp949", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, **kw)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise UnicodeError(f"encoding not detected: {path}")


def melt_wide_hours(df: pd.DataFrame, date_col: str, value_name: str) -> pd.DataFrame:
    """날짜 × 1시~24시 wide 형식 → (timestamp, value) long 형식."""
    hour_cols = [c for c in df.columns if re.fullmatch(r"\d+시(간)?", str(c).strip())]
    m = df.melt(
        id_vars=[date_col], value_vars=hour_cols, var_name="h", value_name=value_name
    )
    m["h"] = m["h"].str.extract(r"(\d+)").astype(int) - 1
    m[value_name] = pd.to_numeric(
        m[value_name].astype(str).str.replace(",", ""), errors="coerce"
    )
    m["ts"] = pd.to_datetime(m[date_col], errors="coerce") + pd.to_timedelta(
        m["h"], unit="h"
    )
    return m.dropna(subset=["ts"])[["ts", value_name]]


# ---------------------------------------------------------------- 수요
def load_demand() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(RAW / "demand" / "demand_*.csv"))) + [
        str(RAW / "jeju_demand_hourly_2026.csv")
    ]:
        df = read_csv_any(f)
        date_col = df.columns[0]
        m = melt_wide_hours(df, date_col, "demand_mw")
        # 단위 혼재: kWh 스케일 파일(값 ~7e5)은 MWh로 환산
        if m["demand_mw"].median() > 10_000:
            m["demand_mw"] /= 1000.0
        frames.append(m)
    out = pd.concat(frames).dropna()
    # 파일 간 기간 중복 → 나중(최신) 파일 우선
    out = out.drop_duplicates("ts", keep="last").set_index("ts").sort_index()
    return out


# ---------------------------------------------------------------- 발전량
def load_generation() -> pd.DataFrame:
    gen_dir = RAW / "jeju_gen_hourly_2019_2023"
    solar = melt_wide_hours(
        read_csv_any(next(gen_dir.glob("*태양광*.csv"))), "날짜", "solar_mw"
    )
    wind = melt_wide_hours(
        read_csv_any(next(gen_dir.glob("*풍력*.csv"))), "날짜", "wind_mw"
    )
    base = solar.merge(wind, on="ts", how="outer")

    # 2024~2025 연장: 지역별 long 포맷에서 제주만 추출
    longs = []
    for f in [
        RAW / "gen_regional" / "regional_solar_wind_2024.csv",
        RAW / "regional_solar_wind_hourly_2025.csv",
    ]:
        df = read_csv_any(f)
        df.columns = [c.strip() for c in df.columns]
        date_c = "거래일자" if "거래일자" in df.columns else "거래일"
        val_c = [c for c in df.columns if "거래량" in c][0]
        df = df[df["지역"].astype(str).str.contains("제주")]
        df["ts"] = pd.to_datetime(df[date_c]) + pd.to_timedelta(
            df["거래시간"].astype(int) - 1, unit="h"
        )
        p = df.pivot_table(index="ts", columns="연료원", values=val_c, aggfunc="sum")
        p = p.rename(columns={"태양광": "solar_mw", "풍력": "wind_mw"})
        longs.append(p[[c for c in ("solar_mw", "wind_mw") if c in p.columns]])
    ext = pd.concat(longs)

    base = base.set_index("ts").sort_index()
    out = pd.concat([base, ext[~ext.index.isin(base.index)]]).sort_index()
    # 지역별 거래량 파일(2024~)은 제주 풍력이 부분 집계(시장외 물량 누락)로 수준 이탈
    # → 풍력은 전용 실적 파일 구간(~2023-12)만 신뢰
    out.loc[out.index >= "2024-01-01", "wind_mw"] = np.nan
    return out


# ---------------------------------------------------------------- 출력제어
def load_curtailment() -> pd.DataFrame:
    frames = []

    def wide_curtail(df, date_col):
        df = df.rename(columns=lambda c: str(c).strip())
        m = melt_wide_hours(df, date_col, "curtail_mwh")
        return m

    # 2017 ~ 2023-03 (풍력 행만 시간별 제어량 보유)
    d1 = read_csv_any(RAW / "jeju_curtail_20230319.csv")
    d1 = d1[d1["구분"].astype(str).str.contains("풍력")]
    frames.append(("a", wide_curtail(d1, "기준일")))

    # 2023 전체
    d2 = read_csv_any(RAW / "jeju_curtail_20231208.csv")
    d2 = d2[d2["구분"].astype(str).str.contains("풍력")]
    frames.append(("b", wide_curtail(d2, "기준일")))

    # 2024 (풍력 제어량 파일)
    for zdir in ("jeju_curtail_20240331", "jeju_curtail_20240531"):
        f = next((RAW / zdir).glob("*풍력*제어량*.csv"))
        frames.append(("c", wide_curtail(read_csv_any(f), "일자")))

    allf = pd.concat([f for _, f in frames])
    # 같은 시각 중복(파일 겹침) → 나중 소스 우선
    allf = allf.drop_duplicates("ts", keep="last").set_index("ts").sort_index()
    return allf


# ---------------------------------------------------------------- 기상
def load_weather() -> pd.DataFrame:
    parts = []
    for f in sorted((RAW / "weather").glob("weather_*.csv")):
        tag = re.search(r"weather_(\w+?)\.csv", f.name).group(1).split("_")[0]
        df = pd.read_csv(f, skiprows=3)
        df = df.rename(columns=lambda c: c.split(" (")[0])
        df["ts"] = pd.to_datetime(df["time"])
        keep = {
            "temperature_2m": f"temp_{tag}",
            "shortwave_radiation": f"rad_{tag}",
            "direct_radiation": f"rad_direct_{tag}",
            "cloud_cover": f"cloud_{tag}",
            "wind_speed_10m": f"ws10_{tag}",
            "wind_speed_100m": f"ws100_{tag}",
            "wind_direction_10m": f"wdir_{tag}",
        }
        parts.append(df.set_index("ts")[list(keep)].rename(columns=keep))
    return pd.concat(parts, axis=1)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    demand = load_demand()
    gen = load_generation()
    curtail = load_curtailment()
    weather = load_weather()

    df = weather.join([demand, gen, curtail], how="left").sort_index()
    # 출력제어: 제어 없는 날은 원본에 행이 없음 → 0으로 간주하되,
    # 제어 기록 커버리지(마지막 기록일)까지만. 이후는 미관측(NaN) 유지.
    curtail_end = curtail.index.max().normalize() + pd.Timedelta(hours=23)
    fillable = df["wind_mw"].notna() & (df.index <= curtail_end)
    df.loc[fillable, "curtail_mwh"] = df.loc[fillable, "curtail_mwh"].fillna(0)

    # 캘린더 피처
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["month"] = df.index.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["doy"] = df.index.dayofyear

    # 결측 보간: 수치 시계열 3시간 이내 선형 보간
    for c in ("demand_mw", "solar_mw", "wind_mw"):
        df[c] = df[c].interpolate(limit=3)

    df.to_parquet(OUT / "dataset.parquet")

    print("dataset:", df.shape, "| 기간:", df.index.min(), "~", df.index.max())
    for c in ("demand_mw", "solar_mw", "wind_mw", "curtail_mwh"):
        s = df[c].dropna()
        print(
            f"  {c:12s} n={len(s):7d}  기간 {s.index.min()} ~ {s.index.max()}"
            f"  평균 {s.mean():8.2f}  최대 {s.max():8.1f}"
        )
    print("연도별 풍력 총제어량(MWh):")
    print(df.groupby(df.index.year)["curtail_mwh"].sum().round(0))


if __name__ == "__main__":
    main()
