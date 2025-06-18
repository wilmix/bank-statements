"""
Data formatting utilities for bank statements.
"""
import pandas as pd
from typing import Union, Optional

def format_currency(value: Union[str, float, int]) -> float:
    """
    Convert a currency string or number to float.
    Handles commas, spaces, and other formatting.
    """
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # Remove commas and spaces
    clean_value = str(value).replace(',', '').replace(' ', '')
    try:
        return float(clean_value)
    except ValueError:
        return None

def clean_text(text: str, remove_all_spaces: bool = False) -> Optional[str]:
    """
    Clean text by removing extra whitespace and special characters.
    
    Args:
        text: Text to clean
        remove_all_spaces: If True, removes all spaces, if False normalizes spaces
    """
    if pd.isna(text):
        return None
        
    # Convert to string and clean special characters
    clean = str(text).replace('\\t', ' ').replace('\\n', ' ').replace('\t', ' ').replace('\n', ' ')
    
    if remove_all_spaces:
        return clean.replace(' ', '')
    
    # Normalize spaces (multiple spaces to single space)
    return ' '.join(clean.split())

def standardize_date(date: Union[str, pd.Timestamp], as_string: bool = True) -> Union[str, pd.Timestamp]:
    """
    Standardize date format.
    
    Args:
        date: Date to standardize
        as_string: If True, returns dd/mm/yyyy string, if False returns pandas Timestamp
    """
    if pd.isna(date):
        return None
        
    try:
        ts = pd.to_datetime(date, dayfirst=True)
        return ts.strftime('%d/%m/%Y') if as_string else ts
    except:
        return None
