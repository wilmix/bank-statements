"""
Funciones para limpiar y normalizar los datos bancarios.
"""
import pandas as pd


def clean_bank_statement(df, bank_type):
    """
    Limpia y normaliza un dataframe de extracto bancario según el tipo de banco.
    
    Args:
        df (pandas.DataFrame): El dataframe a limpiar.
        bank_type (str): Tipo de banco ('bnb', 'bcph', etc.)
    
    Returns:
        pandas.DataFrame: Dataframe limpio y normalizado.
    """
    if bank_type.lower() == 'bnb':
        return _clean_bnb_statement(df)
    elif bank_type.lower() == 'bcph':
        return _clean_bcph_statement(df)
    else:
        print(f"Tipo de banco '{bank_type}' no implementado. Devolviendo datos originales.")
        return df
    

def _clean_bnb_statement(df):
    """
    Limpia específicamente los extractos del BNB.
    
    Args:
        df (pandas.DataFrame): Dataframe con datos del BNB.
    
    Returns:
        pandas.DataFrame: Dataframe limpio.
    """
    # Encontrar la fila que contiene los encabezados reales (usualmente es la primera fila)
    header_row = df[df.iloc[:, 0] == 'Fecha'].index[0] if 'Fecha' in df.iloc[:, 0].values else 0
    
    # Usar esa fila como encabezado y descartar filas anteriores
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Eliminar filas con valores nulos en columnas clave
    df_clean = df_clean.dropna(subset=['Fecha', 'Descripción'])
    
    # Convertir columnas numéricas
    numeric_cols = ['Débitos', 'Créditos', 'Saldo']
    for col in numeric_cols:
        if col in df_clean.columns:
            # Manejar valores como '1,234.56'
            df_clean[col] = df_clean[col].astype(str).str.replace(',', '').astype(float)
            
    # Convertir fecha a formato estándar
    if 'Fecha' in df_clean.columns:
        df_clean['Fecha'] = pd.to_datetime(df_clean['Fecha'], dayfirst=True, errors='coerce')
    
    return df_clean


def _clean_bcph_statement(df):
    """
    Limpia específicamente los extractos del BCPH.
    
    Args:
        df (pandas.DataFrame): Dataframe con datos del BCPH.
    
    Returns:
        pandas.DataFrame: Dataframe limpio.
    """
    # Implementación específica para BCPH
    # Este es un placeholder - necesita implementarse según el formato específico de BCPH
    
    # Buscar las posiciones donde comienzan los datos relevantes
    # Por ejemplo, buscar filas que contengan 'FECHA' o 'TRANSACCIÓN'
    
    # Por ahora, devolvemos el dataframe original con una nota
    print("Limpieza de datos BCPH aún no implementada específicamente")
    return df
