"""File I/O operations for reading and writing data."""

import pandas as pd
from pathlib import Path
from dupcheck.constants import CASES_COLUMNS, PEOPLE_COLUMNS, CASES_RENAME, PEOPLE_RENAME


def read_cases(file_path: Path) -> pd.DataFrame:
    """Read and validate cases Excel file.

    Args:
        file_path: Path to Cases.xlsx file

    Returns:
        DataFrame with cases data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cases file not found: {file_path}")

    df = pd.read_excel(file_path)

    # Validate required columns
    missing = [col for col in CASES_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in cases file: {missing}")

    # Select and rename columns
    df = df[CASES_COLUMNS]
    df.rename(columns=CASES_RENAME, inplace=True)

    return df


def read_people(file_path: Path) -> pd.DataFrame:
    """Read and validate people Excel file.

    Args:
        file_path: Path to People.xlsx file

    Returns:
        DataFrame with people data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    if not file_path.exists():
        raise FileNotFoundError(f"People file not found: {file_path}")

    df = pd.read_excel(file_path)

    # Validate required columns
    missing = [col for col in PEOPLE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in people file: {missing}")

    # Select and rename columns
    df = df[PEOPLE_COLUMNS]
    df.rename(columns=PEOPLE_RENAME, inplace=True)

    return df


def write_duplicates(df: pd.DataFrame, output_path: Path) -> None:
    """Write duplicate records to Excel file.

    Args:
        df: DataFrame with duplicate detection results
        output_path: Path for output Excel file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = pd.ExcelWriter(output_path, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="duplicates", index=False)
    writer.close()

    print(f"Duplicates written to: {output_path}")
