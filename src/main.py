"""
main.py - Entry point clásico para el procesamiento de archivos bancarios.
"""
import sys
import os
import pandas as pd
import argparse
from pathlib import Path
from src.extractors.bank_extractor import BankExtractor
from src.processors.cleaner import clean_bank_statement

# Definir rutas para datos crudos y procesados
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Asegurar que los directorios existan
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Rutas de archivos para procesar
EXCEL_FILES = [
    r"G:\My Drive\Extractos Bancarios\EXTRACTOS BANCARIOS 2025\05\back\bnb1.xls",
    r"G:\My Drive\Extractos Bancarios\EXTRACTOS BANCARIOS 2025\05\back\bnb2.xls",
    r"G:\My Drive\Extractos Bancarios\EXTRACTOS BANCARIOS 2025\05\back\bcph.xls",
]

def process_bank_file(file_path):
    """
    Procesa un archivo bancario: lo convierte a CSV, limpia y devuelve los datos.
    
    Args:
        file_path (str): Ruta al archivo bancario.
        
    Returns:
        tuple: (pandas.DataFrame con datos limpios, ruta al CSV)
    """
    try:
        # Determinar tipo de banco por el nombre del archivo
        bank_type = 'bnb' if 'bnb' in os.path.basename(file_path).lower() else 'bcph'
        
        print(f"\nProcesando archivo: {os.path.basename(file_path)} (Tipo: {bank_type})")
        
        # Extraer datos
        extractor = BankExtractor(file_path, bank_type)
        df = extractor.extract()
        
        print(f"Datos extraídos correctamente a CSV: {extractor.get_csv_path()}")
        print(f"Forma del DataFrame: {df.shape}")
        
        # Limpiar datos
        df_clean = clean_bank_statement(df, bank_type)
        print(f"Datos limpiados correctamente. Forma final: {df_clean.shape}")
        
        # Mostrar una muestra
        print("Muestra de datos limpios:")
        print(df_clean.head(3))
        
        # Guardar versión limpia
        clean_csv_path = extractor.get_csv_path().replace('.csv', '_clean.csv')
        df_clean.to_csv(clean_csv_path, index=False)
        print(f"Datos limpios guardados en: {clean_csv_path}")
        
        return df_clean, extractor.get_csv_path()
    
    except Exception as e:
        print(f"Error procesando {file_path}: {str(e)}")
        return None, None

def main():
    """
    Punto de entrada principal para procesar archivos bancarios.
    """
    parser = argparse.ArgumentParser(description='Procesador de extractos bancarios')
    parser.add_argument('--archivo', type=str, help='Ruta a un archivo específico para procesar')
    args = parser.parse_args()
    
    if args.archivo:
        # Procesar solo el archivo especificado
        process_bank_file(args.archivo)
    else:
        # Procesar todos los archivos configurados
        print(f"Procesando {len(EXCEL_FILES)} archivos configurados...")
        for archivo in EXCEL_FILES:
            process_bank_file(archivo)
    
    print("\nProcesamiento completado.")

if __name__ == "__main__":
    main()
