import os
import pandas as pd
import re
from pathlib import Path
from .config import default_categories

class BankStatement:
    def __init__(self, categories=default_categories):
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system('mkdir -p ~/code/conto/data')
        self.data_dir = Path("~/code/conto/data").expanduser()
        self.data = self.reset_table()
        self.categories = categories

    def load_excel_statement(self):
        self.data = None
        name_pattern = r'MovimentiCC_\d{4}-\d{2}-\d{2}\.xlsx'
        files = []
        for file in self.data_dir.iterdir():
            if re.match(name_pattern, file.name):
                files.append(str(file.resolve()))
        files.sort()
        if not files:
            print("No matching Excel files found.")
            return None
        df = pd.read_excel(files[0], header=None)
        return df

    def reset_table(self, flag = "Data contabile"):
        self.data = self.load_excel_statement()
        col_header_limit, row_header_limit = 10, 10
    
        headers_area = self.data.iloc[:col_header_limit, :row_header_limit]
        if flag not in headers_area.values:
            raise ValueError("Unidentifiable headers.")
        col_headers_index, row_headers_index = (
            (headers_cell := headers_area.isin([flag])).any(axis=0).idxmax(), headers_cell.any(axis=1).idxmax()
        )
        self.data.columns = self.data.iloc[row_headers_index, :].values
        self.data = self.data.iloc[
            row_headers_index + 1:,
            col_headers_index:
            ].reset_index(drop=True)
        self.data["Data valuta"] = pd.to_datetime(self.data["Data valuta"], format="%d/%m/%Y")
        self.data["Importo"] = pd.to_numeric(self.data["Importo"].astype(str).str.replace(',', '.'), errors='coerce')
        return self.data

    def categorize_expenses(self, col_name='Descrizione'):
        if col_name not in self.data.columns:
            raise ValueError(f"'{col_name}' column not found in data.")
    
        def categorize_row(description):
            for category, keywords in self.categories.items():
                if any(keyword.lower() in str(description).lower() for keyword in keywords):
                    return category
            return 'Uncategorized'
        
        self.data['Categoria'] = self.data['Descrizione'].apply(categorize_row)
        return self.data
