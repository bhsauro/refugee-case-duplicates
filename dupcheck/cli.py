"""Command-line interface for duplicate detection."""

import argparse
from pathlib import Path
from datetime import datetime
from dupcheck.pipeline import process_duplicates


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Detect duplicate records in refugee case data"
    )
    parser.add_argument("cases", type=Path, help="Path to Cases.xlsx file")
    parser.add_argument("people", type=Path, help="Path to People.xlsx file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: duplicates_YYYYMMDD.xlsx)",
    )

    args = parser.parse_args()

    # Default output path with timestamp
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        args.output = Path(f"duplicates_{timestamp}.xlsx")

    try:
        process_duplicates(args.cases, args.people, args.output)
        print("\nDuplicate detection complete!")
    except Exception as e:
        print(f"\nError: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
