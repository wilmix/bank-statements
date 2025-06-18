"""
BCP specific workflows for processing bank statements and payment reports.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple
from src.processors.bcp_cleaner import clean_bcp
from src.processors.bcp_payment_cleaner import clean_bcp_payments
from src.enricher.bcp_enricher import BCPEnricher
from src.utils.file_manager import find_bcp_clean_statement, find_payment_report

# Project paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"

def process_bcp_statement_workflow(file_path: Path, df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles the complete workflow for processing BCP bank statements.
    
    Args:
        file_path (Path): Path to the BCP statement Excel file
        df (pd.DataFrame): Raw DataFrame from the Excel file
        
    Returns:
        pd.DataFrame: The cleaned and enriched DataFrame
    """
    print("\nProcessing BCP bank statement...")
    
    # Clean and save statement
    df_clean = clean_bcp(df)
    df_clean['bank'] = 'BCP'
    clean_csv = DATA_PROCESSED / f"{file_path.stem}_clean.csv"
    df_clean.to_csv(clean_csv, index=False)
    print(f"\nBCP statement saved to: {clean_csv}")
    
    # Look for payment report
    payment_file = find_payment_report()
    if payment_file:
        print(f"\nFound payment report: {payment_file}")
        df_payments = pd.read_csv(payment_file)
          # Enrich with payment info
        enricher = BCPEnricher()
        df_enriched, stats = enricher.enrich_statement(df_clean, df_payments)
        if not stats.get('error'):
            enriched_csv = DATA_PROCESSED / "bcp_final.csv"
            df_enriched.to_csv(enriched_csv, index=False)
            print(f"\nEnriched BCP statement saved to: {enriched_csv}")
    else:
        print("\nNo payment report found for enrichment.")
        print("You can process a payment report later by running:")
        print(f"python -m src.main ReporteAbonos.xls")
    
    return df_clean

def process_bcp_payment_workflow(file_path: Path, df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Handles the complete workflow for processing BCP payment reports.
    
    Args:
        file_path (Path): Path to the payment report Excel file
        df (pd.DataFrame): Raw DataFrame from the Excel file
        
    Returns:
        pd.DataFrame | None: The enriched DataFrame or None if processing failed
    """
    print("\nProcessing BCP payment report...")
    
    # Check for existing BCP statement
    bcp_file = find_bcp_clean_statement()
    if not bcp_file:
        print("\nError: No processed BCP statement found.")
        print("Please process the BCP statement first by running:")
        print("python -m src.main bcpHistoricos.xls")
        return None
    
    # Clean payment report
    df_payments_clean = clean_bcp_payments(df)
    if df_payments_clean.empty:
        print("\nError processing payment report")
        return None
    
    # Save cleaned report
    payments_csv = DATA_PROCESSED / f"{file_path.stem}_clean.csv"
    df_payments_clean.to_csv(payments_csv, index=False)
    print(f"\nProcessed payment report saved to: {payments_csv}")
      # Load BCP statement and enrich
    print(f"\nUsing BCP statement: {bcp_file}")
    df_bcp = pd.read_csv(bcp_file)
    enricher = BCPEnricher()
    df_enriched, stats = enricher.enrich_statement(df_bcp, df_payments_clean)
    if not stats.get('error'):
        enriched_csv = DATA_PROCESSED / "bcp_final.csv"
        df_enriched.to_csv(enriched_csv, index=False)
        print(f"\nEnriched BCP statement saved to: {enriched_csv}")
        return df_enriched
    
    return None
