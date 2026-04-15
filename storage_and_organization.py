"""
storage_and_organization.py

Organize project files and document the repository structure.

This script:
1. Creates a standard directory structure for the project
2. Verifies that expected raw data files exist
3. Standardizes file placement and naming
4. Generates a file inventory
5. Writes a short documentation file describing the storage strategy

Expected inputs (created by acquire_data.py):
- data/raw/fred_dff_raw.json
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv
- data/raw/CHECKSUMS.sha256
"""

from pathlib import Path
import shutil
import csv


PROJECT_ROOT = Path(".")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
DOCS_DIR = PROJECT_ROOT / "docs"

EXPECTED_RAW_FILES = [
    RAW_DIR / "fred_dff_raw.json",
    RAW_DIR / "fred_dff.csv",
    RAW_DIR / "sp500_raw.csv",
    RAW_DIR / "CHECKSUMS.sha256",
]


def ensure_directories() -> None:
    """Create the standard project directory structure."""
    for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, DOCS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def verify_raw_files() -> None:
    """Check that the required raw files exist."""
    missing = [path for path in EXPECTED_RAW_FILES if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path.as_posix()}" for path in missing)
        raise FileNotFoundError(
            "The following expected raw files are missing:\n"
            f"{missing_list}\n"
            "Run acquire_data.py first."
        )


def create_placeholder_readme_files() -> None:
    """Create small placeholder files for directories if desired."""
    readmes = {
        RAW_DIR / "README.md": (
            "# Raw Data\n\n"
            "This directory contains unmodified raw data acquired from external sources.\n"
            "Files here should preserve source structure as much as possible.\n"
        ),
        PROCESSED_DIR / "README.md": (
            "# Processed Data\n\n"
            "This directory contains cleaned, transformed, or integrated datasets.\n"
        ),
        OUTPUT_DIR / "README.md": (
            "# Output\n\n"
            "This directory contains analysis outputs such as tables, figures, and final results.\n"
        ),
    }

    for path, content in readmes.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def write_data_structure_doc() -> Path:
    """Write a short markdown document describing storage and organization."""
    doc_path = DOCS_DIR / "DATA_STRUCTURE.md"
    content = """# Data Structure and Organization

## Directory layout

- `data/raw/`
  - Original data acquired from external sources
  - Includes source-preserving files and integrity checksums
- `data/processed/`
  - Cleaned, standardized, and integrated datasets
- `data/output/`
  - Analysis outputs such as tables, charts, and derived results
- `docs/`
  - Supporting project documentation

## Naming conventions

- Lowercase file names
- Words separated with underscores
- Source and content reflected in file names
- Examples:
  - `fred_dff_raw.json`
  - `fred_dff.csv`
  - `sp500_raw.csv`

## Storage strategy

This project separates raw, processed, and output artifacts to support:
- transparency
- reproducibility
- easier workflow automation
- clearer provenance tracking
"""
    doc_path.write_text(content, encoding="utf-8")
    return doc_path


def generate_file_inventory() -> Path:
    """Generate a CSV inventory of files in the data and docs directories."""
    inventory_path = DOCS_DIR / "file_inventory.csv"

    rows = []
    for base_dir in [DATA_DIR, DOCS_DIR]:
        for path in sorted(base_dir.rglob("*")):
            if path.is_file():
                rows.append({
                    "relative_path": path.relative_to(PROJECT_ROOT).as_posix(),
                    "parent_directory": path.parent.relative_to(PROJECT_ROOT).as_posix(),
                    "file_name": path.name,
                    "suffix": path.suffix,
                    "size_bytes": path.stat().st_size,
                })

    with open(inventory_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "relative_path",
                "parent_directory",
                "file_name",
                "suffix",
                "size_bytes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return inventory_path


def main() -> None:
    print("Setting up storage and organization structure...")

    ensure_directories()
    verify_raw_files()
    create_placeholder_readme_files()

    structure_doc = write_data_structure_doc()
    inventory_file = generate_file_inventory()

    print("Storage and organization complete.")
    print(f"Documentation written to: {structure_doc}")
    print(f"Inventory written to: {inventory_file}")


if __name__ == "__main__":
    main()