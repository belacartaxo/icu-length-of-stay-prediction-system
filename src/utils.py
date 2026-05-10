from typing import Sequence, Optional
from pyspark.sql import SparkSession, Window, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.functions import col, min, avg, max, expr
from pandas import DataFrame
from functools import reduce

# Configurando o Spark Session
spark = SparkSession.builder \
    .appName("MIMIC_III_LengthOfStay_Project") \
    .config("spark.sql.session.timeZone", "UTC") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "8g") \
    .config("spark.sql.debug.maxToStringFields", 100) \
    .getOrCreate()

# Verificando se a sessão iniciou corretamente
print(f"Spark Session Initialized! Version: {spark.version}")

def create_df(path:str, columns=None, describe:bool = False) -> DataFrame:
    # Carregando a tabela de pacientes
    df = spark.read.csv(path, header=True, inferSchema=True)
    
    if columns:
        df = df.select(columns)

    if describe:
        df.limit(5).show(5)
        df.printSchema()
        print(f"Number of rows: {df.count()}")
    return df

def merge_dfs(df1, df2, column):
    return df1.join(df2, on=column, how="left")


def filter_events_by_time_window(
    events_df,
    reference_df,
    join_key="ICUSTAY_ID",
    event_time_col="CHARTTIME",
    start_col="INTIME",
    end_col="END_FIRST_24H",
    value_col="VALUENUM",
    drop_null_values=True
):
    """
    Filter events that occur within the first 24 hours window.

    Parameters:
    - events_df: DataFrame with event records (e.g., chartevents)
    - reference_df: DataFrame with time window reference (INTIME, END_FIRST_24H)
    - join_key: column used to join both DataFrames
    - event_time_col: timestamp column in events_df
    - start_col: start time column (usually INTIME)
    - end_col: end time column (usually END_FIRST_24H)
    - value_col: column to check for null values (optional)
    - drop_null_values: whether to filter null values

    Returns:
    - Filtered DataFrame with events in the first 24h window
    """

    df = events_df.join(reference_df, on=join_key, how="inner")

    df = df.filter(
        (col(event_time_col) >= col(start_col)) &
        (col(event_time_col) <= col(end_col))
    )

    if drop_null_values and value_col:
        df = df.filter(col(value_col).isNotNull())

    return df


def normalize_feature_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
    )


def build_code_to_feature_map(features_map: dict) -> dict:
    """
    Converts a flexible feature dictionary into a code -> feature_name map.

    Supports:
    {
        "Heart Rate": [211, 220045],
        "vitals": {
            "Systolic BP": [51, 442]
        }
    }
    """
    code_to_feature = {}

    for key, value in features_map.items():
        if isinstance(value, dict):
            for feature_name, codes in value.items():
                normalized_name = normalize_feature_name(feature_name)

                for code in codes:
                    code_to_feature[code] = normalized_name

        elif isinstance(value, list):
            normalized_name = normalize_feature_name(key)

            for code in value:
                code_to_feature[code] = normalized_name

        else:
            raise ValueError(
                f"Invalid format for feature '{key}'. Expected list or dict."
            )

    return code_to_feature


def extract_selected_codes(code_to_feature: dict) -> list:
    return list(code_to_feature.keys())


def filter_events_by_codes(
    events_df: DataFrame,
    selected_codes: list,
    code_column: str = "ITEMID"
) -> DataFrame:
    return events_df.filter(F.col(code_column).isin(selected_codes))


def add_feature_name_column(
    events_df: DataFrame,
    code_to_feature: dict,
    code_column: str = "ITEMID",
    feature_column: str = "feature_name"
) -> DataFrame:
    mapping_expr = F.create_map(
        *[
            item
            for code, feature_name in code_to_feature.items()
            for item in (F.lit(code), F.lit(feature_name))
        ]
    )

    return events_df.withColumn(
        feature_column,
        mapping_expr[F.col(code_column)]
    )


def aggregate_features(
    events_df: DataFrame,
    id_column: str,
    feature_column: str,
    value_column: str,
    metrics: Sequence[str] = ("min", "avg", "max"),
    time_column: str = "CHARTTIME"
) -> DataFrame:
    metric_functions = {
        "min": F.min(value_column).alias("min_value"),
        "avg": F.avg(value_column).alias("avg_value"),
        "max": F.max(value_column).alias("max_value"),
        "count": F.count(value_column).alias("count_value"),
        "sum": F.sum(value_column).alias("sum_value"),
    }

    aggregations = []

    for metric in metrics:
        if metric == "latest":
            continue

        if metric not in metric_functions:
            raise ValueError(
                f"Unsupported metric '{metric}'. "
                f"Available metrics: {list(metric_functions.keys()) + ['latest']}"
            )

        aggregations.append(metric_functions[metric])

    if aggregations:
        aggregated_df = events_df.groupBy(id_column, feature_column).agg(*aggregations)
    else:
        aggregated_df = events_df.select(id_column, feature_column).distinct()
    
    if "latest" in metrics:
        window_spec = Window.partitionBy(
            id_column,
            feature_column
        ).orderBy(
            F.col(time_column).desc()
        )

        latest_df = (
            events_df
            .withColumn("row_number", F.row_number().over(window_spec))
            .filter(F.col("row_number") == 1)
            .select(
                id_column,
                feature_column,
                F.col(value_column).alias("latest_value")
            )
        )

        aggregated_df = aggregated_df.join(
            latest_df,
            on=[id_column, feature_column],
            how="left"
        )

    return aggregated_df

def pivot_metric(
    aggregated_df: DataFrame,
    metric_column: str,
    suffix: str,
    id_column: str,
    feature_column: str
) -> DataFrame:
    pivot_df = (
        aggregated_df
        .groupBy(id_column)
        .pivot(feature_column)
        .agg(F.first(metric_column))
    )

    for column_name in pivot_df.columns:
        if column_name != id_column:
            pivot_df = pivot_df.withColumnRenamed(
                column_name,
                f"{column_name}_{suffix}"
            )

    return pivot_df


def join_feature_tables(
    dfs: Sequence[DataFrame],
    id_column: str
) -> Optional[DataFrame]:
    if not dfs:
        return None

    return reduce(
        lambda left, right: left.join(right, on=id_column, how="outer"),
        dfs
    )


def build_numeric_feature_table(
    events_df: DataFrame,
    features_map: dict,
    id_column: str = "ICUSTAY_ID",
    code_column: str = "ITEMID",
    value_column: str = "VALUENUM",
    feature_column: str = "feature_name",
    time_column: str = "CHARTTIME",
    metrics: Sequence[str] = ("min", "avg", "max"),
    drop_null_values: bool = True
) -> DataFrame:
    code_to_feature = build_code_to_feature_map(features_map)
    selected_codes = extract_selected_codes(code_to_feature)

    filtered_df = filter_events_by_codes(
        events_df=events_df,
        selected_codes=selected_codes,
        code_column=code_column
    )

    if drop_null_values:
        filtered_df = filtered_df.filter(F.col(value_column).isNotNull())

    mapped_df = add_feature_name_column(
        events_df=filtered_df,
        code_to_feature=code_to_feature,
        code_column=code_column,
        feature_column=feature_column
    )

    aggregated_df = aggregate_features(
        events_df=mapped_df,
        id_column=id_column,
        feature_column=feature_column,
        value_column=value_column,
        metrics=metrics,
        time_column=time_column
    )

    pivoted_dfs = []

    for metric in metrics:
        metric_column = f"{metric}_value"

        pivoted_df = pivot_metric(
            aggregated_df=aggregated_df,
            metric_column=metric_column,
            suffix=metric,
            id_column=id_column,
            feature_column=feature_column
        )

        pivoted_dfs.append(pivoted_df)

    return join_feature_tables(
        dfs=pivoted_dfs,
        id_column=id_column
    )


def aggregate_event_occurrence_features(
    events_df: DataFrame,
    id_column: str,
    feature_column: str = "feature_name"
) -> DataFrame:
    return (
        events_df
        .groupBy(id_column, feature_column)
        .agg(F.count("*").alias("event_count"))
        .withColumn("had_event", F.lit(1))
    )


def build_event_occurrence_feature_table(
    events_df: DataFrame,
    features_map: dict,
    id_column: str = "ICUSTAY_ID",
    code_column: str = "ITEMID",
    feature_column: str = "feature_name",
    count_suffix: str = "num",
    binary_suffix: str = "had"
) -> DataFrame:
    code_to_feature = build_code_to_feature_map(features_map)
    selected_codes = extract_selected_codes(code_to_feature)

    filtered_df = filter_events_by_codes(
        events_df=events_df,
        selected_codes=selected_codes,
        code_column=code_column
    )

    mapped_df = add_feature_name_column(
        events_df=filtered_df,
        code_to_feature=code_to_feature,
        code_column=code_column,
        feature_column=feature_column
    )

    aggregated_df = aggregate_event_occurrence_features(
        events_df=mapped_df,
        id_column=id_column,
        feature_column=feature_column
    )

    count_df = pivot_metric(
        aggregated_df=aggregated_df,
        metric_column="event_count",
        suffix=count_suffix,
        id_column=id_column,
        feature_column=feature_column
    )

    binary_df = pivot_metric(
        aggregated_df=aggregated_df,
        metric_column="had_event",
        suffix=binary_suffix,
        id_column=id_column,
        feature_column=feature_column
    )

    features_df = join_feature_tables(
        dfs=[count_df, binary_df],
        id_column=id_column
    )

    fill_values = {
        column_name: 0
        for column_name in features_df.columns
        if column_name != id_column
    }

    return features_df.fillna(fill_values)