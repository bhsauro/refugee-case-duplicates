"""Duplicate detection logic.

The core duplicate detection uses pandas melt-and-filter pattern:
    1. Melt specified columns into long format (value column + variable name)
    2. Remove within-ID duplicates (same value listed twice for same case)
    3. Find values that appear across multiple IDs (cross-case duplicates)
    4. Flag all IDs that contain duplicate values

This approach is vectorized (uses pandas' C-optimized operations) and is
performant for datasets up to ~100K rows. For larger datasets or real-time
requirements, consider:
    - Hash-based deduplication with groupby() instead of melt
    - Database-native duplicate detection with SQL window functions
    - Distributed processing with Spark for multi-million row datasets
"""

import pandas as pd


def find_duplicates(
    df: pd.DataFrame,
    value_cols: list[str],
    id_col: str = "Unique ID (Case)",
    flag_col: str = "Duplicate",
) -> pd.DataFrame:
    """Find duplicate values across specified columns.

    Args:
        df: DataFrame to check for duplicates
        value_cols: Columns to check for duplicate values
        id_col: Column containing unique identifiers
        flag_col: Name for duplicate flag column

    Returns:
        DataFrame with duplicate flag added
    """
    # Create melted dataframe to check all values
    meltframe = pd.melt(df, id_vars=[id_col], value_vars=value_cols)

    # Remove duplicates within same ID
    meltframe = meltframe.drop_duplicates([id_col, "value"], keep="first")

    # Remove empty values
    meltframe = meltframe[meltframe["value"] != ""]

    # Find IDs with duplicate values
    meltframe = meltframe[
        meltframe.duplicated(["value"], keep=False) & meltframe["value"].notnull()
    ]

    # Keep only one row per ID
    meltframe = meltframe.drop_duplicates([id_col])

    # Create duplicate flag
    meltframe = meltframe.drop(["value", "variable"], axis=1)
    meltframe[flag_col] = True

    # Merge back to original dataframe
    df = pd.merge(df, meltframe, on=id_col, how="left")

    return df


def count_duplicate_flags(row: pd.Series, flag_cols: list[str]) -> int:
    """Count number of duplicate flags for a row.

    Args:
        row: DataFrame row
        flag_cols: Column names containing duplicate flags

    Returns:
        Count of True flags
    """
    count = 0
    for col in flag_cols:
        if row[col]:
            count += 1
    return count


def mark_duplicates(
    df: pd.DataFrame, flag_cols: list[str], min_flags: int = 1
) -> pd.DataFrame:
    """Mark records as duplicates based on flag count.

    Args:
        df: DataFrame with duplicate flag columns
        flag_cols: Column names containing duplicate flags
        min_flags: Minimum number of flags to mark as duplicate

    Returns:
        DataFrame with duplicate marker and flag count
    """
    df["num_dup_flags"] = df.apply(
        lambda row: count_duplicate_flags(row, flag_cols), axis=1
    )
    df["duplicate"] = df["num_dup_flags"] >= min_flags

    return df
