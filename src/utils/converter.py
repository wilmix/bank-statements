"""
Utilidades para convertir archivos XLS/XLSX a CSV.
"""
import os
import pandas as pd


def convert_excel_to_csv(input_path, output_path=None, sheet_name=0):
    """
    Convierte un archivo Excel (XLS/XLSX) a CSV.
    
    Args:
        input_path (str): Ruta al archivo Excel a convertir.
        output_path (str, optional): Ruta donde guardar el CSV. Si no se proporciona,
                                    usa el mismo nombre que el archivo de entrada pero con extensión .csv.
        sheet_name (int/str, optional): Índice u nombre de la hoja a convertir. Por defecto, la primera hoja.
    
    Returns:
        str: La ruta al archivo CSV generado.
        
    Raises:
        FileNotFoundError: Si el archivo Excel no existe.
        Exception: Para otros errores durante la conversión.
    """
    try:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"El archivo {input_path} no existe")
        
        # Generar la ruta de salida si no se proporciona
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'processed')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{base_name}.csv")
        
        # Leer el archivo Excel
        df = pd.read_excel(input_path, sheet_name=sheet_name)
        
        # Guardar como CSV
        df.to_csv(output_path, index=False)
        
        print(f"Archivo convertido exitosamente: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error al convertir {input_path} a CSV: {str(e)}")
        raise
