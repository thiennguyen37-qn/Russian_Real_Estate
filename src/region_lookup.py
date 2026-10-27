"""Tạo bảng tra cứu mã region -> tên vùng, tọa độ xuất hiện nhiều nhất và thủ phủ của mỗi mã.

Đầu ra: data/raw/region_names.csv với các cột region, province, most_frequent_coord, capital, capital_coord.
Chạy: python src/region_lookup.py
"""
import os
import sys
from pathlib import Path

os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
os.environ["PYSPARK_PYTHON"] = sys.executable

import pandas as pd
import shapely
from cartopy.io import shapereader
from pyspark.sql import SparkSession
from pyspark.sql.types import (StructType, StructField, IntegerType, LongType,
                               DoubleType, StringType)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "russia-real-estate.csv"
OUT_PATH = ROOT / "data" / "raw" / "region_names.csv"

SCHEMA = StructType([
    StructField("price",         LongType()),
    StructField("date",          StringType()),
    StructField("time",          StringType()),
    StructField("geo_lat",       DoubleType()),
    StructField("geo_lon",       DoubleType()),
    StructField("region",        IntegerType()),
    StructField("building_type", IntegerType()),
    StructField("level",         IntegerType()),
    StructField("levels",        IntegerType()),
    StructField("rooms",         IntegerType()),
    StructField("area",          DoubleType()),
    StructField("kitchen_area",  DoubleType()),
    StructField("object_type",   IntegerType()),
])

# Natural Earth thiếu hậu tố Oblast/Krai và ghi nhầm vài tên; sửa theo mã ISO 3166-2
NAME_FIX = {
    "RU-ALT": "Altai Krai",                 # bị ghi nhầm là "Altai Republic"
    "RU-MOW": "Moscow Oblast",              # Natural Earth hoán đổi mã của Moscow và tỉnh Moscow
    "RU-MOS": "Moscow",
    "RU-YEV": "Jewish Autonomous Oblast",
    "RU-KR":  "Republic of Karelia",
    "RU-KB":  "Kabardino-Balkar Republic",
    "RU-BA":  "Republic of Bashkortostan",
    "UA-43":  "Republic of Crimea",
}


def province_name(a):
    if a["iso_3166_2"] in NAME_FIX:
        return NAME_FIX[a["iso_3166_2"]]
    name = a["name_en"]
    if a["type_en"] == "Region" and not name.endswith(("Oblast", "Krai")):
        name += " Oblast"
    return name


def load_points(spark):
    """Gom các tọa độ khác nhau của từng mã kèm số bản ghi."""
    df = spark.read.csv(DATA_PATH.as_posix(), header=True, schema=SCHEMA)
    return df.groupBy("region", "geo_lat", "geo_lon").count().toPandas()


def load_provinces():
    """Ranh giới các tỉnh (chủ thể liên bang) của Nga từ Natural Earth admin_1."""
    reader = shapereader.Reader(shapereader.natural_earth("10m", "cultural", "admin_1_states_provinces"))
    return [(province_name(r.attributes), r.geometry) for r in reader.records()
            if r.attributes["adm0_a3"] == "RUS" and r.attributes["name_en"]]


def assign_provinces(pts, prov):
    """Gán mỗi mã cho tỉnh chứa nhiều bản ghi của nó nhất, mỗi tỉnh chỉ một mã."""
    prov_names = [n for n, _ in prov]
    tree = shapely.STRtree([g for _, g in prov])
    pt_idx, prov_idx = tree.query(shapely.points(pts["geo_lon"], pts["geo_lat"]), predicate="within")
    pts["province"] = None
    pts.loc[pts.index[pt_idx], "province"] = [prov_names[i] for i in prov_idx]
    print(f"Bản ghi không thuộc tỉnh nào: {pts.loc[pts['province'].isna(), 'count'].sum():,}")

    by_prov = (pts.dropna(subset=["province"]).groupby(["region", "province"])["count"].sum()
                  .reset_index().sort_values("count", ascending=False))
    n_region = pts.groupby("region")["count"].sum()

    # Mỗi mã là một chủ thể liên bang nên gán 1-1: duyệt cặp (mã, tỉnh) theo số bản ghi giảm dần
    assigned, used = {}, set()
    for r, p, n in by_prov.itertuples(index=False):
        if r not in assigned and p not in used:
            assigned[r] = (p, n)
            used.add(p)

    lookup = (pd.DataFrame([(r, p, n_region[r], round(100 * n / n_region[r], 2)) for r, (p, n) in assigned.items()],
                           columns=["region", "province", "n_records", "match_pct"])
                .sort_values("n_records", ascending=False)
                .reset_index(drop=True))

    # Kiểm tra: đủ mã, mỗi tỉnh một mã; chi tiết các mã có match_pct dưới 90%
    print(f"Số mã: {len(lookup)} | số tỉnh khác nhau: {lookup['province'].nunique()}")
    print(f"Tỉnh không ứng với mã nào: {sorted(set(prov_names) - set(lookup['province']))}")
    outside = pts[pts["province"].isna()].groupby("region")["count"].sum()
    for r, p, n, pct in lookup[lookup["match_pct"] < 90].itertuples(index=False):
        d = by_prov[by_prov["region"] == r]
        parts = [f"{q}: {100 * m / n:.1f}%" for q, m in zip(d["province"], d["count"])]
        parts.append(f"ngoài tỉnh: {100 * outside.get(r, 0) / n:.1f}%")
        print(f"  {r} -> {p} | " + ", ".join(parts))
    return lookup


def most_frequent_coords(pts):
    """Tọa độ xuất hiện nhiều nhất của mỗi mã, dạng "vĩ độ, kinh độ" (dán thẳng vào Google Maps được)."""
    return (pts.sort_values(["region", "count", "geo_lat", "geo_lon"], ascending=[True, False, True, True])
               .drop_duplicates("region")
               .assign(most_frequent_coord=lambda d: d["geo_lat"].astype(str) + ", " + d["geo_lon"].astype(str))
               [["region", "most_frequent_coord"]])


# Tọa độ trung tâm thành phố theo bài Wikipedia tiếng Anh của từng thành phố (truy cập 26/10/2026);
# tỉnh Moscow và tỉnh Leningrad lấy trung tâm là Moscow và Saint Petersburg
WIKI_CENTRES = {
    "Moscow":                    ("Moscow", 55.75583333, 37.61777778),
    "Moscow Oblast":             ("Moscow", 55.75583333, 37.61777778),
    "Saint Petersburg":          ("Saint Petersburg", 59.9375, 30.30861111),
    "Leningrad Oblast":          ("Saint Petersburg", 59.9375, 30.30861111),
    "Novosibirsk Oblast":        ("Novosibirsk", 55.05, 82.95),
    "Krasnodar Krai":            ("Krasnodar", 45.03333333, 38.96666667),
    "Sverdlovsk Oblast":         ("Yekaterinburg", 56.83555556, 60.61277778),
    "Republic of Tatarstan":     ("Kazan", 55.79638889, 49.10888889),
    "Rostov Oblast":             ("Rostov-on-Don", 47.2225, 39.71),
    "Chelyabinsk Oblast":        ("Chelyabinsk", 55.15472222, 61.37583333),
    "Tyumen Oblast":             ("Tyumen", 57.15, 65.53333333),
    "Yaroslavl Oblast":          ("Yaroslavl", 57.6264, 39.8933),
    "Nizhny Novgorod Oblast":    ("Nizhny Novgorod", 56.32694444, 44.0075),
    "Republic of Bashkortostan": ("Ufa", 54.72611111, 55.9475),
    "Krasnoyarsk Krai":          ("Krasnoyarsk", 56.00888889, 92.87194444),
    "Samara Oblast":             ("Samara", 53.20277778, 50.14083333),
    "Altai Krai":                ("Barnaul", 53.34861111, 83.77638889),
    "Voronezh Oblast":           ("Voronezh", 51.67166667, 39.21055556),
    "Stavropol Krai":            ("Stavropol", 45.05, 41.98333333),
    "Chuvash Republic":          ("Cheboksary", 56.15, 47.23333333),
    "Udmurt Republic":           ("Izhevsk", 56.83333333, 53.18333333),
    "Belgorod Oblast":           ("Belgorod", 50.6, 36.6),
    "Perm Krai":                 ("Perm", 58.0, 56.31666667),
    "Kaliningrad Oblast":        ("Kaliningrad", 54.70027778, 20.45305556),
}


def capitals(prov):
    """Thủ phủ của mỗi vùng: điểm Admin-0/Admin-1 capital của Natural Earth gán vào vùng theo ranh giới.

    Vùng có thêm thủ phủ cũ của khu tự trị đã sáp nhập thì giữ thành phố đông dân nhất; sau đó sửa Khakassia
    và thay tọa độ các thành phố lớn theo Wikipedia.
    """
    places = shapereader.Reader(shapereader.natural_earth("10m", "cultural", "populated_places")).records()
    caps = pd.DataFrame([(p.attributes["NAMEASCII"], p.attributes["LATITUDE"], p.attributes["LONGITUDE"], p.attributes["POP_MAX"])
                         for p in places if p.attributes["ADM0_A3"] == "RUS" and "capital" in p.attributes["FEATURECLA"]],
                        columns=["capital", "lat", "lon", "pop"])
    caps["capital"] = caps["capital"].replace({"Sevastapol": "Sevastopol"})   # Natural Earth viết sai
    ci, pi = shapely.STRtree([g for _, g in prov]).query(shapely.points(caps["lon"], caps["lat"]), predicate="within")
    caps["province"] = None
    caps.loc[caps.index[ci], "province"] = [prov[i][0] for i in pi]
    centres = (caps.dropna(subset=["province"]).sort_values("pop", ascending=False)
                   .drop_duplicates("province").set_index("province")[["capital", "lat", "lon"]])
    # Abakan rơi sang Krasnoyarsk Krai do ranh giới thô
    abakan = caps[caps["capital"] == "Abakan"].iloc[0]
    centres.loc["Republic of Khakassia"] = ["Abakan", abakan["lat"], abakan["lon"]]
    for p, v in WIKI_CENTRES.items():
        centres.loc[p] = list(v)
    return (centres.assign(capital_coord=lambda d: d["lat"].astype(str) + ", " + d["lon"].astype(str))
                   .rename_axis("province").reset_index()[["province", "capital", "capital_coord"]])


def main():
    spark = (SparkSession.builder
             .master("local[*]")
             .appName("RegionLookup")
             .config("spark.driver.memory", "8g")
             .config("spark.sql.shuffle.partitions", "16")
             .getOrCreate())
    try:
        pts = load_points(spark)
    finally:
        spark.stop()
    print(f"Số tọa độ khác nhau: {len(pts):,} | số bản ghi: {pts['count'].sum():,} | số mã region: {pts['region'].nunique()}")

    prov = load_provinces()
    lookup = assign_provinces(pts, prov)
    lookup = (lookup.merge(most_frequent_coords(pts), on="region")
                    .merge(capitals(prov), on="province", how="left"))
    print(f"Vùng thiếu thủ phủ: {lookup.loc[lookup['capital'].isna(), 'province'].tolist()}")
    print(lookup.to_string())

    cols = ["region", "province", "most_frequent_coord", "capital", "capital_coord"]
    lookup.sort_values("region")[cols].to_csv(OUT_PATH, index=False)
    print(f"Đã lưu {len(lookup)} mã vào {OUT_PATH}")


if __name__ == "__main__":
    main()
