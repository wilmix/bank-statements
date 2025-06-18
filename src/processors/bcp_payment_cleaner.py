"""
BCP payment report cleaner module.
"""
import pandas as pd

def clean_bcp_payments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize BCP payment reports.
    
    Args:
        df (pd.DataFrame): Raw payment report DataFrame
        
    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame
    """
    print("\nStarting payment report cleaning...")
    
    # Find header row
    header_row = None
    for i, row in df.iterrows():
        if any(isinstance(val, str) and 'FECHA' in str(val).upper() for val in row) and \
           any(isinstance(val, str) and 'MONTO ABONADO' in str(val).upper() for val in row):
            header_row = i
            break
    
    if header_row is None:
        print("Could not find header row in payment report")
        return pd.DataFrame()
    
    print(f"Header row found at index: {header_row}")
    
    # Create clean DataFrame
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = df.iloc[header_row]
    
    # Select relevant columns
    required_cols = [
        'CANAL', 'FECHA', 'HORA', 'MONTO ABONADO',
        'MONTO OP.', 'MONEDA OP.', 'GLOSA', 'TITULAR'
    ]
    
    # Create new DataFrame
    df_new = pd.DataFrame()
    for col in required_cols:
        if col in df_clean.columns:
            df_new[col] = df_clean[col]
            print(f"Column found: {col}")
        else:
            print(f"Warning: Column {col} not found")
            df_new[col] = None
    
    # Remove empty rows
    df_new = df_new.dropna(how='all')
    print(f"Total rows after removing empty: {len(df_new)}")
    
    # Clean dates
    if 'FECHA' in df_new.columns:
        print("\nProcessing dates...")
        dates_before = df_new['FECHA'].head()
        df_new['FECHA'] = pd.to_datetime(
            df_new['FECHA'],
            dayfirst=True
        ).dt.strftime('%d/%m/%Y')
        print("Date conversion example:")
        print("Before:", dates_before.tolist())
        print("After:", df_new['FECHA'].head().tolist())
    
    # Clean amounts
    if 'MONTO ABONADO' in df_new.columns:
        print("\nProcessing amounts...")
        amounts_before = df_new['MONTO ABONADO'].head()
        df_new['MONTO ABONADO'] = pd.to_numeric(
            df_new['MONTO ABONADO'].astype(str).str.replace(',', ''),
            errors='coerce'
        )
        print("Amount conversion example:")
        print("Before:", amounts_before.tolist())
        print("After:", df_new['MONTO ABONADO'].head().tolist())
    
    # Generate Additional Info column
    print("\nGenerating Additional Info column...")
    df_new['Adicionales'] = df_new.apply(
        lambda row: f"{row['TITULAR']} - {row['GLOSA']}" if pd.notna(row['TITULAR']) and pd.notna(row['GLOSA']) 
        else row['TITULAR'] if pd.notna(row['TITULAR']) 
        else row['GLOSA'] if pd.notna(row['GLOSA'])
        else None,
        axis=1
    )
    
    print(f"\nProcess complete. Total records: {len(df_new)}")
    return df_new
