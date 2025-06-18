"""
main.py - Detecta banco y número de cuenta desde la cabecera, convierte a CSV y muestra el head.
"""
import os
import pandas as pd
from pathlib import Path

# Configurar pandas para mostrar todas las columnas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Definir rutas
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Cambia aquí el nombre del archivo a procesar (debe estar en data/raw)
ARCHIVO_A_PROCESAR = "bcpHistoricos.xls"  # Ejemplo: "union.xls", "bcph.xls", "bnb2.xls"


# Cuentas BNB:
#   'Número De cuenta' 1000092297  -> BNB1
#   'Número De cuenta' 1000264616  -> BNB2
# Cuentas UNION:
#   'Cuenta:' 10000014847393 -> UNION
# Cuentas BCP:
#   '201-0005751-3-23' -> BCP


def identificar_banco_y_cuenta(df):
    # BNB: 'Número De cuenta' y el número en la cabecera
    if 'Número De cuenta' in df.columns:
        for col in df.columns:
            if str(col) == '1000092297':
                return 'BNB1', col
            if str(col) == '1000264616':
                return 'BNB2', col
            if str(col).startswith('10000'):
                return 'BNB', col
    # UNION: buscar fila con 'Cuenta:' y número
    for i, row in df.iterrows():
        for val in row:
            if isinstance(val, str) and 'Cuenta:' in val:
                # Buscar el número de cuenta en la misma fila
                for v in row:
                    if isinstance(v, (str, int)) and str(v).strip().isdigit() and len(str(v).strip()) > 8:
                        return 'UNION', str(v).strip()
    # BCP: buscar patrón de cuenta BCP (ejemplo: 201-0005751-3-23)
    for i, row in df.iterrows():
        for val in row:
            if isinstance(val, str) and '-' in val and val.count('-') >= 2:
                return 'BCP', val.strip()
    return 'Desconocido', 'No encontrado'


def clean_bnb(df):
    """Limpieza específica para extractos BNB."""
    # Buscar la fila que contiene los encabezados reales (usualmente la primera fila)
    header_row = df[df.iloc[:, 0] == 'Fecha'].index[0] if 'Fecha' in df.iloc[:, 0].values else 0
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    # Eliminar filas vacías
    df_clean = df_clean.dropna(how='all')
    # Eliminar filas sin fecha
    df_clean = df_clean[df_clean['Fecha'].notnull()]
    # Invertir el orden para que los primeros movimientos estén arriba
    df_clean = df_clean.iloc[::-1].reset_index(drop=True)
    return df_clean


def clean_bcp(df):
    """Limpieza específica para extractos BCP."""
    # Buscar fila con 'Fecha' y 'Hora' en alguna columna
    header_row = None
    for i, row in df.iterrows():
        if any(isinstance(val, str) and 'Fecha' in val for val in row) and any(isinstance(val, str) and 'Hora' in val for val in row):
            header_row = i
            break
    if header_row is None:
        header_row = 0
        
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Eliminar filas y columnas completamente vacías
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.dropna(axis=1, how='all')
    
    # Filtrar filas que no son movimientos reales
    if 'Fecha' in df_clean.columns and 'Glosa' in df_clean.columns:
        mask = (
            # Debe tener fecha
            df_clean['Fecha'].notna() &
            # No debe ser SALDO AL CIERRE
            ~df_clean['Glosa'].str.contains('SALDO AL CIERRE', na=False, case=False) &
            # No debe tener BATCH como usuario y 0 como número de operación
            ~((df_clean['Usuario'].str.contains('BATCH', na=False, case=False)) & 
              (df_clean['Nro. Operación'].astype(str) == '0'))
        )
        df_clean = df_clean[mask]
    
    # Resetear el índice
    df_clean = df_clean.reset_index(drop=True)
    
    return df_clean


def clean_union(df):
    """Limpieza específica para extractos UNION."""
    # Buscar fila que contiene "Fecha Movimiento" exactamente
    header_row = None
    for i, row in df.iterrows():
        if 'Fecha Movimiento' in row.values:
            header_row = i
            break
    if header_row is None:
        # Si no encontramos el header exacto, buscar la última fila de encabezado
        # que contenga "Fecha" antes de los datos
        for i, row in df.iterrows():
            if any(isinstance(val, str) and 'Fecha' in val for val in row):
                header_row = i
    if header_row is None:
        header_row = 0
    
    print(f"\nFila de encabezado encontrada en índice: {header_row}")
    
    # Extraer los encabezados y limpiarlos de caracteres especiales y espacios
    headers = []
    for val in df.iloc[header_row].values:
        if pd.isna(val) or not isinstance(val, str):
            headers.append('Unnamed')
        else:
            # Limpiar el valor del header
            clean_val = val.strip().replace('\n', ' ').replace('\\n', ' ').strip()
            headers.append(clean_val)
    
    # Crear el DataFrame limpio con los datos después del encabezado
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers    # Eliminar filas completamente vacías y filas de resumen
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.dropna(axis=1, how='all')  # También eliminar columnas vacías    # Primero, vamos a crear una máscara para filas válidas
    mask = (
        # La fecha debe ser una cadena con formato dd/mm/yyyy
        df_clean['Fecha Movimiento'].astype(str).str.match(r'\d{2}/\d{2}/\d{4}') &
        # La descripción no debe estar vacía
        df_clean['Descripción'].notna() &
        # No debe ser una fila de totales o tránsito
        ~df_clean['Fecha Movimiento'].astype(str).str.contains('Total|Tránsito', na=False)
    )
    
    # Aplicar la máscara
    df_clean = df_clean[mask].copy()
    
    # Resetear el índice
    df_clean = df_clean.reset_index(drop=True)
    
    print(f"\nTotal filas después de limpieza: {len(df_clean)}")
    if len(df_clean) > 0:
        print("\nPrimera fila:", df_clean.iloc[0]['Fecha Movimiento'])
        print("Última fila:", df_clean.iloc[-1]['Fecha Movimiento'])
    
    # Mapeo de columnas incluyendo variaciones en nombres
    mapeo_columnas = {
        'Fecha Movimiento': ['Fecha Movimiento', 'FECHA MOVIMIENTO', 'Fecha'],
        'AG': ['AG', 'Agencia', 'AGENCIA'],
        'Descripción': ['Descripción', 'DESCRIPCIÓN', 'DESCRIPCION', 'Glosa', 'GLOSA'],
        'Nro Documento': ['Nro Documento', 'NRO DOCUMENTO', 'NUM DOCUMENTO', 'N° DOCUMENTO'],
        'Monto': ['Monto', 'MONTO', 'Importe', 'IMPORTE', 'VALOR', 'Monto\n', 'MONTO\n'],
        'Saldo': ['Saldo', 'SALDO'],
        'Adicionales': ['Adicionales', 'ADICIONALES', 'Observaciones', 'OBSERVACIONES']
    }
    
    print("\nColumnas antes de mapeo:")
    print(df_clean.columns.tolist())
    
    # Crear nuevo DataFrame con columnas estandarizadas
    df_nuevo = pd.DataFrame()
    
    # Función para encontrar una columna por sus variantes o por coincidencia parcial
    def encontrar_columna(df, alternativas):
        # Primero buscar coincidencia exacta
        for alt in alternativas:
            if alt in df.columns:
                return alt
        # Luego buscar coincidencia parcial
        for col in df.columns:
            for alt in alternativas:
                if isinstance(col, str) and alt.lower().replace(' ', '') in col.lower().replace(' ', ''):
                    return col
        return None
      # Para cada columna deseada, buscar en el DataFrame original
    for col_nueva, alternativas in mapeo_columnas.items():
        col_encontrada = encontrar_columna(df_clean, alternativas)
        if col_encontrada:
            # Obtener los datos de la columna
            datos = df_clean[col_encontrada]
            
            # Si es la columna Adicionales, limpiar caracteres especiales
            if col_nueva == 'Adicionales' and datos.notna().any():
                datos = datos.astype(str).apply(lambda x: (
                    x.replace('\\t', '')  # Eliminar tabulaciones
                     .replace('\\n', '')  # Eliminar saltos de línea
                     .replace('\t', '')   # Eliminar tabulaciones reales
                     .replace('\n', '')   # Eliminar saltos de línea reales
                     .strip()             # Eliminar espacios al inicio y final
                ))
                # Reemplazar 'nan' por None
                datos = datos.replace('nan', None)
            
            df_nuevo[col_nueva] = datos
            print(f"Columna {col_nueva} mapeada desde: {col_encontrada}")
        else:
            df_nuevo[col_nueva] = None
            print(f"Advertencia: No se encontró la columna {col_nueva}")
    
    # Reset del índice para que empiece en 0
    df_nuevo = df_nuevo.reset_index(drop=True)
    
    return df_nuevo


def mostrar_resumen_df(df, banco, archivo):
    """Muestra un resumen completo del DataFrame."""
    print(f"\nResumen del DataFrame ({banco}):")
    print(f"Total filas: {len(df)}")
    print(f"Columnas disponibles:")
    print(df.columns.tolist())
    
    print("\nPrimeras 5 filas:")
    print(df.head().to_string())
    print("\nÚltimas 5 filas:")
    print(df.tail().to_string())
    
    # Guardar versión limpia en CSV
    if archivo:
        review_file = DATA_PROCESSED / f"{archivo.stem}_clean.csv"
        df.to_csv(review_file, index=False)
        print(f"\nArchivo limpio guardado en: {review_file}")

def main():
    archivo = DATA_RAW / ARCHIVO_A_PROCESAR
    if not archivo.exists():
        print(f"No se encontró {archivo}")
        return
    print(f"Procesando archivo: {archivo}")

    # Leer Excel y convertir a CSV
    df = pd.read_excel(archivo, header=0)
    csv_path = DATA_PROCESSED / (archivo.stem + ".csv")
    df.to_csv(csv_path, index=False)
    print(f"Archivo convertido a CSV: {csv_path}")

    # Identificar banco y cuenta
    banco, cuenta = identificar_banco_y_cuenta(df)
    print(f"Banco detectado: {banco}")
    print(f"Número de cuenta: {cuenta}")

    # Limpiar según banco y mostrar resumen
    if banco in ["BNB", "BNB1", "BNB2"]:
        df_clean = clean_bnb(df)
    elif banco == "BCP":
        df_clean = clean_bcp(df)
    elif banco == "UNION":
        df_clean = clean_union(df)
    else:
        df_clean = df
    
    # Agregar columna banco y mostrar resumen
    df_clean['banco'] = banco
    mostrar_resumen_df(df_clean, banco, archivo)

if __name__ == "__main__":
    main()
