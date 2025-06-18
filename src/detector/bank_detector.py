"""
Bank and account detection module.
"""
import pandas as pd
from typing import Tuple, Optional

def detect_bank_and_account(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Detect bank and account number from statement content.
    
    Args:
        df: DataFrame with bank statement data
        
    Returns:
        tuple: (bank_name, account_number)
            bank_name: 'BNB1', 'BNB2', 'BCP', 'UNION', or 'Unknown'
            account_number: The detected account number or 'Not found'
    """    # Check BNB accounts - first check in data for "Número De cuenta"
    for i, row in df.iterrows():
        for j, val in enumerate(row):
            if isinstance(val, str) and val.strip() == 'Número De cuenta':
                if j + 1 < len(row):  # Check next column for account number
                    account = str(row[j + 1]).strip()
                    if account == '1000092297':
                        return 'BNB1', account
                    if account == '1000264616':
                        return 'BNB2', account
                    if account == '1400017553':
                        return 'BNBUSD', account
                    if account.startswith('10000'):
                        return 'BNB1', account  # Default to BNB1 for other 10000* accounts
                
    # Check UNION account
    for _, row in df.iterrows():
        for val in row:
            if isinstance(val, str) and 'Cuenta:' in val:
                for v in row:
                    if isinstance(v, (str, int)) and str(v).strip().isdigit() and len(str(v).strip()) > 8:
                        return 'UNION', str(v).strip()
                        
    # Check BCP account pattern
    for _, row in df.iterrows():
        for val in row:
            if isinstance(val, str) and '-' in val and val.count('-') >= 2:
                return 'BCP', val.strip()
                
    return 'Unknown', 'Not found'

def detect_bcp_payment_report(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Check if the DataFrame is a BCP payment details report.
    
    Args:
        df: DataFrame to check
        
    Returns:
        tuple: (is_payment_report, account_number)
            is_payment_report: True if it's a payment report
            account_number: Account number if found, None otherwise
    """
    # Check header for payment report indicator
    for i in range(min(5, len(df))):
        for val in df.iloc[i]:
            if isinstance(val, str) and "CONSULTA DE ABONOS RECIBIDOS" in val.upper():
                # Look for account number
                for j in range(i, min(i + 5, len(df))):
                    for val in df.iloc[j]:
                        if isinstance(val, str) and "Nro. Cuenta Destino:" in val:
                            account = val.split(":")[-1].strip()
                            return True, account
                return True, None
    return False, None
