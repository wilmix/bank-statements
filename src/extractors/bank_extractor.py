"""
Extractor base para leer archivos de extractos bancarios.
"""
import os
import pandas as pd
from src.utils.converter import convert_excel_to_csv


class BankExtractor:
    """
    Clase base para extraer datos de archivos bancarios.
    """
    
    def __init__(self, file_path, bank_type):
        """
        Inicializa el extractor.
        
        Args:
            file_path (str): Ruta al archivo bancario.
            bank_type (str): Tipo de banco ('bnb', 'bcph', etc.)
        """
        self.file_path = file_path
        self.bank_type = bank_type
        self.csv_path = None
        
    def extract(self):
        """
        Extrae los datos del archivo bancario.
        
        Returns:
            pandas.DataFrame: Los datos extraídos.
        """
        # Convertir a CSV si es un archivo Excel
        if self.file_path.lower().endswith(('.xls', '.xlsx')):
            self.csv_path = convert_excel_to_csv(self.file_path)
            df = pd.read_csv(self.csv_path)
        elif self.file_path.lower().endswith('.csv'):
            self.csv_path = self.file_path
            df = pd.read_csv(self.csv_path)
        else:
            raise ValueError(f"Formato de archivo no soportado: {self.file_path}")
        
        return df
    
    def get_csv_path(self):
        """
        Obtiene la ruta al archivo CSV.
        
        Returns:
            str: Ruta al archivo CSV.
        """
        return self.csv_path
