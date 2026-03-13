"""Constants and reference data for duplicate detection.

This module contains stable reference data organized with module-level constants.

NOTE: These schemas reflect a legacy case management system that has since been deprecated
in favor of a modern relational database with proper foreign key relationships.
This tool was designed for the legacy system where person IDs were stored in unstructured
tag fields rather than proper relational links.
"""

# === Regex Patterns ===

# Basic extraction patterns
PERSON_ID_PATTERN = r"(contact-[0-9]{8})"
EMAIL_PATTERN = r"(\S+@\S+)"
PHONE_PATTERN = r"([0-9]{6,})"

# Case number patterns by type
SIV_NVC_PATTERN = r"(NVCSIV[0-9]{10})"
SIV_EMBASSY_PATTERN = r"(^(?!SIV)[A-Z]{3}[0-9]{10})"
USRAP_PATTERN = r"([A-Z]{2}-[0-9]{6})"
UNHCR_PATTERN = r"([A-Z0-9]{3}.?[0-9]{2}[A-Z][0-9]{4,6})"


# === Phone Number Patterns (Country Codes) ===

COUNTRY_CODES = {
    "Lebanon": "961",
    "Jordan": "962",
    "Turkey": "90",
    "Egypt": "20",
    "Iraq": "964",
    "Syria": "963",
    "Sudan": "249",
    "Afghanistan": "93",
}

VALID_PHONE_PREFIXES = list(COUNTRY_CODES.values())


def get_country_code(country: str) -> str | None:
    """Get calling code for a country.

    Args:
        country: Country name

    Returns:
        Calling code string, or None if country not found
    """
    return COUNTRY_CODES.get(country)


def is_valid_prefix(prefix: str) -> bool:
    """Check if prefix is a valid country code.

    Args:
        prefix: Phone number prefix to validate

    Returns:
        True if prefix is a known country code, False otherwise
    """
    return prefix in VALID_PHONE_PREFIXES


# === Column Schemas ===

# Expected columns in Cases.xlsx
CASES_COLUMNS = [
    "Unique ID",
    "Client",
    "Office",
    "External Case Number",
    "Stage",
    "Country",
    "Country of Origin",
    "Date of Initial Contact",
    "Tags",
]

# Expected columns in People.xlsx
PEOPLE_COLUMNS = [
    "Unique ID",
    "Full Name",
    "Full Name in Native Script",
    "Preferred Email",
    "Phone Number",
]

# Column renames for standardization
CASES_RENAME = {"Unique ID": "Unique ID (Case)"}
PEOPLE_RENAME = {"Unique ID": "Unique ID (Person)"}


# === Duplicate Detection ===

# Duplicate flag column names
DUPLICATE_NAME = "duplicate_name"
DUPLICATE_PHONE = "duplicate_phone"
DUPLICATE_EMAIL = "duplicate_email"
DUPLICATE_CASE_NUM = "duplicate_casenum"

# All duplicate check types
DUPLICATE_TYPES = [DUPLICATE_NAME, DUPLICATE_PHONE, DUPLICATE_EMAIL, DUPLICATE_CASE_NUM]

# Minimum number of flags to mark record as duplicate
MIN_DUPLICATE_FLAGS = 1


# === Output ===

OUTPUT_COLUMNS = [
    "Unique ID (Case)",
    "Unique ID (Person)",
    "Office",
    "Stage",
    "Date of Initial Contact",
    "num_dup_flags",
    "duplicate_name",
    "duplicate_phone",
    "duplicate_email",
    "duplicate_casenum",
    "Names",
    "Phone Numbers",
    "Emails",
    "Case Numbers",
]
