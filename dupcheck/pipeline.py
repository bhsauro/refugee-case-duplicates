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
    """
    print("Reading input files...")
    cases = io.read_cases(cases_path)
    people = io.read_people(people_path)

    print("Extracting person IDs from case tags...")
    # Extract person IDs from the tags field as a list
    cases["person_ids"] = cases["Tags"].str.findall(PERSON_ID_PATTERN)

    print("Creating junction table and merging with people data...")
    # Create junction table (case-person relationships) - grows vertically
    case_person = cases[["Unique ID (Case)", "person_ids"]].explode("person_ids")

    # Normalize person IDs for matching
    people["Unique ID (Person)"] = people["Unique ID (Person)"].str.lower()
    case_person["person_ids"] = case_person["person_ids"].str.lower()

    # Single merge with people data (one-to-many relationship)
    combined = case_person.merge(
        people, left_on="person_ids", right_on="Unique ID (Person)", how="left"
    )

    # Merge case metadata back
    case_metadata = cases[
        [
            "Unique ID (Case)",
            "Client",
            "Office",
            "External Case Number",
            "Stage",
            "Country",
            "Country of Origin",
            "Date of Initial Contact",
        ]
    ]
    combined = combined.merge(case_metadata, on="Unique ID (Case)", how="left")

    # === Detect name matches ===

    print("Checking for duplicate names...")
    combined = detect.find_duplicates(
        combined, ["Full Name", "Full Name in Native Script"], flag_col="Duplicate"
    )
    combined["duplicate_name"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    # === Detect email matches ===

    print("Checking for duplicate emails...")
    # the Preferred Email field can contain multiple emails 
    combined["Emails_extracted"] = combined["Preferred Email"].str.findall(
        EMAIL_PATTERN
    )
    combined["Emails_extracted"] = combined["Emails_extracted"].str.join(", ")
    combined = detect.find_duplicates(
        combined, ["Emails_extracted"], flag_col="Duplicate"
    )
    combined["duplicate_email"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    # === Detect phone number matches ===

    print("Normalizing and checking phone numbers...")
    combined["Phone_normalized"] = combined["Phone Number"].apply(
        normalize.normalize_arabic_numerals
    )
    combined["Phone_normalized"] = combined["Phone_normalized"].str.replace(
        r"([^\s0-9])", "", regex=True
    )
    combined["Phone_normalized"] = combined["Phone_normalized"].apply(
        normalize.clean_phone_spaces
    )
    combined["Phone_normalized"] = combined["Phone_normalized"].str.lstrip("0")

    # Add country codes
    combined["Phone_normalized"] = combined.apply(
        lambda row: normalize.add_country_code(
            row["Phone_normalized"], get_country_code(row.get("Country"))
        ),
        axis=1,
    )

    combined = detect.find_duplicates(
        combined, ["Phone_normalized"], flag_col="Duplicate"
    )
    combined["duplicate_phone"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    # === Detect case number matches ===

    print("Checking for duplicate case numbers...")
    # Case numbers are at case level, not person level
    combined["Case Numbers"] = combined["External Case Number"].str.upper()
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

    # Check for duplicates across case number types
    combined = detect.find_duplicates(
        combined,
        ["SIV (NVC)", "SIV (Embassy)", "USRAP", "UNHCR"],
        flag_col="Duplicate",
    )
    combined["duplicate_casenum"] = combined["Duplicate"].fillna(False)
    combined = combined.drop("Duplicate", axis=1)

    print("Finalizing duplicate detection...")
    # Mark duplicates at person level
    # Each row represents one person - if they have a duplicate, they get flagged
    combined = detect.mark_duplicates(combined, DUPLICATE_TYPES, MIN_DUPLICATE_FLAGS)

    # Filter to people with duplicates (person-level output)
    duplicates = combined[combined["duplicate"]].copy()

    # Rename columns for output clarity
    duplicates.rename(
        columns={
            "person_ids": "Unique ID (Person)",
            "Full Name": "Name",
            "Emails_extracted": "Email",
            "Phone_normalized": "Phone Number",
        },
        inplace=True,
    )

    # Select and reorder output columns
    output_columns_person_level = [
        "Unique ID (Case)",
        "Unique ID (Person)",
        "Name",
        "Phone Number",
        "Email",
        "Office",
        "Stage",
        "Date of Initial Contact",
        "Case Numbers",
        "num_dup_flags",
        "duplicate_name",
        "duplicate_phone",
        "duplicate_email",
        "duplicate_casenum",
    ]

    # Select only columns that exist
    output_cols = [col for col in output_columns_person_level if col in duplicates.columns]
    duplicates = duplicates[output_cols]

    print(f"Found {len(duplicates)} people with duplicate flags")

    io.write_duplicates(duplicates, output_path)
