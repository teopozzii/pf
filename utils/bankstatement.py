import os
import sys
import pandas as pd
import re
import json
import hashlib
from pathlib import Path
import logging
from typing import Optional, Dict, List, Any, Any
from utils.config import CONFIG

logger = logging.getLogger(__name__)

class BankStatement:
    def __init__(self, owner: str = "papà", categories: Optional[Dict[str, List[str]]] = None):
        base_dir = Path.home() / ".bankstatementapp"
        if sys.platform == "win32":
            base_dir = Path(os.getenv('APPDATA')) / "BankStatementApp"
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.owner: str = owner
        self.headers: Dict[str, str] = CONFIG[owner]["headers"]
        self.data: Optional[pd.DataFrame] = None
        self.user_categories_path = self.data_dir / f"{owner}_categories.json"
        
        # Load and merge categories (defaults + learned)
        self.merged_categories: Dict[str, List[str]] = self._load_and_merge_categories()
        
        # For backward compatibility
        self.categories: Dict[str, List[str]] = self.merged_categories
        
        self._update_logger("BankStatement initialized.")

    def _update_logger(self, message: str) -> None:
        logger.info(message)

    def load_last_available_statement(self) -> Dict[str, Any]:
        name_pattern = r'categorized_\d{8}_\d{6}_' + CONFIG[self.owner]["sourcedoc_namepattern"] + r'\.xlsx'
        files = []
        for file in self.data_dir.iterdir():
            if re.match(name_pattern, file.name):
                files.append(str(file.resolve()))
        files.sort(reverse=True)
        if not files:
            self._update_logger("No matching Excel files found.")
            return {"data" : None, "time_saved" : None}
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

    def process_statement(self, data: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
        if data is not None:
            self.data = data
        elif self.data is None: return None
        flag = self.headers["loc_identif"]
        col_header_limit, row_header_limit = 30, 30
    
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

    def categorize_expenses(self) -> pd.DataFrame:
        description_col = self.headers.get("descript", "Descrizione")
        detail_col = self.headers.get("detail", "Dettaglio")
        category_col = self.headers.get("category", "Categoria")
        if description_col not in self.data.columns:
            raise ValueError(f"'{description_col}' column not found in data.")
    
        def categorize_row(row):
            # Concatenate Description and Detail (handling nulls gracefully)
            description = str(row.get(description_col, "")).strip() if pd.notna(row.get(description_col)) else ""
            detail = str(row.get(detail_col, "")).strip() if pd.notna(row.get(detail_col)) else ""
            combined_text = f"{description} {detail}".strip()
            
            # Match against concatenated text
            for category, keywords in self.merged_categories.items():
                if any(keyword.lower() in combined_text.lower() for keyword in keywords):
                    return category
            return 'Uncategorized'
        
        self.data[category_col] = self.data.apply(categorize_row, axis=1)
        return self.data
    
    def write_data(self, df: Optional[pd.DataFrame] = None, filename: str = "categorized_statement.xlsx") -> None:
        """Write DataFrame to Excel. If df is None, uses self.data"""
        output_path = self.data_dir / filename
        data_to_write = df if df is not None else self.data
        data_to_write.to_excel(output_path, index=False)
        self._update_logger(f"{self.__class__.__name__} data written to {output_path}")
    
    def _load_and_merge_categories(self) -> Dict[str, List[str]]:
        """Load user_categories.json and merge learned keywords with defaults"""
        if self.user_categories_path.exists():
            user_cats = json.load(open(self.user_categories_path))
            merged = user_cats.get("default_categories", {}).copy()
            
            # Merge learned keywords into existing categories
            for category, keywords in user_cats.get("learned_categories", {}).items():
                if category in merged:
                    merged[category].extend(keywords)
                else:
                    merged[category] = keywords
            return merged
        else:
            # Fallback: Load from default_categories.json for first-time users
            try:
                from utils.paths import resource_path
                defaults_path = resource_path("utils/default_categories.json")
                defaults_data = json.load(open(defaults_path))
                # In default_categories.json, categories are stored directly under user name
                user_defaults = defaults_data.get(self.owner, {})
                return user_defaults
            except Exception as e:
                logger.warning(f"Could not load default categories: {e}")
                return {}
    
    def _load_user_categories_file(self) -> Dict:
        """Load user_categories.json or return empty structure"""
        if self.user_categories_path.exists():
            return json.load(open(self.user_categories_path))
        return {"default_categories": {}, "learned_categories": {}, "last_categorized_files": {}}
    
    def _write_user_categories_file(self, data: Dict) -> None:
        """Write categories data to user_categories.json"""
        self.user_categories_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _initialize_user_categories_from_config(self) -> None:
        """Initialize user_categories.json from config.json defaults (one-time migration)"""
        if not self.user_categories_path.exists():
            # This would be called on first categorization save
            # For now, we'll handle it when saving learned categories
            pass
    
    def save_learned_category(self, keyword: str, category: str) -> None:
        """Add a keyword to learned_categories [DEPRECATED - use save_learned_category_multi_column]"""
        # Kept for backward compatibility; use save_learned_category_multi_column instead
        self.save_learned_category_multi_column(keyword, "", category)
    
    def save_learned_category_multi_column(self, description: str, detail: str, category: str) -> None:
        """Add a multi-column concatenated keyword (Description + Detail) to learned_categories"""
        cats_data = self._load_user_categories_file()
        
        # Initialize from defaults if first time
        if not cats_data.get("default_categories"):
            try:
                from utils.paths import resource_path
                defaults_path = resource_path("utils/default_categories.json")
                defaults_data = json.load(open(defaults_path))
                # In default_categories.json, categories are stored directly under user name
                user_defaults = defaults_data.get(self.owner, {})
                cats_data["default_categories"] = user_defaults
                logger.info(f"Initialized {self.user_categories_path} with defaults")
            except Exception as e:
                logger.warning(f"Could not initialize defaults: {e}")
        
        # Ensure learned_categories exists
        if "learned_categories" not in cats_data:
            cats_data["learned_categories"] = {}
        
        # Ensure category exists in learned_categories
        if category not in cats_data["learned_categories"]:
            cats_data["learned_categories"][category] = []
        
        # Concatenate description and detail (handle nulls/empty gracefully)
        description = str(description).strip() if description else ""
        detail = str(detail).strip() if detail else ""
        combined_keyword = f"{description} {detail}".strip()
        
        # Add keyword if not already there and not empty (case-insensitive check)
        if combined_keyword and combined_keyword.lower() not in [k.lower() for k in cats_data["learned_categories"][category]]:
            cats_data["learned_categories"][category].append(combined_keyword)
        
        self._write_user_categories_file(cats_data)
        # Rebuild merged categories
        self.merged_categories = self._load_and_merge_categories()
        self._update_logger(f"Learned category: '{combined_keyword}' -> '{category}'")

    
    def add_new_category(self, category_name: str) -> None:
        """Add a new empty category to user_categories.json"""
        cats_data = self._load_user_categories_file()
        
        if category_name not in cats_data.get("default_categories", {}):
            if "default_categories" not in cats_data:
                cats_data["default_categories"] = {}
            if "learned_categories" not in cats_data:
                cats_data["learned_categories"] = {}
            
            cats_data["default_categories"][category_name] = []
            cats_data["learned_categories"][category_name] = []
        
        self._write_user_categories_file(cats_data)
        self.merged_categories = self._load_and_merge_categories()
        self._update_logger(f"Added new category: '{category_name}'")
    
    @staticmethod
    def get_file_hash(filename: str, content: bytes) -> str:
        """Generate hash for a file to track if it's been processed"""
        return hashlib.md5((filename + str(content)).encode()).hexdigest()

    # Helper function to get truly unmapped descriptions
    def get_unmapped_transactions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Filter to descriptions with ZERO keyword matches in merged categories.
        Returns list of dicts with 'Descrizione', 'Dettaglio', and 'Count' columns.
        """
        merged_categories = self.merged_categories
        detail_col = CONFIG[self.owner]["headers"].get("detail", "Dettaglio")

        uncategorized = df[df['Categoria'] == 'Uncategorized']

        if uncategorized.empty:
            return []

        # Find truly unmapped: where concatenated description+detail has no keyword matches
        truly_unmapped = []
        for _, row in uncategorized.iterrows():
            description = str(row['Descrizione']).strip() if pd.notna(row['Descrizione']) else ""
            detail = str(row.get(detail_col, "")).strip() if pd.notna(row.get(detail_col)) else ""
            combined_text = f"{description} {detail}".strip()

            matches_any = False
            for keywords in merged_categories.values():
                if any(kw.lower() in combined_text.lower() for kw in keywords):
                    matches_any = True
                    break
            if not matches_any and combined_text:  # Avoid empty rows
                truly_unmapped.append((description, detail))

        # Build result: descriptions + details + counts, sorted by count descending
        result_rows = []
        seen = set()
        for description, detail in truly_unmapped:
            key = (description, detail)
            if key not in seen:
                seen.add(key)
                # Count how many transactions have this description+detail combo
                matching_txs = uncategorized[
                    (uncategorized['Descrizione'] == description) &
                    (uncategorized.get(detail_col, "") == detail)
                ]
                result_rows.append({
                    'Descrizione': description,
                    'Dettaglio': detail,
                    'Count': len(matching_txs),
                    'Category': ''
                })

        # Sort by count descending
        result_df = pd.DataFrame(result_rows)
        if not result_df.empty:
            result_df = result_df.sort_values('Count', ascending=False)

        return result_df.to_dict('records')
