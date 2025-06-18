"""
BNB statement cleaner implementation.
"""
from typing import Dict
import pandas as pd
from .base_cleaner import BankStatementCleaner
from ..utils.formatter import clean_text, format_currency, standardize_date

class BNBCleaner(BankStatementCleaner):
    def get_column_mapping(self) -> Dict[str, str]:
        return {
            'Fecha': 'date',
            'Hora': 'time',
            'Oficina': 'branch',
            'Descripción': 'description',
            'Referencia': 'reference',
            'Código de transacción': 'transaction_code',
            'ITF': 'tax',
            'Débitos': 'debits',
            'Créditos': 'credits',
            'Saldo': 'balance',
            'Adicionales': 'details'
        }
        
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize BNB statement data."""
        # Find header row
        header_row = df[df.iloc[:, 0] == 'Fecha'].index[0] if 'Fecha' in df.iloc[:, 0].values else 0
        
        # Extract data with proper headers
        df_clean = df.iloc[header_row+1:].copy()
        df_clean.columns = df.iloc[header_row]
        
        # Remove empty rows and rows without date
        df_clean = df_clean.dropna(how='all')
        df_clean = df_clean[df_clean['Fecha'].notna()]
        
        # Clean text columns
        text_columns = ['Referencia', 'Descripción', 'Código de transacción', 'Adicionales']
        for col in text_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(
                    lambda x: clean_text(x, remove_all_spaces=(col=='Código de transacción'))
                )
        
        # Clean numeric columns
        numeric_columns = ['Débitos', 'Créditos', 'Saldo', 'ITF']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(format_currency)
        
        # Clean dates
        if 'Fecha' in df_clean.columns:
            df_clean['Fecha'] = df_clean['Fecha'].apply(standardize_date)
        
        # Reverse order for chronological display and reset index
        df_clean = df_clean.iloc[::-1].reset_index(drop=True)
        
        return self.standardize_columns(df_clean)
