"""Hàm tính khoảng cách địa lý dùng chung cho các notebook."""
from pyspark.sql import Column, functions as F

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: Column, lon1: Column, lat2: Column, lon2: Column) -> Column:
    """Khoảng cách (km) trên mặt cầu giữa hai điểm (vĩ độ, kinh độ tính bằng độ), viết bằng hàm có sẵn của Spark."""
    dlat = F.radians(lat2 - lat1)
    dlon = F.radians(lon2 - lon1)
    a = F.sin(dlat / 2) ** 2 + F.cos(F.radians(lat1)) * F.cos(F.radians(lat2)) * F.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * F.asin(F.sqrt(a))
