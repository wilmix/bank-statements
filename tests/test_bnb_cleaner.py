"""
Test module for the BNB bank statement cleaner.
"""
import pandas as pd
from datetime import date, time
from src.processors.bnb_cleaner import clean_bnb, generate_company_voucher, extract_transaction_type

def test_clean_bnb():
    """Test the BNB statement cleaning process."""
    # Create sample input data
    input_data = {
        'Fecha': ['30/05/2025', '30/05/2025'],
        'Hora': ['15:20:16', '16:30:00'],
        'Oficina': ['LA PAZ-AGENCIA CENTRAL', 'SANTA CRUZ-CENTRAL'],
        'Descripción': ['Abono Cta por ACH', 'Cargo por transferencia'],
        'Referencia': ['1041305633', '1041305634'],
        'Código de transacción': ['1O5T377394', '1O5T377395'],
        'ITF': ['0.00', '1.50'],
        'Débitos': ['0.00', '1000.00'],
        'Créditos': ['210.00', '0.00'],
        'Saldo': ['289024.23', '288024.23'],
        'Adicionales': [
            'Cuenta Origen: 1041305633. Nombre Originante: MANEJO INTEGRADO DE PLAGAS MIP S.R.L..',
            'Transferencia a cuenta 123456'
        ]
    }
    df = pd.DataFrame(input_data)
    
    # Clean the data
    clean_df = clean_bnb(df, 'BNB1', '1041305633')
    
    # Verify results
    assert len(clean_df) == 2
    
    # Check first row (credit transaction)
    assert clean_df.iloc[0]['bank_code'] == 'BNB1'
    assert clean_df.iloc[0]['account_number'] == '1041305633'
    assert clean_df.iloc[0]['bank_voucher'] == '1O5T377394'
    assert clean_df.iloc[0]['company_voucher'] == 'BNB1-20250530-1O5T377394'
    assert clean_df.iloc[0]['transaction_date'] == date(2025, 5, 30)
    assert clean_df.iloc[0]['transaction_time'] == time(15, 20, 16)
    assert clean_df.iloc[0]['description'] == 'Abono Cta por ACH'
    assert clean_df.iloc[0]['transaction_type'] == 'CREDIT'
    assert clean_df.iloc[0]['reference_number'] == '1041305633'
    assert clean_df.iloc[0]['debit_amount'] == 0.00
    assert clean_df.iloc[0]['credit_amount'] == 210.00
    assert clean_df.iloc[0]['balance'] == 289024.23
    assert clean_df.iloc[0]['itf_amount'] == 0.00
    assert clean_df.iloc[0]['branch_office'] == 'LA PAZ-AGENCIA CENTRAL'
    assert 'MANEJO INTEGRADO DE PLAGAS MIP S.R.L.' in clean_df.iloc[0]['additional_details']
    assert clean_df.iloc[0]['import_batch_id'] is not None
    
    # Check second row (debit transaction)
    assert clean_df.iloc[1]['transaction_type'] == 'DEBIT'
    assert clean_df.iloc[1]['debit_amount'] == 1000.00
    assert clean_df.iloc[1]['credit_amount'] == 0.00
    assert clean_df.iloc[1]['itf_amount'] == 1.50

def test_generate_company_voucher():
    """Test company voucher generation."""
    test_date = date(2025, 5, 30)
    bank_voucher = '1O5T377394'
    
    voucher = generate_company_voucher('BNB1', test_date, bank_voucher)
    assert voucher == 'BNB1-20250530-1O5T377394'

def test_extract_transaction_type():
    """Test transaction type extraction from descriptions."""
    assert extract_transaction_type('Abono Cta por ACH') == 'CREDIT'
    assert extract_transaction_type('Cargo por transferencia') == 'DEBIT'
    assert extract_transaction_type('TRANSFERENCIA ENTRE CUENTAS') == 'TRANSFER'
    assert extract_transaction_type('OTRO TIPO DE OPERACION') == 'OTHER'
