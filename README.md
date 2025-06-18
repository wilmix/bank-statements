# Bank Statements Project

Base de proyecto Python para procesar archivos bancarios (ej. xlsx) en Windows.

## Estructura
- `src/`: Código fuente principal
- `tests/`: Pruebas

## Requisitos
- Python 3.8+
- Activar el entorno virtual: `source .venv/Scripts/activate` (en bash Windows)

## Primeros pasos
1. Crear entorno virtual: `python -m venv .venv`
2. Activar entorno virtual:
   - Bash: `source .venv/Scripts/activate`
   - CMD: `.venv\Scripts\activate.bat`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Ejecutar: `python -m src.main`

## Bank Identification Logic

This project identifies the bank and account number from the header or specific rows in each statement file. The logic is as follows:

| Bank   | Pattern in Header/Row         | Account Example   | Detection Logic in Code         |
|--------|------------------------------|-------------------|---------------------------------|
| BNB1   | 'Número De cuenta' 1000092297| 1000092297        | Header column == '1000092297'   |
| BNB2   | 'Número De cuenta' 1000264616| 1000264616        | Header column == '1000264616'   |
| UNION  | Row contains 'Cuenta:' + num | 10000014847393    | Row with 'Cuenta:' and number   |
| BCP    | Row with pattern XX-XXXX...  | 201-0005751-3-23  | Row with at least 2 hyphens     |

- The detection logic is implemented in the `identificar_banco_y_cuenta` function in `src/main.py`.
- Update this table if new banks or patterns are added.
