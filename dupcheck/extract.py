"""Data extraction utilities for parsing structured data from text fields."""

import pandas as pd


def extract_and_expand(
    df: pd.DataFrame,
    from_col: str,
    to_col: str,
    pattern: str,
) -> list[str]:
    """Extract regex matches and expand into separate columns.

    Args:
        df: DataFrame to process (modified in place)
        from_col: Source column name to extract from
        to_col: Base name for output columns
        pattern: Regex pattern to match

    Returns:
        List of created column names (e.g., ['person_ids1', 'person_ids2'])
    """
    # Extract all matches into lists
    df[to_col] = df[from_col].str.findall(pattern)

    # Find maximum number of matches across all rows
    max_matches = int(df[to_col].str.len().max())

    # Create concatenated string version
    df[to_col] = df[to_col].str.join(", ")

    # Expand into separate numbered columns
    new_cols = []
    for i in range(max_matches):
        col_name = f"{to_col}{i + 1}"
        df[col_name] = df[to_col].str.split(", ", expand=True)[i]
        new_cols.append(col_name)

    return new_cols


def combine_fields(row: pd.Series, cols: list[str]) -> str:
    """Combine multiple field values into a comma-separated string.

    Args:
        row: DataFrame row
        cols: List of column names to combine

    Returns:
        Comma-separated string of non-null values
    """
    if not cols:
        return ""

    value = str(row[cols[0]]) if pd.notnull(row[cols[0]]) else ""

    for col in cols[1:]:
        if pd.notnull(row[col]):
            if value:
                value = f"{value}, {row[col]}"
            else:
                value = str(row[col])

    return value
