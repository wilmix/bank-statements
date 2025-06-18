"""
Common path utilities for the bank statements processor.
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def get_raw_file_path(filename: str) -> Path:
    """Get the full path for a raw data file."""
    return RAW_DIR / filename

def get_processed_file_path(filename: str) -> Path:
    """Get the full path for a processed data file."""
    return PROCESSED_DIR / filename

def find_latest_file(pattern: str, directory: Path = PROCESSED_DIR) -> Path:
    """Find the most recently modified file matching a pattern in a directory."""
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)
