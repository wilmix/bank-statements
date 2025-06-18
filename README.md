# Bank Statements Project

Python project for processing and enriching bank statement data from Excel files. Currently supports BCP, BNB, and UNION banks.

## Project Overview
- Automatic bank and account detection from file content
- Bank-specific cleaning and standardization
- Special BCP workflow with payment details enrichment
- Clean CSV output for further processing

## Current Structure
```
src/
├── main.py           # Current main logic (to be refactored)
├── extractors/       # Bank statement data extraction
├── processors/       # Data cleaning and processing
└── utils/           # Common utilities
data/
├── raw/             # Original bank files (.xls/.xlsx)
└── processed/       # Cleaned and enriched CSVs
tests/               # Test files
```

## Requirements
- Python 3.8+
- pandas, openpyxl for Excel processing
- Virtual environment recommended

## Setup
1. Create virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate environment:
   ```bash
   # Windows (Git Bash)
   source .venv/Scripts/activate
   # Windows (CMD)
   .venv\Scripts\activate.bat
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Statement Processing
Process any bank statement:
```bash
python -m src.main <statement.xls>
```

### BCP Enrichment Workflow
1. First process BCP statement:
   ```bash
   python -m src.main bcpHistoricos.xls
   ```
   Creates: `data/processed/bcpHistoricos_clean.csv`

2. Then process payment details:
   ```bash
   python -m src.main ReporteAbonos.xls
   ```
   Creates: `data/processed/bcp_final.csv`

## Bank Detection Logic

The project automatically identifies banks from statement content:

| Bank   | Detection Pattern            | Example Account    |
|--------|----------------------------|-------------------|
| BNB1   | Column = '1000092297'     | 1000092297       |
| BNB2   | Column = '1000264616'     | 1000264616       |
| UNION  | Row with 'Cuenta:'        | 10000014847393   |
| BCP    | Pattern: XX-XXXX-X-XX     | 201-0005751-3-23 |

## Data Cleaning

### Common Cleaning
- Remove empty rows and columns
- Standardize date formats
- Clean special characters
- Reset index for consistency

### Bank-Specific Cleaning

#### BCP
- Detect headers with 'Fecha' and 'Hora'
- Remove informational rows (SALDO AL CIERRE, BATCH operations)
- Prepare for potential enrichment with payment details

#### UNION
- Find 'Fecha Movimiento' header
- Standardize column names
- Clean 'Adicionales' column
- Remove summary rows

#### BNB
- Find 'Fecha' column
- Remove rows without dates
- Reverse order for chronological display

## BCP Enrichment Process

### Input Files
- Bank statement (`bcpHistoricos.xls`)
- Payment details (`ReporteAbonos.xls`)

### Matching Logic
Records are matched on:
- Exact date match
- Exact amount match

### Enrichment Results
- Matches are logged with statistics
- Multiple matches are reported
- Unmatched transactions are preserved
- Final enriched statement in `bcp_final.csv`

## Planned Improvements
1. Modular Refactoring:
   ```
   src/
   ├── main.py         # Entry point only
   ├── reader.py       # Excel reading
   ├── detector.py     # Bank detection
   ├── cleaner/        # Bank-specific cleaning
   ├── enricher/       # BCP enrichment
   └── utils/          # Common tools
   ```

2. Code Quality:
   - Move to English function names
   - Add proper error handling
   - Improve logging
   - Add unit tests

3. Features:
   - Support more banks
   - Add data validation
   - Improve matching accuracy
   - Add summary reports
