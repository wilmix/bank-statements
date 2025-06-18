"""
BCP bank statement cleaner module.
"""
import pandas as pd
from typing import Optional

def clean_bcp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize BCP bank statements.
    
    Args:
        df (pd.DataFrame): Raw BCP statement DataFrame
        
    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame
    """
    # Find header row with 'Fecha' and 'Hora'
    header_row = None
    for i, row in df.iterrows():
        if (any(isinstance(val, str) and 'Fecha' in val for val in row) and 
            any(isinstance(val, str) and 'Hora' in val for val in row)):
            header_row = i
            break
    header_row = header_row if header_row is not None else 0
        
    # Use headers and clean data
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Remove empty rows/columns
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.dropna(axis=1, how='all')
    
    # Filter real transactions
    if 'Fecha' in df_clean.columns and 'Glosa' in df_clean.columns:
        mask = (
            df_clean['Fecha'].notna() &
            ~df_clean['Glosa'].str.contains('SALDO AL CIERRE', na=False, case=False) &
            ~((df_clean['Usuario'].str.contains('BATCH', na=False, case=False)) & 
              (df_clean['Nro. Operación'].astype(str) == '0'))
        )
        df_clean = df_clean[mask]
    
    return df_clean.reset_index(drop=True)
