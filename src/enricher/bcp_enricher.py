"""
BCP payment details enrichment module.
"""
from pathlib import Path
import pandas as pd
from typing import Dict, Tuple
from ..utils.formatter import clean_text, format_currency, standardize_date

class BCPEnricher:
    def clean_payment_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize BCP payment report data."""
        # Find header row
        header_row = None
        for i, row in df.iterrows():
            if any(isinstance(val, str) and 'FECHA' in str(val).upper() for val in row) and \
               any(isinstance(val, str) and 'MONTO ABONADO' in str(val).upper() for val in row):
                header_row = i
                break
        
        if header_row is None:
            return pd.DataFrame()
            
        # Create clean DataFrame
        df_clean = df.iloc[header_row+1:].copy()
        df_clean.columns = df.iloc[header_row]
        
        # Select relevant columns
        required_columns = [
            'CANAL', 'FECHA', 'HORA', 'MONTO ABONADO',
            'MONTO OP.', 'MONEDA OP.', 'GLOSA', 'TITULAR'
        ]
        
        df_new = pd.DataFrame()
        for col in required_columns:
            if col in df_clean.columns:
                df_new[col] = df_clean[col]
            else:
                df_new[col] = None
                
        # Remove empty rows
        df_new = df_new.dropna(how='all')
        
        # Clean dates and convert to datetime
        if 'FECHA' in df_new.columns:
            df_new['FECHA'] = pd.to_datetime(df_new['FECHA'].apply(standardize_date))
            
        # Clean amounts
        if 'MONTO ABONADO' in df_new.columns:
            df_new['MONTO ABONADO'] = df_new['MONTO ABONADO'].apply(format_currency)
            
        # Generate enriched details column
        df_new['Adicionales'] = df_new.apply(
            lambda row: ' - '.join(filter(pd.notna, [
                row.get('TITULAR', None),
                row.get('GLOSA', None),
                f"Canal: {row.get('CANAL', '')}" if pd.notna(row.get('CANAL', None)) else None
            ])),
            axis=1
        )
        
        return df_new
        
    def enrich_statement(self, df_bcp: pd.DataFrame, df_payments: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Enrich BCP statement with payment details according to updated mapping schema.
        
        Args:
            df_bcp (pd.DataFrame): Cleaned BCP statement
            df_payments (pd.DataFrame): Cleaned payment details
            
        Returns:
            tuple: (enriched_df, statistics)
        """
        print("\nStarting enrichment process...")
        print(f"BCP statement records: {len(df_bcp)}")
        print(f"Payment records: {len(df_payments)}")
        
        # Create copy for enrichment
        df_enriched = df_bcp.copy()
        
        # Verify required columns
        required_bcp = ['Fecha', 'Importe', 'Nro. Operación']
        required_payments = ['FECHA', 'MONTO ABONADO', 'Adicionales']
        
        if not all(col in df_bcp.columns for col in required_bcp):
            return df_bcp, {'error': f'Missing required columns in BCP statement: {required_bcp}'}
            
        if not all(col in df_payments.columns for col in required_payments):
            return df_bcp, {'error': f'Missing required columns in payment report: {required_payments}'}
            
        # Initialize statistics
        stats = {
            'total_bcp': len(df_bcp),
            'total_payments': len(df_payments),
            'matched': 0,
            'multiple_matches': 0,
            'no_match': 0
        }
          # Ensure datetime for matching
        df_enriched['Fecha'] = pd.to_datetime(df_enriched['Fecha'])
        df_payments['FECHA'] = pd.to_datetime(df_payments['FECHA'], format='%d/%m/%Y')
        
        # Add details column if not exists
        if 'Adicionales' not in df_enriched.columns:
            df_enriched['Adicionales'] = None
            
        # Match records by date and amount
        for idx, bcp_row in df_enriched.iterrows():            # Convert amounts to float and round
            bcp_amount = round(float(abs(bcp_row['Importe'])), 2)
            payment_amounts = df_payments['MONTO ABONADO'].astype(float).round(2)
            
            matches = df_payments[
                (df_payments['FECHA'] == bcp_row['Fecha']) & 
                (payment_amounts == bcp_amount)
            ]
            
            if len(matches) == 1:
                # Single match found
                df_enriched.at[idx, 'Adicionales'] = matches.iloc[0]['Adicionales']
                stats['matched'] += 1
            elif len(matches) > 1:
                # Multiple matches - concatenate details
                df_enriched.at[idx, 'Adicionales'] = ' | '.join(matches['Adicionales'].dropna())
                stats['multiple_matches'] += 1
            else:
                stats['no_match'] += 1
                
        return df_enriched, stats
