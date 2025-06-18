"""
UNION bank statement cleaner implementation.
"""
from typing import Dict
import pandas as pd
from .base_cleaner import BankStatementCleaner
from ..utils.formatter import clean_text, format_currency, standardize_date

class UnionCleaner(BankStatementCleaner):
    def get_column_mapping(self) -> Dict[str, str]:
        return {
            'Fecha Movimiento': 'date',
            'AG': 'branch',
            'Descripción': 'description',
            'Nro Documento': 'document_number',
            'Monto': 'amount',
            'Saldo': 'balance',
            'Adicionales': 'details'
        }
        
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize UNION bank statement data."""
        # Find header row with "Fecha Movimiento"
        header_row = None
        for i, row in df.iterrows():
            if 'Fecha Movimiento' in row.values:
                header_row = i
                break
                
        if header_row is None:
            for i, row in df.iterrows():
                if any(isinstance(val, str) and 'Fecha' in val for val in row):
                    header_row = i
                    break
        
        header_row = header_row if header_row is not None else 0
        
        # Clean headers
        headers = []
        for val in df.iloc[header_row].values:
            if pd.isna(val) or not isinstance(val, str):
                headers.append('Unnamed')
            else:
                clean_val = clean_text(val)
                headers.append(clean_val)
        
        # Create clean DataFrame
        df_clean = df.iloc[header_row+1:].copy()
        df_clean.columns = headers
        
        # Remove empty rows and summary rows
        df_clean = df_clean.dropna(how='all')
        df_clean = df_clean.dropna(axis=1, how='all')
        
        # Filter valid rows
        mask = (
            df_clean['Fecha Movimiento'].astype(str).str.match(r'\d{2}/\d{2}/\d{4}') &
            df_clean['Descripción'].notna() &
            ~df_clean['Fecha Movimiento'].astype(str).str.contains('Total|Tránsito', na=False)
        )
        
        df_clean = df_clean[mask].copy()
        
        # Clean text fields
        if 'Descripción' in df_clean.columns:
            df_clean['Descripción'] = df_clean['Descripción'].apply(clean_text)
            
        if 'Adicionales' in df_clean.columns:
            df_clean['Adicionales'] = df_clean['Adicionales'].apply(clean_text)
            
        # Clean numeric fields
        if 'Monto' in df_clean.columns:
            df_clean['Monto'] = df_clean['Monto'].apply(format_currency)
            
        if 'Saldo' in df_clean.columns:
            df_clean['Saldo'] = df_clean['Saldo'].apply(format_currency)
            
        # Clean dates
        if 'Fecha Movimiento' in df_clean.columns:
            df_clean['Fecha Movimiento'] = df_clean['Fecha Movimiento'].apply(standardize_date)
        
        return self.standardize_columns(df_clean)
