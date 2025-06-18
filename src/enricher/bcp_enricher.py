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
        
        # Clean dates
        if 'FECHA' in df_new.columns:
            df_new['FECHA'] = df_new['FECHA'].apply(standardize_date)
            
        # Clean amounts
        if 'MONTO ABONADO' in df_new.columns:
            df_new['MONTO ABONADO'] = df_new['MONTO ABONADO'].apply(format_currency)
            
        # Generate details column
        df_new['Adicionales'] = df_new.apply(
            lambda row: f"{row['TITULAR']} - {row['GLOSA']}" if pd.notna(row['TITULAR']) and pd.notna(row['GLOSA']) 
            else row['TITULAR'] if pd.notna(row['TITULAR']) 
            else row['GLOSA'] if pd.notna(row['GLOSA'])
            else None,
            axis=1
        )
        
        return df_new
        
    def enrich_statement(self, df_bcp: pd.DataFrame, df_payments: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Enrich BCP statement with payment details.
        
        Returns:
            tuple: (enriched_df, statistics)
        """
        print("\nStarting enrichment process...")
        print(f"BCP statement records: {len(df_bcp)}")
        print(f"Payment records: {len(df_payments)}")
        
        # Create copy for enrichment
        df_enriched = df_bcp.copy()
        
        # Verify required columns
        if 'Fecha' not in df_bcp.columns or 'Importe' not in df_bcp.columns:
            return df_bcp, {'error': 'Missing required columns in BCP statement'}
            
        if 'FECHA' not in df_payments.columns or 'MONTO ABONADO' not in df_payments.columns:
            return df_bcp, {'error': 'Missing required columns in payment report'}
            
        # Initialize statistics
        stats = {
            'total_bcp': len(df_bcp),
            'total_payments': len(df_payments),
            'matched': 0,
            'multiple_matches': 0,
            'no_match': 0
        }
        
        # Convert amounts to numeric
        df_enriched['Importe'] = df_enriched['Importe'].apply(format_currency)
        
        # Add details column if not exists
        if 'Adicionales' not in df_enriched.columns:
            df_enriched['Adicionales'] = None
            
        # Match records
        for idx, row in df_enriched.iterrows():
            # Find matches by date and amount
            matches = df_payments[
                (df_payments['FECHA'] == row['Fecha']) & 
                (df_payments['MONTO ABONADO'] == abs(row['Importe']))
            ]
            
            if len(matches) == 1:
                # Single match
                df_enriched.at[idx, 'Adicionales'] = matches['Adicionales'].iloc[0]
                stats['matched'] += 1
                
            elif len(matches) > 1:
                # Multiple matches
                df_enriched.at[idx, 'Adicionales'] = ' | '.join(matches['Adicionales'].dropna().unique())
                stats['multiple_matches'] += 1
                
                print(f"\nMultiple matches for transaction on {row['Fecha']} amount {row['Importe']}:")
                print(matches[['FECHA', 'MONTO ABONADO', 'Adicionales']].to_string())
            else:
                stats['no_match'] += 1
                
        # Show statistics
        print("\nMatching statistics:")
        print(f"Total BCP transactions: {stats['total_bcp']}")
        print(f"Total payment records: {stats['total_payments']}")
        print(f"Single matches: {stats['matched']}")
        print(f"Multiple matches: {stats['multiple_matches']}")
        print(f"Unmatched: {stats['no_match']}")
        
        return df_enriched, stats
