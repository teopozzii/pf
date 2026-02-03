import os
import sys
import pandas as pd
import re
from pathlib import Path
import logging
import json

from utils.paths import resource_path

with open(Path(resource_path("utils/config.json")), 'r') as f:
    config = json.load(f)

logger = logging.getLogger(__name__)

class BankStatement:
    def __init__(self, owner="papà", categories=None):
        base_dir = Path.home() / ".bankstatementapp"
        if sys.platform == "win32":
            base_dir = Path(os.getenv('APPDATA')) / "BankStatementApp"
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.owner = owner
        self.headers = config[owner]["headers"]
        self.data = None
        self.categories = categories if categories else config[owner]["default_categories"]
        self._update_logger("BankStatement initialized.")

    def _update_logger(self, message):
        logger.info(message)

    def load_last_available_statement(self):
        name_pattern = r'categorized_\d{8}_\d{6}_' + config[self.owner]["sourcedoc_namepattern"] + r'\.xlsx'
        files = []
        for file in self.data_dir.iterdir():
            if re.match(name_pattern, file.name):
                files.append(str(file.resolve()))
        files.sort(reverse=True)
        if not files:
            print("No matching Excel files found.")
            return None
        # Remove files older than the past 3 ones
        for old_file in files[3:]:
            try:
                os.remove(old_file)
                logger.info(f"Removed old file: {old_file}")
            except Exception as e:
                logger.warning(f"Failed to remove old file {old_file}: {e}")
        df = pd.read_excel(files[0])
        time_of_saving = files[0].split('_')[1] + " " + files[0].split('_')[2]
        self._update_logger(f"Loaded last available statement from {files[0]} saved at {time_of_saving}.")
        return {
            "data" : df,
            "time_saved" : time_of_saving
        }

    def process_statement(self, data=None):
        if data is not None:
            self.data = data
        elif self.data is None: return None
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
    
    def write_data(self, filename="categorized_statement.xlsx"):
        output_path = self.data_dir / filename
        self.data.to_excel(output_path, index=False)
        self._update_logger(f"{self.__class__.__name__} data written to {output_path}")
