"""
main.py - Detecta banco y número de cuenta desde la cabecera, convierte a CSV y muestra el head.
"""
import os
import pandas as pd
from pathlib import Path

# Definir rutas
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Cambia aquí el nombre del archivo a procesar (debe estar en data/raw)
ARCHIVO_A_PROCESAR = "bcph.xls"  # Ejemplo: "union.xls", "bcph.xls", "bnb2.xls"


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

    # Mostrar el head
    print("\nHead del DataFrame:")
    print(df.head())

if __name__ == "__main__":
    main()
