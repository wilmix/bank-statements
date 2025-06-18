"""
BCP statement cleaner implementation.
"""
from typing import Dict
import pandas as pd
from .base_cleaner import BankStatementCleaner
from ..utils.formatter import clean_text, format_currency, standardize_date

class BCPCleaner(BankStatementCleaner):
    def get_column_mapping(self) -> Dict[str, str]:
        return {
            'Fecha': 'date',
            'Hora': 'time',
            'Glosa': 'description',
            'Tipo': 'type',
            'Suc. Age.': 'branch',
            'Usuario': 'user',
            'Importe': 'amount',
            'Saldo': 'balance',
            'Nro. Operación': 'operation_number',
            'Adicionales': 'details'
        }
        
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize BCP statement data."""
        # Find header row with 'Fecha' and 'Hora'
        header_row = None
        for i, row in df.iterrows():
            if any(isinstance(val, str) and 'Fecha' in val for val in row) and \
               any(isinstance(val, str) and 'Hora' in val for val in row):
                header_row = i
                break
        
        # Extract data with proper headers
        df_clean = df.iloc[header_row+1:].copy() if header_row is not None else df.copy()
        df_clean.columns = df.iloc[header_row] if header_row is not None else df.columns
        
        # Remove empty rows and columns
        df_clean = df_clean.dropna(how='all')
        df_clean = df_clean.dropna(axis=1, how='all')
        
        # Filter out non-transaction rows
        if 'Fecha' in df_clean.columns and 'Glosa' in df_clean.columns:
            mask = (
                df_clean['Fecha'].notna() &
                ~df_clean['Glosa'].str.contains('SALDO AL CIERRE', na=False, case=False) &
                ~((df_clean['Usuario'].str.contains('BATCH', na=False, case=False)) & 
                  (df_clean['Nro. Operación'].astype(str) == '0'))
            )
            df_clean = df_clean[mask]
        
        # Clean and standardize data types
        if 'Fecha' in df_clean.columns:
            df_clean['Fecha'] = df_clean['Fecha'].apply(standardize_date)
            
        if 'Importe' in df_clean.columns:
            df_clean['Importe'] = df_clean['Importe'].apply(format_currency)
            
        if 'Saldo' in df_clean.columns:
            df_clean['Saldo'] = df_clean['Saldo'].apply(format_currency)
            
        if 'Glosa' in df_clean.columns:
            df_clean['Glosa'] = df_clean['Glosa'].apply(clean_text)
            
        # Reset index and standardize columns
        df_clean = df_clean.reset_index(drop=True)
        return self.standardize_columns(df_clean)
