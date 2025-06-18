"""
Base cleaner interface for bank statements.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BankStatementCleaner(ABC):
    """Abstract base class for bank statement cleaners."""
    
    @abstractmethod
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize bank statement data."""
        pass
        
    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """Get mapping of source columns to standard column names."""
        pass
        
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names using the mapping."""
        mapping = self.get_column_mapping()
        df_clean = df.copy()
        df_clean.columns = [mapping.get(col, col) for col in df.columns]
        return df_clean
