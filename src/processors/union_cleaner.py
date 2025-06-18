"""
UNION bank statement cleaner module.
"""
import pandas as pd

def clean_union(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean UNION bank statements.
    
    Args:
        df (pd.DataFrame): Raw UNION statement DataFrame
        
    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame
    """
    # Find row with "Fecha Movimiento"
    header_row = None
    for i, row in df.iterrows():
        if 'Fecha Movimiento' in row.values:
            header_row = i
            break
    if header_row is None:
        for i, row in df.iterrows():
            if any(isinstance(val, str) and 'Fecha' in val for val in row):
                header_row = i
    header_row = header_row if header_row is not None else 0
    
    print(f"\nHeader row found at index: {header_row}")
    
    # Extract and clean headers
    headers = []
    for val in df.iloc[header_row].values:
        if pd.isna(val) or not isinstance(val, str):
            headers.append('Unnamed')
        else:
            clean_val = val.strip().replace('\n', ' ').replace('\\n', ' ').strip()
            headers.append(clean_val)
    
    # Create clean DataFrame
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Remove empty rows and columns
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.dropna(axis=1, how='all')
    
    # Filter valid rows
    mask = (
        df_clean['Fecha Movimiento'].astype(str).str.match(r'\d{2}/\d{2}/\d{4}') &
        df_clean['Descripción'].notna() &
        ~df_clean['Fecha Movimiento'].astype(str).str.contains('Total|Tránsito', na=False)
    )
    
    df_clean = df_clean[mask].copy()
    df_clean = df_clean.reset_index(drop=True)
    
    # Column mapping - look for variations in column names
    column_map = {
        'Fecha Movimiento': ['Fecha Movimiento', 'FECHA MOVIMIENTO', 'Fecha'],
        'AG': ['AG', 'Agencia', 'AGENCIA'],
        'Descripción': ['Descripción', 'DESCRIPCIÓN', 'DESCRIPCION', 'Glosa', 'GLOSA'],
        'Nro Documento': ['Nro Documento', 'NRO DOCUMENTO', 'NUM DOCUMENTO', 'N° DOCUMENTO'],
        'Monto': ['Monto', 'MONTO', 'Importe', 'IMPORTE', 'VALOR'],
        'Saldo': ['Saldo', 'SALDO'],
        'Adicionales': ['Adicionales', 'ADICIONALES', 'Observaciones', 'OBSERVACIONES']
    }
    
    # Create new DataFrame with standardized columns
    df_new = pd.DataFrame()
    
    def find_column(df: pd.DataFrame, alternatives: list) -> str:
        """Find column name from list of alternatives."""
        for alt in alternatives:
            if alt in df.columns:
                return alt
        for col in df.columns:
            for alt in alternatives:
                if isinstance(col, str) and alt.lower().replace(' ', '') in col.lower().replace(' ', ''):
                    return col
        return None
    
    for new_col, alternatives in column_map.items():
        found_col = find_column(df_clean, alternatives)
        if found_col:
            data = df_clean[found_col]
            
            if new_col == 'Adicionales' and data.notna().any():
                data = data.astype(str).apply(lambda x: (
                    x.replace('\\t', '')
                     .replace('\\n', '')
                     .replace('\t', '')
                     .replace('\n', '')
                     .strip()
                ))
                data = data.replace('nan', None)
            
            df_new[new_col] = data
        else:
            df_new[new_col] = None
    
    return df_new
