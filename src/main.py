"""
main.py - Detect bank and account number from headers, clean and enrich data.
"""
import os
import sys
import pandas as pd
from pathlib import Path

from src.detector.bank_detector import detect_bank_and_account, detect_bcp_payment_report
from src.processors.bcp_cleaner import clean_bcp
from src.processors.bnb_cleaner import clean_bnb
from src.processors.union_cleaner import clean_union
from src.workflows.bcp_workflow import process_bcp_statement_workflow, process_bcp_payment_workflow
from src.utils.file_manager import ensure_dirs, DATA_RAW, DATA_PROCESSED

# Configure pandas to show all columns
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Ensure data directories exist
ensure_dirs()

def show_summary(df: pd.DataFrame, bank: str, file_path: Path) -> None:
    """Show a complete summary of the DataFrame."""
    print(f"\nDataFrame Summary ({bank}):")
    print(f"Total rows: {len(df)}")
    print(f"Available columns:")
    print(df.columns.tolist())
    
    print("\nFirst 5 rows:")
    print(df.head().to_string())
    print("\nLast 5 rows:")
    print(df.tail().to_string())
    
    # Save clean version to CSV
    if file_path:
        clean_file = DATA_PROCESSED / f"{file_path.stem}_clean.csv"
        df.to_csv(clean_file, index=False)
        print(f"\nClean file saved to: {clean_file}")

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
    """Main entry point for the bank statement processor."""
    if len(sys.argv) < 2:
        print("Error: You must specify the file name to process")
        print("Usage: python -m src.main <file.xls>")
        print("Example: python -m src.main bcpHistoricos.xls")
        return

    file_name = sys.argv[1]
    file_path = DATA_RAW / file_name
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
        
    print(f"Processing file: {file_path}")

    # Read Excel
    df = pd.read_excel(file_path, header=0)
    
    # First check if it's a BCP payment report
    is_payment_report, account = detect_bcp_payment_report(df)
    if is_payment_report:
        # Payment report workflow
        if account:
            print(f"Account: {account}")
        df_result = process_bcp_payment_workflow(file_path, df)
        return
    
    # If not a payment report, detect bank and account
    bank, account = detect_bank_and_account(df)
    print(f"\nDetected bank: {bank}")
    print(f"Account number: {account}")
    
    # Process according to bank
    if bank == "BCP":
        # Special workflow for BCP statements
        df_clean = process_bcp_statement_workflow(file_path, df)
    else:
        # Normal workflow for other banks
        if bank in ["BNB", "BNB1", "BNB2"]:
            df_clean = clean_bnb(df)
        elif bank == "UNION":
            df_clean = clean_union(df)
        else:
            df_clean = df
        
        # Add bank column and save
        df_clean['bank'] = bank
        show_summary(df_clean, bank, file_path)

if __name__ == "__main__":
    main()
