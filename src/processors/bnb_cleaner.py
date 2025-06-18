"""
BNB bank statement cleaner module.

This module processes BNB bank statements and maps them to the standardized database schema.
Fields are mapped according to documentation:

CSV_Campo                → DB_Campo                  
----------------------------------------------------------------------------------------
Fecha                    → transaction_date           (Converted from DD/MM/YYYY to DATE)
Hora                     → transaction_time           (Format HH:MM:SS)
Oficina                  → branch_office             (Direct)
Descripción             → description               (Direct)
Referencia              → reference_number          (Direct)
Código de transacción  → bank_voucher              (VOUCHER ORIGINAL DEL BANCO)
ITF                      → itf_amount                (Impuesto a transacciones)
Débitos                 → debit_amount              (Only if has value)
Créditos                → credit_amount             (Only if has value)
Saldo                    → balance                   (Convert numeric format)
Adicionales             → additional_details        (Extra information)
"""
from datetime import datetime
import uuid
from typing import Dict, Optional
import pandas as pd
import re

def generate_company_voucher(bank_code: str, date: datetime, bank_voucher: str) -> str:
    """
    Generate a unique company voucher following a standardized format.
    Format: {BANK_CODE}-{DATE_YYYYMMDD}-{BANK_VOUCHER}
    """
    date_str = date.strftime('%Y%m%d')
    return f"{bank_code}-{date_str}-{bank_voucher}"

def extract_transaction_type(description: str) -> str:
    """
    Extract transaction type from description.
    Returns one of: DEBIT, CREDIT, TRANSFER
    """
    description = description.upper()
    
    # Check for DEBIT first as it might contain 'TRANSFERENCIA'
    if any(term in description for term in ['CARGO', 'DEBITO', 'PAGO']):
        return 'DEBIT'
    elif any(term in description for term in ['TRANSFERENCIA', 'TRF', 'TRASPASO']):
        return 'TRANSFER'
    elif any(term in description for term in ['ABONO', 'CREDITO', 'DEPOSITO']):
        return 'CREDIT'
    
    return 'OTHER'

def clean_bnb(df: pd.DataFrame, bank_code: str, account_number: str, import_batch_id: Optional[str] = None) -> pd.DataFrame:
    """
    Clean and standardize BNB bank statements to match the database schema.
    
    Args:
        df (pd.DataFrame): Raw BNB statement DataFrame
        bank_code (str): Bank code (BNB1, BNB2, or BNBUSD)
        account_number (str): Account number for the statement
        import_batch_id (str, optional): Batch ID for the import process
        
    Returns:
        pd.DataFrame: Cleaned and standardized DataFrame matching the database schema
    """
    # Validate bank code
    if bank_code not in ['BNB1', 'BNB2', 'BNBUSD']:
        raise ValueError(f"Invalid bank code {bank_code}. Must be one of: BNB1, BNB2, BNBUSD")    # Start with a clean copy of the data after the header row
    header_row = 1  # We know BNB files have account info in row 0 and headers in row 1
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = df.iloc[header_row]
    
    # Reset index after slicing
    df_clean = df_clean.reset_index(drop=True)
    
    # Remove empty rows and those without dates
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean[df_clean['Fecha'].notna()]
    
    # Process dates and times
    df_clean['transaction_date'] = pd.to_datetime(df_clean['Fecha'], format='%d/%m/%Y', errors='coerce').dt.date
    df_clean['transaction_time'] = pd.to_datetime(df_clean['Hora'], format='%H:%M:%S', errors='coerce').dt.time
    
    # Clean and map text columns with proper field names
    df_clean['bank_voucher'] = df_clean['Código de transacción'].astype(str).apply(lambda x: 
        x.strip().replace(' ', '') if pd.notna(x) else None
    )
    
    # Generate company voucher (must be unique)
    df_clean['company_voucher'] = df_clean.apply(
        lambda row: generate_company_voucher(bank_code, pd.Timestamp(row['transaction_date']), row['bank_voucher'])
        if pd.notna(row['bank_voucher']) else None,
        axis=1
    )
    
    # Map schema fields
    df_clean['bank_code'] = bank_code
    df_clean['account_number'] = account_number
    df_clean['description'] = df_clean['Descripción'].astype(str).apply(lambda x: x.strip())
    df_clean['reference_number'] = df_clean['Referencia'].astype(str).apply(lambda x: ' '.join(x.split()) if pd.notna(x) else None)
    df_clean['branch_office'] = df_clean['Oficina'].astype(str).apply(lambda x: x.strip() if pd.notna(x) else None)
    df_clean['additional_details'] = df_clean['Adicionales'].astype(str).apply(lambda x: x.strip() if pd.notna(x) != 'nan' else None)
    
    # Extract transaction type from description
    df_clean['transaction_type'] = df_clean['description'].apply(extract_transaction_type)
    
    # Convert amounts to numeric, handling commas and ensuring positive values
    df_clean['debit_amount'] = pd.to_numeric(
        df_clean['Débitos'].astype(str).str.replace(',', ''),
        errors='coerce'
    ).abs()
    
    df_clean['credit_amount'] = pd.to_numeric(
        df_clean['Créditos'].astype(str).str.replace(',', ''),
        errors='coerce'
    ).abs()
    
    df_clean['balance'] = pd.to_numeric(
        df_clean['Saldo'].astype(str).str.replace(',', ''),
        errors='coerce'
    )
    
    df_clean['itf_amount'] = pd.to_numeric(
        df_clean['ITF'].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0.00)
    
    # Add processing fields
    if import_batch_id:
        df_clean['import_batch_id'] = import_batch_id
    else:
        df_clean['import_batch_id'] = str(uuid.uuid4())
    
    # Select and order final columns according to schema
    final_columns = [
        'bank_code', 'account_number', 'company_voucher', 'bank_voucher',
        'transaction_date', 'transaction_time', 'description', 'transaction_type',
        'reference_number', 'debit_amount', 'credit_amount', 'balance', 
        'itf_amount', 'branch_office', 'additional_details', 'import_batch_id'
    ]
    
    # Ensure all schema columns exist
    for col in final_columns:
        if col not in df_clean.columns:
            df_clean[col] = None
    
    # Return only schema columns in correct order
    return df_clean[final_columns].reset_index(drop=True)
