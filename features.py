"""Tạo đặc trưng dùng chung cho tập train và tập test (cùng công thức, cùng mốc thời gian)."""
from pyspark.sql import DataFrame, functions as F

START_MONTH = "2018-02-01"   # tháng đầu của dữ liệu train, mốc cố định cho months_since_start


def add_features(df: DataFrame) -> DataFrame:
    """Thêm các cột thời gian, nhóm vùng và vị trí tầng; df cần có date (kiểu ngày), province, level, levels."""
    month_start = F.trunc(F.col("date"), "month")
    return (df
            .withColumn("year", F.year("date"))
            .withColumn("month", F.month("date"))
            .withColumn("months_since_start", F.months_between(month_start, F.lit(START_MONTH).cast("date")).cast("int"))
            .withColumn("is_moscow_or_spb", F.col("province").isin("Moscow", "Saint Petersburg").cast("int"))
            .withColumn("is_first_floor", (F.col("level") == 1).cast("int"))
            .withColumn("is_top_floor", (F.col("level") == F.col("levels")).cast("int"))
            .withColumn("level_ratio", F.col("level") / F.col("levels")))
