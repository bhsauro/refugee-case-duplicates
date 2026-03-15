# Testing Strategy

This document outlines the testing approach for the refugee case duplicate detection tool. While a comprehensive test suite is not currently implemented, this strategy documents how testing would be structured for production use.

## Test Coverage Plan

### Unit Tests

**Normalization Functions** (`dupcheck/normalize.py`)
- `normalize_arabic_numerals()`: Eastern Arabic (٠-٩) → Western (0-9) conversion
  - Test cases: pure Eastern Arabic, mixed numerals, empty strings, null values
- `add_country_code()`: Country code prefix handling
  - Test cases: numbers with/without codes, invalid codes, null values
- `clean_phone_spaces()`: Space-delimited phone number cleaning
  - Test cases: various spacing patterns, numbers without spaces
- `normalize_unhcr_case_number()`: UNHCR case number formatting
  - Test cases: various UNHCR formats, edge cases

**Extraction Functions** (`dupcheck/extract.py`)
- `extract_and_expand()`: Regex extraction and column expansion
  - Test cases: multiple matches, single match, no matches, null values
- `combine_fields()`: Multi-column concatenation
  - Test cases: all populated, some null, all null

**Duplicate Detection** (`dupcheck/detect.py`)
- `find_duplicates()`: Core duplicate detection logic
  - Test cases: known duplicates, non-duplicates, within-ID duplicates (should be ignored)
  - Edge cases: empty dataframes, single row, all duplicates
- `mark_duplicates()`: Multi-criteria flagging
  - Test cases: various flag combinations (1, 2, 3, 4 criteria matched)

**I/O Operations** (`dupcheck/io.py`)
- `read_cases()` and `read_people()`: File reading with validation
  - Test cases: valid files, missing columns, missing files, corrupt files
- Schema validation edge cases

### Integration Tests

**Full Pipeline** (`dupcheck/pipeline.py`)
- End-to-end processing with sample data
  - Input: Small test Cases.xlsx and People.xlsx files
  - Verify: Correct output structure, expected duplicates flagged
- Multi-person cases (3+ people per case)
- Single-person cases
- Cases with no people (orphaned cases)
- Mixed scenarios

### Regression Tests

**Known Duplicate Pairs**
- Maintain test dataset with documented duplicate relationships
- Ensure these always match after code changes
- Examples:
  - Same phone number in different formats ("961 123 456" vs "٩٦١١٢٣٤٥٦")
  - Same name in Latin and native script
  - Various UNHCR case number formats

**Case Number Format Handling**
- SIV-NVC: `NVCSIV1234567890`
- SIV-Embassy: `ABC1234567890`
- USRAP: `AB-123456`
- UNHCR: Various country/year/serial combinations

### Data Quality Tests

**Schema Validation**
- Required columns present in input files
- Column data types match expectations
- ID formats (person IDs, case IDs) match expected patterns

**Data Integrity**
- Phone numbers don't exceed 15 digits (E.164 standard)
- Email addresses match valid email pattern
- Case numbers conform to known formats

**Edge Cases**
- Null values in person data
- Empty strings vs. null values
- Cases with no Tags field (no person IDs)
- Unicode handling (Arabic script, special characters)

## Test Data

### Fixtures
Would create small, realistic test datasets:
- `tests/fixtures/test_cases.xlsx`: 10-20 cases with various scenarios
- `tests/fixtures/test_people.xlsx`: 20-30 people with known duplicates
- Documented expected outcomes for each test case

### Synthetic Data Generation
For larger-scale testing, would implement:
- Generator for realistic names (including Arabic script)
- Phone number generator with various formats
- Case number generator for all supported types

## Testing Tools

**Framework**: pytest
- Fixtures for test data loading
- Parameterized tests for multiple input scenarios
- Coverage reporting

**Data Validation**: pandas.testing
- `assert_frame_equal()` for DataFrame comparisons
- `assert_series_equal()` for column validation

**Mocking**: unittest.mock
- Mock file I/O for error condition testing
- Mock external dependencies if added

## Continuous Integration

For production deployment, would integrate:
- GitHub Actions or similar CI/CD
- Run tests on: push, pull request, scheduled (nightly)
- Coverage threshold: aim for 80%+ coverage
- Automated regression suite

## Why Not Implemented

This tool was developed for a legacy case management system that has since been deprecated. The organization has migrated to a modern CRM with built-in duplicate detection. Given the system's deprecated status and the focus on demonstrating data engineering concepts for portfolio purposes, a full test suite was not prioritized.

However, the testing strategy documented here reflects production-level thinking about code quality, edge cases, and maintainability.

## Logging & Observability

The current implementation uses `print()` statements for CLI user feedback. For production deployment (scheduled batch jobs, Lambda functions, Airflow DAGs), logging would be enhanced:

**Structured Logging**
```python
import logging
import json

logger = logging.getLogger(__name__)

# JSON-formatted logs for aggregation in CloudWatch/Datadog
logger.info(json.dumps({
    'event': 'duplicate_detection_complete',
    'duplicates_found': len(duplicates),
    'processing_time_seconds': elapsed,
    'timestamp': datetime.utcnow().isoformat()
}))
```

**Metrics to Track**
- Processing time per stage (read, normalize, detect, write)
- Duplicate counts by type (name, phone, email, case number)
- Input record counts (cases, people)
- Error rates and types
- Memory usage for performance monitoring

**Alerting Thresholds**
- Unexpected spike in duplicate rate (possible data quality issue)
- Schema validation failures (upstream system changes)
- Processing time exceeds SLA
- Zero duplicates found (possible pipeline failure)

**Audit Trail**
- Which cases/people were flagged as duplicates
- When detection was run
- Who initiated the process (user, scheduled job, API call)

## Future Work

If this tool were to be deployed in a production environment, the test suite would be implemented following this strategy, with particular emphasis on:
1. Regression tests for known duplicate patterns
2. Data quality validation to catch schema changes early
3. Integration tests to ensure end-to-end workflow integrity
4. Structured logging with metrics and alerting for operational monitoring
