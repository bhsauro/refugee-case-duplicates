"""Unit tests for duplicate detection logic.

Tests cover:
- Core duplicate detection algorithm (find_duplicates)
- Multi-criteria duplicate flagging (mark_duplicates)
- Edge cases: empty data, single records, within-ID duplicates
"""

import pytest
import pandas as pd
from dupcheck.detect import find_duplicates, mark_duplicates, count_duplicate_flags


class TestFindDuplicates:
    """Test the core duplicate detection algorithm."""

    def test_detect_simple_duplicate(self):
        """Should flag records that share the same value."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-002", "case-003"],
            "Name": ["John Doe", "John Doe", "Jane Smith"]
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        # case-001 and case-002 should be flagged (both have "John Doe")
        assert result.loc[0, "duplicate"] == True
        assert result.loc[1, "duplicate"] == True
        # case-003 should not be flagged (unique name) - will be NaN/null
        assert pd.isna(result.loc[2, "duplicate"]) or result.loc[2, "duplicate"] == False

    def test_no_duplicates(self):
        """Should not flag any records when all values are unique."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-002", "case-003"],
            "Name": ["John Doe", "Jane Smith", "Bob Jones"]
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        # All should be False
        assert result["duplicate"].sum() == 0

    def test_all_duplicates(self):
        """Should flag all cases when all share the same value."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-002", "case-003"],
            "Name": ["John Doe", "John Doe", "John Doe"]
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        # All should be flagged
        assert result["duplicate"].sum() == 3

    def test_ignore_empty_values(self):
        """Should not flag records with empty/null values as duplicates."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-002", "case-003"],
            "Name": ["John Doe", "", ""]
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        # Empty values shouldn't create duplicate matches
        assert result["duplicate"].sum() == 0

    def test_multiple_columns(self):
        """Should check duplicates across multiple columns."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-002", "case-003"],
            "Name1": ["John Doe", "Jane Smith", ""],
            "Name2": ["", "John Doe", "Bob Jones"]
        })

        result = find_duplicates(df, ["Name1", "Name2"], id_col="Unique ID (Case)", flag_col="duplicate")

        # case-001 and case-002 both have "John Doe" (in different columns)
        assert result.loc[0, "duplicate"] == True
        assert result.loc[1, "duplicate"] == True
        # case-003 has unique value - will be NaN/null
        assert pd.isna(result.loc[2, "duplicate"]) or result.loc[2, "duplicate"] == False

    def test_ignore_within_id_duplicates(self):
        """Should not flag same value appearing twice in same ID."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-001", "case-002"],
            "Name": ["John Doe", "John Doe", "Jane Smith"]
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        # Both rows of case-001 should not be flagged (same case, same name)
        # This tests the drop_duplicates([id_col, 'value']) logic
        assert result["duplicate"].sum() == 0

    def test_null_values_ignored(self):
        """Should handle null values without flagging as duplicates."""
        df = pd.DataFrame({
            "Unique ID (Case)": ["case-001", "case-002", "case-003"],
            "Name": ["John Doe", None, None]
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        # Nulls shouldn't match each other
        assert result["duplicate"].sum() == 0

    def test_empty_dataframe(self):
        """Should handle empty dataframe without error."""
        df = pd.DataFrame({
            "Unique ID (Case)": [],
            "Name": []
        })

        result = find_duplicates(df, ["Name"], id_col="Unique ID (Case)", flag_col="duplicate")

        assert len(result) == 0


class TestCountDuplicateFlags:
    """Test duplicate flag counting."""

    def test_count_multiple_flags(self):
        """Should count number of True flags in row."""
        row = pd.Series({
            "duplicate_name": True,
            "duplicate_phone": True,
            "duplicate_email": False,
            "duplicate_casenum": True
        })

        flag_cols = ["duplicate_name", "duplicate_phone", "duplicate_email", "duplicate_casenum"]
        count = count_duplicate_flags(row, flag_cols)

        assert count == 3

    def test_count_zero_flags(self):
        """Should return 0 when no flags are True."""
        row = pd.Series({
            "duplicate_name": False,
            "duplicate_phone": False,
        })

        count = count_duplicate_flags(row, ["duplicate_name", "duplicate_phone"])

        assert count == 0

    def test_count_all_flags(self):
        """Should count all flags when all are True."""
        row = pd.Series({
            "duplicate_name": True,
            "duplicate_phone": True,
        })

        count = count_duplicate_flags(row, ["duplicate_name", "duplicate_phone"])

        assert count == 2


class TestMarkDuplicates:
    """Test multi-criteria duplicate marking."""

    def test_mark_with_min_flags(self):
        """Should mark as duplicate when meeting minimum flag threshold."""
        df = pd.DataFrame({
            "duplicate_name": [True, False, True],
            "duplicate_phone": [False, True, True],
        })

        result = mark_duplicates(df, ["duplicate_name", "duplicate_phone"], min_flags=2)

        # Only row 2 has 2 flags
        assert result.loc[0, "duplicate"] == False  # 1 flag
        assert result.loc[1, "duplicate"] == False  # 1 flag
        assert result.loc[2, "duplicate"] == True   # 2 flags

    def test_mark_with_min_one_flag(self):
        """Should mark as duplicate with minimum of 1 flag."""
        df = pd.DataFrame({
            "duplicate_name": [True, False, True],
            "duplicate_phone": [False, True, False],
        })

        result = mark_duplicates(df, ["duplicate_name", "duplicate_phone"], min_flags=1)

        # Rows 0, 1, 2 all have at least 1 flag
        assert result.loc[0, "duplicate"] == True
        assert result.loc[1, "duplicate"] == True
        assert result.loc[2, "duplicate"] == True

    def test_flag_count_column(self):
        """Should add num_dup_flags column with counts."""
        df = pd.DataFrame({
            "duplicate_name": [True, False, True],
            "duplicate_phone": [True, True, True],
        })

        result = mark_duplicates(df, ["duplicate_name", "duplicate_phone"], min_flags=1)

        assert result.loc[0, "num_dup_flags"] == 2
        assert result.loc[1, "num_dup_flags"] == 1
        assert result.loc[2, "num_dup_flags"] == 2
