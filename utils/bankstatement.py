import os
import pandas as pd
import re
from pathlib import Path
import json
with open(Path("~/code/conto/utils/config.json").expanduser(), 'r') as f:
    config = json.load(f)

class BankStatement:
    def __init__(self, owner="papà", categories=None):
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system('mkdir -p ~/code/conto/data')
        self.data_dir = Path("~/code/conto/data").expanduser()
        self.headers = config[owner]["headers"]
        self.data = self.reset_table()
        self.categories = categories if categories else config[owner]["default_categories"]

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

    def reset_table(self):
        self.data = self.load_excel_statement()
        flag = self.headers["loc_identif"]
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
        self.data[self.headers["date"]] = pd.to_datetime(self.data[self.headers["date"]], format="%d/%m/%Y")
        self.data[self.headers["value"]] = pd.to_numeric(self.data[self.headers["value"]].astype(str).str.replace(',', '.'), errors='coerce')
        return self.data

    def categorize_expenses(self):
        description_col = self.headers.get("descript", "Descrizione")
        category_col = self.headers.get("category", "Categoria")
        if description_col not in self.data.columns:
            raise ValueError(f"'{description_col}' column not found in data.")
    
        def categorize_row(description):
            for category, keywords in self.categories.items():
                if any(keyword.lower() in str(description).lower() for keyword in keywords):
                    return category
            return 'Uncategorized'
        
        self.data[category_col] = self.data[description_col].apply(categorize_row)
        return self.data
