"""
BCP bank statement cleaner module.
Generates output compatible with bank_statements table structure.
"""
import pandas as pd
from typing import Optional
from datetime import datetime
import uuid

def generate_company_voucher(bank: str, date: datetime, voucher: str) -> str:
    """Generate a unique company voucher."""
    date_str = date.strftime('%Y%m%d')
    return f"{bank}-{date_str}-{voucher}"

def clean_bcp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize BCP bank statements according to bank_statements table structure.
    
    Args:
        df (pd.DataFrame): Raw BCP statement DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with columns matching bank_statements table
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
    
    # Remove any existing bank columns to avoid duplication
    if 'bank' in df_clean.columns:
        df_clean = df_clean.drop(columns=['bank'])
        
    # Create new DataFrame with bank identifier
    rows = []
    import_batch_id = str(uuid.uuid4())
    
    for _, row in df_clean.iterrows():
        # Convert date and time
        try:
            transaction_date = pd.to_datetime(row['Fecha'], format='%d/%m/%Y').date()
            transaction_time = pd.to_datetime(row['Hora'], format='%H:%M:%S').time()
        except:
            transaction_date = None
            transaction_time = None
            
        # Convert amount
        try:
            amount = float(str(row['Importe']).replace(',', ''))
            debit_amount = abs(amount) if amount < 0 else None
            credit_amount = amount if amount > 0 else None
        except:
            debit_amount = None
            credit_amount = None
            
        # Convert balance
        try:
            balance = float(str(row['Saldo']).replace(',', ''))
        except:
            balance = 0.0
            
        # Create voucher components
        bank_voucher = str(row['Nro. Operación'])
        account = str(row['Suc. Age.'])
        
        # Generate company voucher
        if transaction_date:
            company_voucher = generate_company_voucher('BCP', datetime.combine(transaction_date, transaction_time or datetime.min.time()), bank_voucher)
        else:
            company_voucher = f"BCP-UNKNOWN-{bank_voucher}"
            
        # Build row
        clean_row = {
            'bank_code': 'BCP',
            'account_number': account,
            'company_voucher': company_voucher,
            'bank_voucher': bank_voucher,
            'transaction_date': transaction_date,
            'transaction_time': transaction_time,
            'description': str(row['Glosa']).strip(),
            'transaction_type': str(row['Tipo']).strip(),
            'reference_number': bank_voucher,
            'transaction_code': str(row['Tipo']).strip(),
            'debit_amount': debit_amount,
            'credit_amount': credit_amount,
            'balance': balance,
            'itf_amount': 0.00,
            'branch_office': None,
            'agency_code': account,
            'user_code': str(row['Usuario']),
            'operation_number': bank_voucher,
            'additional_details': row.get('Adicionales', None),
            'import_batch_id': import_batch_id
        }
        rows.append(clean_row)
    
    # Create final DataFrame with correct schema
    df_final = pd.DataFrame(rows)
    
    # Ensure correct column order matching the database table
    desired_columns = [
        'bank_code', 'account_number', 'company_voucher', 'bank_voucher',
        'transaction_date', 'transaction_time', 'description', 'transaction_type',
        'reference_number', 'transaction_code', 'debit_amount', 'credit_amount',
        'balance', 'itf_amount', 'branch_office', 'agency_code', 'user_code',
        'operation_number', 'additional_details', 'import_batch_id'
    ]
    
    df_final = df_final[desired_columns]
    
    return df_final.reset_index(drop=True)

def clean_bcp_enrichment(df_bcp: pd.DataFrame, df_payments: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich BCP data with additional information from payments data.
    
    Merges df_bcp and df_payments on transaction details to add extra information
    like payment method, check number, etc. from df_payments to df_bcp.
    
    Returns merged DataFrame and a dictionary with statistics about the merge.
    """
    # Create copy for enrichment
    df_clean = df_bcp.copy()
    
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
    
    # Remove existing bank_code column if exists to avoid duplication
    if 'bank_code' in df_clean.columns:
        df_clean = df_clean.drop(columns=['bank_code'])
    if 'bank' in df_clean.columns:
        df_clean = df_clean.drop(columns=['bank'])
    
    # Merge logic here (to be implemented)
    
    return df_clean.reset_index(drop=True), stats
