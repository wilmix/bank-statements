"""
File management utilities for finding and managing statement files.
"""
from pathlib import Path
from typing import Optional

# Project paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

def find_bcp_clean_statement() -> Optional[Path]:
    """
    Find the most recent cleaned BCP statement.
    
    Returns:
        Path | None: Path of the file if it exists, None otherwise
    """
    statement_candidates = list(DATA_PROCESSED.glob("bcpHistoricos_clean.csv"))
    if not statement_candidates:
        return None
    return max(statement_candidates, key=lambda p: p.stat().st_mtime)

def find_payment_report() -> Optional[Path]:
    """
    Find the most recent cleaned BCP payment report.
    
    Returns:
        Path | None: Path of the file if it exists, None otherwise
    """
    report_candidates = list(DATA_PROCESSED.glob("ReporteAbonos_clean.csv"))
    if not report_candidates:
        return None
    return max(report_candidates, key=lambda p: p.stat().st_mtime)

def ensure_dirs() -> None:
    """Ensure data directories exist."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
