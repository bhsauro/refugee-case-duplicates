"""Data normalization and cleaning functions.

Handles domain-specific normalization challenges for refugee case data:
    - Eastern Arabic numerals (٠-٩) commonly used in Middle East/North Africa
    - Phone numbers without country codes (require geographic context)
    - Inconsistent spacing and formatting in user-entered data
    - UNHCR case number format variations

These normalizations are critical for accurate duplicate detection across
international data sources where the same phone number might be entered as:
    "961 123 456" (Lebanon, with spaces)
    "٩٦١١٢٣٤٥٦" (Eastern Arabic numerals)
    "123456" (missing country code)
All normalize to: "961123456" for comparison.
"""

import pandas as pd
import re
from dupcheck.constants import VALID_PHONE_PREFIXES, get_country_code


# Eastern Arabic to Western Arabic numeral mapping
# Maps Unicode codepoints for Eastern Arabic (U+0660-U+0669) to ASCII (48-57)
NUMERAL_TABLE = {
    1632: 48,  # 0
    1633: 49,  # 1
    1634: 50,  # 2
    1635: 51,  # 3
    1636: 52,  # 4
    1637: 53,  # 5
    1638: 54,  # 6
    1639: 55,  # 7
    1640: 56,  # 8
    1641: 57,  # 9
}


def normalize_arabic_numerals(text: str) -> str:
    """Convert Eastern Arabic numerals to Western Arabic numerals.

    Args:
        text: Text containing Eastern Arabic numerals

    Returns:
        Text with Western Arabic numerals
    """
    if pd.isnull(text):
        return text
    return str(text).translate(NUMERAL_TABLE)


def clean_phone_spaces(text: str) -> str:
    """Remove spaces from space-delimited phone numbers.

    Args:
        text: Phone number text

    Returns:
        Cleaned phone number
    """
    if pd.isnull(text):
        return text

    text = str(text)
    # If no long digit sequences, remove all spaces
    if re.search(r"([0-9]{6,})", text) is None:
        return text.replace(" ", "")
    return text


def add_country_code(phone: str, country_code: str) -> str:
    """Add country code to phone number if not present.

    Args:
        phone: Phone number
        country_code: Country calling code

    Returns:
        Phone number with country code
    """
    if pd.isnull(phone) or pd.isnull(country_code):
        return phone

    if phone == "":
        return phone

    # Check if already has valid prefix
    if phone.startswith(tuple(VALID_PHONE_PREFIXES)):
        return phone

    return country_code + phone


def normalize_unhcr_case_number(case_num: str) -> str:
    """Normalize UNHCR case number format.

    Args:
        case_num: UNHCR case number

    Returns:
        Normalized case number
    """
    if pd.isnull(case_num):
        return case_num

    # Remove non-alphanumeric characters
    clean = re.sub(r"[^A-Za-z0-9]+", "", case_num)

    # Add hyphen after first 3 characters
    if len(clean) > 3:
        return clean[:3] + "-" + clean[3:]

    return clean
