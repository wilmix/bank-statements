"""
main.py - Detecta banco y número de cuenta desde la cabecera, convierte a CSV y muestra el head.
"""
import os
import sys
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

def find_bcp_clean_statement():
    """
    Busca el archivo de extracto BCP limpio más reciente.
    Returns:
        Path del archivo si existe, None si no.
    """
    extracto_candidates = list(DATA_PROCESSED.glob("bcpHistoricos_clean.csv"))
    if not extracto_candidates:
        return None
    return max(extracto_candidates, key=lambda p: p.stat().st_mtime)

def find_abonos_clean_report():
    """
    Busca el archivo de reporte de abonos limpio más reciente.
    Returns:
        Path del archivo si existe, None si no.
    """
    abonos_candidates = list(DATA_PROCESSED.glob("ReporteAbonos_clean.csv"))
    if not abonos_candidates:
        return None
    return max(abonos_candidates, key=lambda p: p.stat().st_mtime)

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
    """
    Limpieza específica para extractos BNB.
    - Elimina filas vacías y sin fecha
    - Limpia espacios en columnas de texto
    - Estandariza formatos de referencia y códigos
    """
    # Buscar la fila que contiene los encabezados reales
    header_row = df[df.iloc[:, 0] == 'Fecha'].index[0] if 'Fecha' in df.iloc[:, 0].values else 0
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Eliminar filas vacías y sin fecha
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean[df_clean['Fecha'].notnull()]
    
    # Limpiar espacios en columnas de texto
    columnas_texto = ['Referencia', 'Descripción', 'Código de transacción', 'Adicionales']
    for col in columnas_texto:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).apply(lambda x: 
                x.strip() if pd.notna(x) else x
            )
    
    # Limpiar referencias y códigos específicamente
    if 'Referencia' in df_clean.columns:
        df_clean['Referencia'] = df_clean['Referencia'].astype(str).apply(lambda x: 
            ' '.join(x.split()) if pd.notna(x) else x
        )
    
    if 'Código de transacción' in df_clean.columns:
        df_clean['Código de transacción'] = df_clean['Código de transacción'].astype(str).apply(lambda x: 
            x.strip().replace(' ', '') if pd.notna(x) else x
        )
    
    # Asegurar que los montos sean numéricos
    for col in ['Débitos', 'Créditos', 'Saldo', 'ITF']:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(
                df_clean[col].astype(str).str.replace(',', ''),
                errors='coerce'
            )
    
    # Invertir el orden para que los primeros movimientos estén arriba
    df_clean = df_clean.iloc[::-1].reset_index(drop=True)
    
    return df_clean

def clean_bcp(df):
    """Limpieza específica para extractos BCP."""
    # Buscar fila con 'Fecha' y 'Hora'
    header_row = None
    for i, row in df.iterrows():
        if any(isinstance(val, str) and 'Fecha' in val for val in row) and any(isinstance(val, str) and 'Hora' in val for val in row):
            header_row = i
            break
    header_row = header_row if header_row is not None else 0
        
    headers = df.iloc[header_row].values
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Eliminar filas y columnas vacías
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.dropna(axis=1, how='all')
    
    # Filtrar filas que no son movimientos reales
    if 'Fecha' in df_clean.columns and 'Glosa' in df_clean.columns:
        mask = (
            df_clean['Fecha'].notna() &
            ~df_clean['Glosa'].str.contains('SALDO AL CIERRE', na=False, case=False) &
            ~((df_clean['Usuario'].str.contains('BATCH', na=False, case=False)) & 
              (df_clean['Nro. Operación'].astype(str) == '0'))
        )
        df_clean = df_clean[mask]
    
    return df_clean.reset_index(drop=True)

def clean_union(df):
    """Limpieza específica para extractos UNION."""
    # Buscar fila con "Fecha Movimiento"
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
    
    print(f"\nFila de encabezado encontrada en índice: {header_row}")
    
    # Extraer y limpiar encabezados
    headers = []
    for val in df.iloc[header_row].values:
        if pd.isna(val) or not isinstance(val, str):
            headers.append('Unnamed')
        else:
            clean_val = val.strip().replace('\n', ' ').replace('\\n', ' ').strip()
            headers.append(clean_val)
    
    # Crear DataFrame limpio
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = headers
    
    # Eliminar filas vacías y de resumen
    df_clean = df_clean.dropna(how='all')
    df_clean = df_clean.dropna(axis=1, how='all')
    
    # Filtrar filas válidas
    mask = (
        df_clean['Fecha Movimiento'].astype(str).str.match(r'\d{2}/\d{2}/\d{4}') &
        df_clean['Descripción'].notna() &
        ~df_clean['Fecha Movimiento'].astype(str).str.contains('Total|Tránsito', na=False)
    )
    
    df_clean = df_clean[mask].copy()
    df_clean = df_clean.reset_index(drop=True)
    
    # Mapeo de columnas
    mapeo_columnas = {
        'Fecha Movimiento': ['Fecha Movimiento', 'FECHA MOVIMIENTO', 'Fecha'],
        'AG': ['AG', 'Agencia', 'AGENCIA'],
        'Descripción': ['Descripción', 'DESCRIPCIÓN', 'DESCRIPCION', 'Glosa', 'GLOSA'],
        'Nro Documento': ['Nro Documento', 'NRO DOCUMENTO', 'NUM DOCUMENTO', 'N° DOCUMENTO'],
        'Monto': ['Monto', 'MONTO', 'Importe', 'IMPORTE', 'VALOR'],
        'Saldo': ['Saldo', 'SALDO'],
        'Adicionales': ['Adicionales', 'ADICIONALES', 'Observaciones', 'OBSERVACIONES']
    }
    
    # Crear nuevo DataFrame con columnas estandarizadas
    df_nuevo = pd.DataFrame()
    
    def encontrar_columna(df, alternativas):
        for alt in alternativas:
            if alt in df.columns:
                return alt
        for col in df.columns:
            for alt in alternativas:
                if isinstance(col, str) and alt.lower().replace(' ', '') in col.lower().replace(' ', ''):
                    return col
        return None
    
    for col_nueva, alternativas in mapeo_columnas.items():
        col_encontrada = encontrar_columna(df_clean, alternativas)
        if col_encontrada:
            datos = df_clean[col_encontrada]
            
            if col_nueva == 'Adicionales' and datos.notna().any():
                datos = datos.astype(str).apply(lambda x: (
                    x.replace('\\t', '')
                     .replace('\\n', '')
                     .replace('\t', '')
                     .replace('\n', '')
                     .strip()
                ))
                datos = datos.replace('nan', None)
            
            df_nuevo[col_nueva] = datos
        else:
            df_nuevo[col_nueva] = None
    
    return df_nuevo

def identificar_reporte_abonos_bcp(df):
    """
    Identifica si el DataFrame corresponde a un reporte de abonos del BCP.
    Returns: (es_reporte_abonos: bool, numero_cuenta: str)
    """
    for i in range(min(5, len(df))):
        for val in df.iloc[i]:
            if isinstance(val, str) and "CONSULTA DE ABONOS RECIBIDOS" in val.upper():
                for j in range(i, min(i + 5, len(df))):
                    for val in df.iloc[j]:
                        if isinstance(val, str) and "Nro. Cuenta Destino:" in val:
                            cuenta = val.split(":")[-1].strip()
                            return True, cuenta
                return True, None
    return False, None

def clean_bcp_abonos(df):
    """Limpieza específica para reportes de abonos BCP."""
    print("\nIniciando limpieza de reporte de abonos...")
    
    # Buscar fila de encabezados
    header_row = None
    for i, row in df.iterrows():
        if any(isinstance(val, str) and 'FECHA' in str(val).upper() for val in row) and \
           any(isinstance(val, str) and 'MONTO ABONADO' in str(val).upper() for val in row):
            header_row = i
            break
    
    if header_row is None:
        print("No se encontró la fila de encabezados en el reporte de abonos")
        return pd.DataFrame()
    
    print(f"Fila de encabezados encontrada en índice: {header_row}")
    
    # Crear DataFrame limpio
    df_clean = df.iloc[header_row+1:].copy()
    df_clean.columns = df.iloc[header_row]
    
    # Seleccionar columnas relevantes
    columnas_requeridas = [
        'CANAL', 'FECHA', 'HORA', 'MONTO ABONADO',
        'MONTO OP.', 'MONEDA OP.', 'GLOSA', 'TITULAR'
    ]
    
    # Crear nuevo DataFrame
    df_nuevo = pd.DataFrame()
    for col in columnas_requeridas:
        if col in df_clean.columns:
            df_nuevo[col] = df_clean[col]
            print(f"Columna encontrada: {col}")
        else:
            print(f"Advertencia: No se encontró la columna {col}")
            df_nuevo[col] = None
    
    # Eliminar filas vacías
    df_nuevo = df_nuevo.dropna(how='all')
    print(f"Total filas después de eliminar vacías: {len(df_nuevo)}")
    
    # Limpiar fechas
    if 'FECHA' in df_nuevo.columns:
        print("\nProcesando fechas...")
        fechas_antes = df_nuevo['FECHA'].head()
        df_nuevo['FECHA'] = pd.to_datetime(
            df_nuevo['FECHA'],
            dayfirst=True
        ).dt.strftime('%d/%m/%Y')
        print("Ejemplo de conversión de fechas:")
        print("Antes:", fechas_antes.tolist())
        print("Después:", df_nuevo['FECHA'].head().tolist())
    
    # Limpiar montos
    if 'MONTO ABONADO' in df_nuevo.columns:
        print("\nProcesando montos...")
        montos_antes = df_nuevo['MONTO ABONADO'].head()
        df_nuevo['MONTO ABONADO'] = pd.to_numeric(
            df_nuevo['MONTO ABONADO'].astype(str).str.replace(',', ''),
            errors='coerce'
        )
        print("Ejemplo de conversión de montos:")
        print("Antes:", montos_antes.tolist())
        print("Después:", df_nuevo['MONTO ABONADO'].head().tolist())
    
    # Generar columna Adicionales
    print("\nGenerando columna Adicionales...")
    df_nuevo['Adicionales'] = df_nuevo.apply(
        lambda row: f"{row['TITULAR']} - {row['GLOSA']}" if pd.notna(row['TITULAR']) and pd.notna(row['GLOSA']) 
        else row['TITULAR'] if pd.notna(row['TITULAR']) 
        else row['GLOSA'] if pd.notna(row['GLOSA'])
        else None,
        axis=1
    )
    
    print(f"\nProceso completado. Total registros: {len(df_nuevo)}")
    return df_nuevo

def enrich_bcp_with_abonos(df_bcp, df_abonos):
    """
    Enriquece el extracto BCP con información del reporte de abonos.
    """
    print("\nIniciando proceso de enriquecimiento con abonos...")
    print(f"Registros en extracto BCP: {len(df_bcp)}")
    print(f"Registros en reporte de abonos: {len(df_abonos)}")
    
    # Crear copia para no modificar el original
    df_enriched = df_bcp.copy()
    
    # Asegurar que tenemos las columnas necesarias
    if 'Fecha' not in df_bcp.columns or 'Importe' not in df_bcp.columns:
        print("Error: El extracto BCP no tiene las columnas requeridas (Fecha, Importe)")
        return df_bcp, {'error': 'Columnas faltantes en BCP'}
    
    if 'FECHA' not in df_abonos.columns or 'MONTO ABONADO' not in df_abonos.columns:
        print("Error: El reporte de abonos no tiene las columnas requeridas (FECHA, MONTO ABONADO)")
        return df_bcp, {'error': 'Columnas faltantes en abonos'}
    
    # Inicializar estadísticas
    stats = {
        'total_bcp': len(df_bcp),
        'total_abonos': len(df_abonos),
        'matched': 0,
        'multiple_matches': 0,
        'no_match': 0
    }
    
    # Convertir importes BCP a números
    df_enriched['Importe'] = df_enriched['Importe'].astype(str).str.replace(',', '').astype(float)
    
    # Agregar columna para info de abonos si no existe
    if 'Adicionales' not in df_enriched.columns:
        df_enriched['Adicionales'] = None
    
    # Iterar sobre cada transacción BCP
    for idx, row in df_enriched.iterrows():
        # Buscar matches en abonos por fecha y monto
        matches = df_abonos[
            (df_abonos['FECHA'] == row['Fecha']) & 
            (df_abonos['MONTO ABONADO'] == abs(row['Importe']))
        ]
        
        if len(matches) == 1:
            # Match único encontrado
            adicionales = matches['Adicionales'].iloc[0]
            df_enriched.at[idx, 'Adicionales'] = adicionales
            stats['matched'] += 1
            
        elif len(matches) > 1:
            # Múltiples matches - usar todos con separador
            adicionales = ' | '.join(matches['Adicionales'].dropna().unique())
            df_enriched.at[idx, 'Adicionales'] = adicionales
            stats['multiple_matches'] += 1
            
            print(f"\nMúltiples matches encontrados para transacción del {row['Fecha']} por {row['Importe']}:")
            print(matches[['FECHA', 'MONTO ABONADO', 'Adicionales']].to_string())
        else:
            stats['no_match'] += 1
    
    # Mostrar estadísticas
    print("\nEstadísticas del proceso de matching:")
    print(f"Total transacciones BCP: {stats['total_bcp']}")
    print(f"Total registros de abonos: {stats['total_abonos']}")
    print(f"Matches únicos encontrados: {stats['matched']}")
    print(f"Casos con múltiples matches: {stats['multiple_matches']}")
    print(f"Transacciones sin match: {stats['no_match']}")
    
    return df_enriched, stats

def process_bcp_workflow(archivo, df):
    """
    Maneja el flujo completo de procesamiento de extractos BCP.
    """
    print("\nProcesando extracto BCP...")
    
    # Limpiar y guardar extracto
    df_clean = clean_bcp(df)
    df_clean['banco'] = 'BCP'
    clean_csv = DATA_PROCESSED / f"{archivo.stem}_clean.csv"
    df_clean.to_csv(clean_csv, index=False)
    print(f"\nExtracto BCP guardado en: {clean_csv}")
    
    # Buscar reporte de abonos limpio
    abonos_file = find_abonos_clean_report()
    if abonos_file:
        print(f"\nEncontrando reporte de abonos: {abonos_file}")
        df_abonos = pd.read_csv(abonos_file)
        
        # Enriquecer con abonos
        df_enriched, stats = enrich_bcp_with_abonos(df_clean, df_abonos)
        if not stats.get('error'):
            enriched_csv = DATA_PROCESSED / "bcp_final.csv"
            df_enriched.to_csv(enriched_csv, index=False)
            print(f"\nExtracto BCP enriquecido guardado en: {enriched_csv}")
    else:
        print("\nNo se encontró reporte de abonos para enriquecer.")
        print("Puede procesar un reporte de abonos después ejecutando:")
        print(f"python -m src.main ReporteAbonos.xls")
    
    return df_clean

def process_abonos_workflow(archivo, df):
    """
    Maneja el flujo completo de procesamiento de reportes de abonos.
    """
    print("\nProcesando reporte de abonos BCP...")
    
    # Verificar que existe el extracto BCP limpio
    bcp_file = find_bcp_clean_statement()
    if not bcp_file:
        print("\nError: No se encontró un extracto BCP procesado.")
        print("Primero debe procesar el extracto BCP ejecutando:")
        print("python -m src.main bcpHistoricos.xls")
        return None
    
    # Limpiar reporte de abonos
    df_abonos_clean = clean_bcp_abonos(df)
    if df_abonos_clean.empty:
        print("\nError al procesar el reporte de abonos")
        return None
    
    # Guardar reporte limpio
    abonos_csv = DATA_PROCESSED / f"{archivo.stem}_clean.csv"
    df_abonos_clean.to_csv(abonos_csv, index=False)
    print(f"\nReporte de abonos procesado y guardado en: {abonos_csv}")
    
    # Cargar extracto BCP y enriquecer
    print(f"\nUsando extracto BCP: {bcp_file}")
    df_bcp = pd.read_csv(bcp_file)
    
    df_enriched, stats = enrich_bcp_with_abonos(df_bcp, df_abonos_clean)
    if not stats.get('error'):
        enriched_csv = DATA_PROCESSED / "bcp_final.csv"
        df_enriched.to_csv(enriched_csv, index=False)
        print(f"\nExtracto BCP enriquecido guardado en: {enriched_csv}")
        return df_enriched
    
    return None

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
    if len(sys.argv) < 2:
        print("Error: Debe especificar el nombre del archivo a procesar")
        print("Uso: python -m src.main <archivo.xls>")
        print("Ejemplo: python -m src.main bcpHistoricos.xls")
        return

    nombre_archivo = sys.argv[1]
    archivo = DATA_RAW / nombre_archivo
    
    if not archivo.exists():
        print(f"No se encontró el archivo: {archivo}")
        return
        
    print(f"Procesando archivo: {archivo}")

    # Leer Excel
    df = pd.read_excel(archivo, header=0)
    
    # Primero verificar si es un reporte de abonos BCP
    es_reporte_abonos, cuenta_abonos = identificar_reporte_abonos_bcp(df)
    if es_reporte_abonos:
        # Flujo de reporte de abonos
        if cuenta_abonos:
            print(f"Cuenta: {cuenta_abonos}")
        df_result = process_abonos_workflow(archivo, df)
        return
    
    # Si no es reporte de abonos, identificar el banco
    banco, cuenta = identificar_banco_y_cuenta(df)
    print(f"\nBanco detectado: {banco}")
    print(f"Número de cuenta: {cuenta}")
    
    # Procesar según el banco
    if banco == "BCP":
        # Flujo especial para extractos BCP
        df_clean = process_bcp_workflow(archivo, df)
    else:
        # Flujo normal para otros bancos
        if banco in ["BNB", "BNB1", "BNB2"]:
            df_clean = clean_bnb(df)
        elif banco == "UNION":
            df_clean = clean_union(df)
        else:
            df_clean = df
        
        # Agregar columna banco y guardar
        df_clean['banco'] = banco
        mostrar_resumen_df(df_clean, banco, archivo)

if __name__ == "__main__":
    main()
