"""
Bank statement file reader module.
"""
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

def read_bank_statement(file_path: Path) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Read a bank statement Excel file and return the DataFrame and any error message.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        tuple: (DataFrame, error_message)
            - DataFrame with the file contents
            - Error message if there was a problem, None otherwise
    """
    try:
        df = pd.read_excel(file_path, header=0)
        if df.empty:
            return df, "File is empty"
        return df, None
    except FileNotFoundError:
        return pd.DataFrame(), f"File not found: {file_path}"
    except Exception as e:
        return pd.DataFrame(), f"Error reading file: {str(e)}"
