"""Main duplicate detection pipeline."""

from pathlib import Path
from dupcheck import io, extract, normalize, detect
from dupcheck.constants import (
    PERSON_ID_PATTERN,
    EMAIL_PATTERN,
    PHONE_PATTERN,
    SIV_NVC_PATTERN,
    SIV_EMBASSY_PATTERN,
    USRAP_PATTERN,
    UNHCR_PATTERN,
    DUPLICATE_TYPES,
    MIN_DUPLICATE_FLAGS,
    OUTPUT_COLUMNS,
    get_country_code,
)


def process_duplicates(cases_path: Path, people_path: Path, output_path: Path) -> None:
    """Run the duplicate detection pipeline.

    This is the main entry point for programmatic use of the duplicate detection tool.
    It processes two Excel files (cases and people), detects duplicates across multiple
    criteria, and writes results to an output file.

    Args:
        cases_path: Path to Cases.xlsx file
        people_path: Path to People.xlsx file
        output_path: Path for output Excel file

    Example:
        >>> from pathlib import Path
        >>> from dupcheck.pipeline import process_duplicates
        >>> process_duplicates(
        ...     Path("Cases.xlsx"),
        ...     Path("People.xlsx"),
        ...     Path("results.xlsx")
        ... )
    """
    print("Reading input files...")
    cases = io.read_cases(cases_path)
    people = io.read_people(people_path)

    print("Extracting person IDs from case tags...")
    personid_cols = extract.extract_and_expand(
        cases, "Tags", "person_ids", PERSON_ID_PATTERN
    )

    print("Merging cases and people data...")
    people["Unique ID (Person)"] = people["Unique ID (Person)"].str.lower()

    # Merge first person
    combined = cases.merge(
        people, how="left", left_on=personid_cols[0], right_on="Unique ID (Person)"
    )

    # Merge additional people
    for i, col in enumerate(personid_cols[1:], start=1):
        suffix_left = f" {i}"
        suffix_right = f" {i+1}"
        combined = combined.merge(
            people,
            how="left",
            left_on=col,
            right_on="Unique ID (Person)",
            suffixes=(suffix_left, suffix_right),
        )

    print("Checking for duplicate names...")
    name_cols = [col for col in combined if col.startswith("Full Name")]
    combined["Names"] = combined.apply(
        lambda row: extract.combine_fields(row, name_cols), axis=1
    )
    combined = detect.find_duplicates(combined, name_cols, flag_col="Duplicate")
    combined["duplicate_name"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    print("Checking for duplicate emails...")
    email_cols = [col for col in combined if col.startswith("Preferred Email")]
    combined["Emails"] = combined.apply(
        lambda row: extract.combine_fields(row, email_cols), axis=1
    )
    new_email_cols = extract.extract_and_expand(
        combined, "Emails", "Emails", EMAIL_PATTERN
    )
    combined = detect.find_duplicates(combined, new_email_cols, flag_col="Duplicate")
    combined["duplicate_email"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    print("Normalizing and checking phone numbers...")
    phone_cols = [col for col in combined if col.startswith("Phone Number")]
    combined["Phone Numbers"] = combined.apply(
        lambda row: extract.combine_fields(row, phone_cols), axis=1
    )

    # Normalize Arabic numerals and clean
    combined["Phone Numbers"] = combined["Phone Numbers"].apply(
        normalize.normalize_arabic_numerals
    )
    combined["Phone Numbers"] = combined["Phone Numbers"].str.replace(
        r"([^\s0-9])", "", regex=True
    )
    combined["Phone Numbers"] = combined["Phone Numbers"].apply(
        normalize.clean_phone_spaces
    )

    # Extract phone numbers
    new_phone_cols = extract.extract_and_expand(
        combined, "Phone Numbers", "Phone Numbers", PHONE_PATTERN
    )

    # Add country codes
    for col in new_phone_cols:
        combined[col] = combined[col].str.lstrip("0")
        combined[col] = combined.apply(
            lambda row: normalize.add_country_code(
                row[col], get_country_code(row.get("Country"))
            ),
            axis=1,
        )

    combined["Phone Numbers"] = combined.apply(
        lambda row: extract.combine_fields(row, new_phone_cols), axis=1
    )
    combined = detect.find_duplicates(combined, new_phone_cols, flag_col="Duplicate")
    combined["duplicate_phone"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    print("Checking for duplicate case numbers...")
    combined.rename(
        columns={"External Case Number": "Case Numbers"}, inplace=True
    )
    combined["Case Numbers"] = combined["Case Numbers"].str.upper()
    combined["Case Numbers"] = combined["Case Numbers"].apply(
        normalize.normalize_arabic_numerals
    )

    # Extract case numbers by type
    combined["SIV (NVC)"] = combined["Case Numbers"].str.extract(SIV_NVC_PATTERN)
    combined["SIV (Embassy)"] = combined["Case Numbers"].str.extract(
        SIV_EMBASSY_PATTERN
    )
    combined["USRAP"] = combined["Case Numbers"].str.extract(USRAP_PATTERN)
    combined["UNHCR"] = combined["Case Numbers"].str.extract(UNHCR_PATTERN)
    combined["UNHCR"] = combined["UNHCR"].apply(normalize.normalize_unhcr_case_number)

    case_cols = ["SIV (NVC)", "SIV (Embassy)", "USRAP", "UNHCR"]
    combined["Case Numbers"] = combined.apply(
        lambda row: extract.combine_fields(row, case_cols), axis=1
    )
    combined["Case Numbers"] = combined["Case Numbers"].str.replace("nan, ", "", regex=False)

    # Find non-duplicates first
    combined_copy = combined.copy()
    for col in case_cols:
        combined_copy = combined_copy.drop(
            combined_copy[
                combined_copy.duplicated([col], keep=False) & combined_copy[col].notnull()
            ].index,
            axis=0,
        )

    combined_copy = combined_copy.drop(combined_copy.columns[1:], axis=1)
    combined_copy["Non-duplicate"] = True
    combined = combined.merge(combined_copy, on="Unique ID (Case)", how="left")
    combined["duplicate_casenum"] = ~combined["Non-duplicate"].fillna(False)
    combined = combined.drop("Non-duplicate", axis=1)

    print("Finalizing duplicate detection...")
    combined = detect.mark_duplicates(combined, DUPLICATE_TYPES, MIN_DUPLICATE_FLAGS)

    # Filter to duplicates only
    duplicates = combined[combined["duplicate"]]
    duplicates.rename(columns={"person_ids": "Unique ID (Person)"}, inplace=True)

    # Select output columns (only those that exist)
    output_cols = [col for col in OUTPUT_COLUMNS if col in duplicates.columns]
    duplicates = duplicates[output_cols]

    print(f"Found {len(duplicates)} duplicate records")

    io.write_duplicates(duplicates, output_path)
