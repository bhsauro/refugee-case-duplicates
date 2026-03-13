# Refugee Case Duplicate Checker

A data engineering tool designed to identify whether applicants for legal assistance in refugee case management already exist in the system—whether they have active cases or have applied for assistance in the past.

This tool detects duplicate records across multiple criteria including names, phone numbers, emails, and external case numbers (UNHCR, USRAP, SIV programs). It helps prevent duplicate case creation and ensures accurate tracking of client interactions.

**Note:** The data schemas and ID patterns shown in this codebase are no longer in use. This tool was built for a legacy case management system that has since been replaced with a modern relational database.

## Features

- **Multi-criteria duplicate detection**: Checks for duplicates across names, phone numbers, emails, and case numbers
- **Phone number normalization**: Handles Eastern Arabic numerals, adds country codes, validates formats
- **Case number parsing**: Extracts and validates SIV, USRAP, and UNHCR case numbers
- **Clean architecture**: Organized into logical modules with clear separation of concerns
- **Type-safe**: Uses type hints for better code clarity and IDE support

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd duplicates-refactor

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run the duplicate checker from the command line:

```bash
python -m dupcheck.cli Cases.xlsx People.xlsx
```

With custom output file:
```bash
python -m dupcheck.cli Cases.xlsx People.xlsx -o results.xlsx
```

### As a Python Library

Import and use programmatically in your own scripts:

```python
from pathlib import Path
from dupcheck.pipeline import process_duplicates

# Run the full pipeline
process_duplicates(
    cases_path=Path("Cases.xlsx"),
    people_path=Path("People.xlsx"),
    output_path=Path("duplicates.xlsx")
)
```

Or use individual modules for custom workflows:

```python
from dupcheck import io, extract, normalize, detect
from dupcheck.constants import PERSON_ID_PATTERN, get_country_code

# Build your own pipeline
cases = io.read_cases(Path("Cases.xlsx"))
people = io.read_people(Path("People.xlsx"))

# Extract person IDs
person_ids = extract.extract_and_expand(
    cases, "Tags", "person_ids", PERSON_ID_PATTERN
)

# Normalize phone numbers
phone_clean = normalize.normalize_arabic_numerals(cases["Phone"])

# Get country code
code = get_country_code("Lebanon")  # Returns "961"

# Detect duplicates on specific columns
duplicates = detect.find_duplicates(cases, ["Name", "Email"])
```

## Input Files

### Cases.xlsx
Expected columns:
- Unique ID
- Client
- Office
- External Case Number
- Stage
- Country
- Country of Origin
- Date of Initial Contact
- Tags

### People.xlsx
Expected columns:
- Unique ID
- Full Name
- Full Name in Native Script
- Preferred Email
- Phone Number

## Output

The tool generates an Excel file containing:
- Unique ID (Case)
- Unique ID (Person)
- Office
- Stage
- Date of Initial Contact
- num_dup_flags (count of duplicate criteria matched)
- duplicate_name (boolean)
- duplicate_phone (boolean)
- duplicate_email (boolean)
- duplicate_casenum (boolean)
- Names (concatenated)
- Phone Numbers (normalized)
- Emails (extracted)
- Case Numbers (parsed)

## Project Structure

```
dupcheck/
├── __init__.py
├── constants.py    # Configuration constants and patterns
├── extract.py      # Data extraction utilities
├── normalize.py    # Data normalization functions
├── detect.py       # Duplicate detection logic
├── io.py           # File I/O operations
├── pipeline.py     # Main duplicate detection pipeline (library API)
└── cli.py          # Command-line interface
```

## How It Works

1. **Load Data**: Reads Cases.xlsx and People.xlsx files
2. **Extract Person IDs**: Parses person IDs from case tags using regex
3. **Merge Data**: Combines case and person data (handles multiple people per case)
4. **Normalize Data**:
   - Converts Eastern Arabic numerals to Western
   - Cleans phone numbers and adds country codes
   - Standardizes case number formats
5. **Detect Duplicates**: Identifies duplicate values across:
   - Full names
   - Email addresses
   - Phone numbers
   - Case numbers
6. **Generate Report**: Creates Excel file with flagged duplicates

## Technical Details

### Phone Number Normalization
- Converts Eastern Arabic (٠-٩) to Western numerals (0-9)
- Removes special characters and formatting
- Adds country calling codes based on location
- Validates against configured country code prefixes

### Case Number Parsing
Handles multiple case number formats:
- **SIV-NVC**: `NVCSIV` + 10 digits
- **SIV-Embassy**: 3 letters + 10 digits (excluding SIV prefix)
- **USRAP**: 2 letters + hyphen + 6 digits
- **UNHCR**: Complex format with country/year/serial components

### Duplicate Detection Algorithm
1. Melt DataFrame to check all values in specified columns
2. Remove within-ID duplicates (same person listed twice)
3. Identify cross-ID duplicates (different records with matching values)
4. Flag records with one or more duplicate matches
5. Count duplicate flags per record for prioritization

## Requirements

- Python 3.10+
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- xlsxwriter >= 3.1.0

## License

MIT

## Author

Brooke Sauro
