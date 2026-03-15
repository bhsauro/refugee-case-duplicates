"""Unit tests for data normalization functions.

Tests cover:
- Eastern Arabic to Western numeral conversion
- Phone number normalization (spaces, country codes)
- UNHCR case number formatting
"""

import pytest
import pandas as pd
from dupcheck.normalize import (
    normalize_arabic_numerals,
    clean_phone_spaces,
    add_country_code,
    normalize_unhcr_case_number,
)


class TestNormalizeArabicNumerals:
    """Test Eastern Arabic (٠-٩) to Western (0-9) numeral conversion."""

    def test_eastern_arabic_to_western(self):
        """Should convert Eastern Arabic numerals to Western."""
        input_text = "٩٦١١٢٣٤٥٦"
        expected = "961123456"
        assert normalize_arabic_numerals(input_text) == expected

    def test_already_western_numerals(self):
        """Should leave Western numerals unchanged."""
        input_text = "961123456"
        assert normalize_arabic_numerals(input_text) == input_text

    def test_mixed_numerals(self):
        """Should convert mixed Eastern/Western numerals."""
        input_text = "٩٦1123456"  # First two are Eastern Arabic
        expected = "961123456"
        assert normalize_arabic_numerals(input_text) == expected

    def test_null_value(self):
        """Should handle null values without error."""
        result = normalize_arabic_numerals(None)
        assert pd.isnull(result)

    def test_empty_string(self):
        """Should handle empty strings."""
        assert normalize_arabic_numerals("") == ""


class TestCleanPhoneSpaces:
    """Test phone number space cleaning for space-delimited formats."""

    def test_space_delimited_phone(self):
        """Should remove spaces from space-delimited numbers."""
        input_phone = "961 123 456"
        expected = "961123456"
        assert clean_phone_spaces(input_phone) == expected

    def test_long_number_with_spaces(self):
        """Should preserve long numbers that have embedded long sequences."""
        # If there's a 6+ digit sequence, spaces are preserved
        input_phone = "1234567 890"
        # Has 7-digit sequence, so spaces stay
        assert clean_phone_spaces(input_phone) == "1234567 890"

    def test_no_spaces(self):
        """Should leave numbers without spaces unchanged."""
        input_phone = "961123456"
        assert clean_phone_spaces(input_phone) == input_phone

    def test_null_value(self):
        """Should handle null values."""
        result = clean_phone_spaces(None)
        assert pd.isnull(result)


class TestAddCountryCode:
    """Test country code addition to phone numbers."""

    def test_add_country_code_when_missing(self):
        """Should add country code if not present."""
        phone = "123456"
        country_code = "961"
        expected = "961123456"
        assert add_country_code(phone, country_code) == expected

    def test_preserve_existing_country_code(self):
        """Should not add country code if already present."""
        phone = "961123456"
        country_code = "961"
        # Should recognize 961 prefix and not add again
        assert add_country_code(phone, country_code) == phone

    def test_different_valid_prefix(self):
        """Should preserve other valid country codes."""
        phone = "962123456"  # Jordan
        country_code = "961"  # Lebanon
        # Should recognize 962 is valid and not add 961
        assert add_country_code(phone, country_code) == phone

    def test_null_phone(self):
        """Should handle null phone gracefully."""
        result = add_country_code(None, "961")
        assert pd.isnull(result)

    def test_null_country_code(self):
        """Should handle null country code gracefully."""
        result = add_country_code("123456", None)
        assert result == "123456"

    def test_empty_phone(self):
        """Should handle empty phone string."""
        assert add_country_code("", "961") == ""


class TestNormalizeUNHCRCaseNumber:
    """Test UNHCR case number normalization."""

    def test_add_hyphen_after_country_code(self):
        """Should add hyphen after 3-character country code."""
        case_num = "LEB22A12345"
        expected = "LEB-22A12345"
        assert normalize_unhcr_case_number(case_num) == expected

    def test_remove_existing_hyphens_and_normalize(self):
        """Should clean existing formatting and renormalize."""
        case_num = "LEB-22-A-12345"  # Has multiple hyphens
        expected = "LEB-22A12345"
        assert normalize_unhcr_case_number(case_num) == expected

    def test_numeric_country_code(self):
        """Should handle numeric country codes."""
        case_num = "96122A12345"
        expected = "961-22A12345"
        assert normalize_unhcr_case_number(case_num) == expected

    def test_short_case_number(self):
        """Should handle case numbers shorter than 3 characters."""
        case_num = "AB"
        assert normalize_unhcr_case_number(case_num) == "AB"

    def test_null_value(self):
        """Should handle null values."""
        result = normalize_unhcr_case_number(None)
        assert pd.isnull(result)
