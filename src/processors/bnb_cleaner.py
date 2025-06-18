"""
BNB bank statement cleaner module.
"""
import pandas as pd

def clean_bnb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean BNB bank statements.
    
    Args:
        df (pd.DataFrame): Raw BNB statement DataFrame
        
    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame
    """
    # Find the row containing actual headers
    header_row = df[df.iloc[:, 0] == 'Fecha'].index[0] if 'Fecha' in df.iloc[:, 0].values else 0
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Remove empty rows and those without dates
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean[df_clean['Fecha'].notna()]
    
    # Clean text columns
    text_cols = ['Referencia', 'Descripción', 'Código de transacción', 'Adicionales']
    for col in text_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).apply(lambda x: 
                x.strip() if pd.notna(x) else x
            )
    
    # Clean references and codes specifically
    if 'Referencia' in df_clean.columns:
        df_clean['Referencia'] = df_clean['Referencia'].astype(str).apply(lambda x: 
            ' '.join(x.split()) if pd.notna(x) else x
        )
    
    if 'Código de transacción' in df_clean.columns:
        df_clean['Código de transacción'] = df_clean['Código de transacción'].astype(str).apply(lambda x: 
            x.strip().replace(' ', '') if pd.notna(x) else x
        )
    
    # Convert amounts to numeric
    amount_cols = ['Débitos', 'Créditos', 'Saldo', 'ITF']
    for col in amount_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(
                df_clean[col].astype(str).str.replace(',', ''),
                errors='coerce'
            )
    
    # Reverse order to show earliest transactions first
    df_clean = df_clean.iloc[::-1].reset_index(drop=True)
    
    return df_clean
