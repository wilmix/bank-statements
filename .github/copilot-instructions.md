<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Bank Statements Processor

This Python project processes bank statements from Excel files, with special focus on BCP bank enrichment workflows. The project aims for clean, modular code following Python best practices.

## Project Context
- Processes `.xls/.xlsx` bank statements from Windows paths
- Supports multiple banks (BCP, BNB, UNION)
- Special workflow for enriching BCP statements with payment details
- Outputs standardized CSVs for further processing

## Key Workflows
1. Basic Bank Statement Processing:
   - Detect bank from content
   - Clean according to bank format
   - Export clean CSV

2. BCP Enrichment Workflow:
   - Process BCP statement first
   - Process payment details file
   - Match by date and amount
   - Enrich with payment information

## Code Guidelines

### General Principles
- Use English for all code (variables, functions, comments)
- Follow PEP 8 style guide
- Keep functions focused (single responsibility)
- Add docstrings to all public functions
- Use type hints where helpful

### Naming Conventions
```python
# Function names (snake_case)
def process_bank_statement():
def clean_bcp_data():
def enrich_with_payments():

# Variables (clear, descriptive)
bank_name = "BCP"
account_number = "201-0005751-3-23"
payment_details = pd.DataFrame()
```

### Error Handling
```python
# Proper error handling
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    raise
except Exception as e:
    logger.error(f"Error processing file: {str(e)}")
    raise
```

### Path Handling
```python
# Use pathlib for paths
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
```

### Data Processing
```python
# Clear data transformations
def clean_statement(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize bank statement data."""
    # Remove empty rows
    df = df.dropna(how='all')
    
    # Standardize dates
    df['date'] = pd.to_datetime(df['date'])
    
    return df
```

## Current Focus
- Modular code organization
- Clean data processing workflows
- Proper error handling
- Clear logging and feedback
- Consistent file handling

## Future Improvements
- Complete modular structure
- Enhanced error handling
- Better logging system
- Unit test coverage
- Data validation rules

