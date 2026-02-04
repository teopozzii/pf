# Utility Modules Reference

## Overview

Utility modules in `utils/` provide cross-cutting functionality for data processing, configuration management, visualization, and resource resolution. This document describes each module's purpose, public interface, and usage patterns.

## 1. `bankstatement.py`

### Purpose
Core data processing engine for parsing, validating, and categorizing bank statement files.

### Class: `BankStatement`

#### Constructor
```python
BankStatement(owner="papà", categories=None)
```

**Parameters:**
- `owner` (str): User profile key from `CONFIG` (e.g., "papà", "teo")
- `categories` (dict, optional): Custom keyword categories dict. If None, uses `CONFIG[owner]["default_categories"]`

**Attributes:**
- `self.data` (pd.DataFrame) - Current working DataFrame
- `self.owner` (str) - Profile name
- `self.headers` (dict) - Column name mappings from user's CONFIG profile
- `self.categories` (dict) - Keyword-to-category mapping
- `self.data_dir` (Path) - Platform-specific local storage directory

**Platform Detection:**
- **Windows:** `%APPDATA%/BankStatementApp/data/`
- **macOS/Linux:** `~/.bankstatementapp/data/`

#### Method: `load_last_available_statement()`
```python
load_last_available_statement() → dict | None
```

**Purpose:** Load the most recent processed statement from local storage.

**Process:**
1. Search `data_dir` for files matching pattern: `categorized_YYYYMMDD_HHMMSS_<owner_pattern>.xlsx`
2. Sort files by name (newest first)
3. Prune files older than 3rd newest (keeps 3 most recent)
4. Read oldest file with pandas.read_excel()

**Returns:**
```python
{
  "data": pd.DataFrame,        # Processed statement
  "time_saved": "YYYYMMDD HH:MM:SS"  # Extraction timestamp
}
```
Returns `None` if no matching files found.

**Example:**
```python
bs = BankStatement("papà")
result = bs.load_last_available_statement()
if result:
    df = result["data"]
    timestamp = result["time_saved"]
```

#### Method: `process_statement(data=None)`
```python
process_statement(data=None) → pd.DataFrame
```

**Purpose:** Extract headers and clean raw CSV/Excel data from bank.

**Parameters:**
- `data` (pd.DataFrame, optional): Raw DataFrame to process. If None, uses `self.data`

**Process:**
1. Scan first 10×10 cell area for identifier (e.g., "Data contabile")
2. Locate column and row indices of identifier
3. Use that row as column headers
4. Remove all rows before and columns before identifier
5. Convert date column to datetime (`%d/%m/%Y` format)
6. Convert amount column to numeric (handles comma decimals: "1.234,56" → 1234.56)

**Returns:** Cleaned DataFrame with proper types

**Raises:** `ValueError` if identifier column not found

**Example:**
```python
bs = BankStatement("papà")
raw_df = pd.read_excel("bank_export.xlsx", header=None)
cleaned_df = bs.process_statement(raw_df)
```

#### Method: `categorize_expenses()`
```python
categorize_expenses() → pd.DataFrame
```

**Purpose:** Add category column by matching transaction descriptions against keyword lists.

**Process:**
1. For each transaction in description column
2. Scan categories in priority order
3. Check if any keyword in category's keyword list appears in description (case-insensitive)
4. Assign first matching category
5. Default to "Uncategorized" if no match

**Returns:** DataFrame with new "Categoria" column added

**Example:**
```python
bs = BankStatement("papà")
bs.data = bs.process_statement(raw_df)
bs.categorize_expenses()
# Now bs.data has a "Categoria" column
```

#### Method: `write_data(filename="categorized_statement.xlsx")`
```python
write_data(filename="categorized_statement.xlsx") → None
```

**Purpose:** Save current DataFrame to Excel in local storage directory.

**Parameters:**
- `filename` (str): Filename to use in data_dir

**File Format:**
- Sheet name: "Movimenti"
- Includes all columns from `self.data`
- Exports index=False (no row numbers)

**Logging:** Logs file path upon success

**Example:**
```python
bs.write_data("categorized_20250115_143022_REVOLUT.xlsx")
# File written to ~/.bankstatementapp/data/categorized_20250115_143022_REVOLUT.xlsx
```

### Usage Example: Complete Flow
```python
from utils.bankstatement import BankStatement
import pandas as pd

# Create instance for user
bs = BankStatement(owner="papà")

# Load previous statement (if exists)
result = bs.load_last_available_statement()
if not result:
    # Process new upload
    raw_df = pd.read_csv("REVOLUT_statement.csv", header=None)
    bs.process_statement(raw_df)
    bs.categorize_expenses()
    bs.write_data("categorized_20250115_143022_REVOLUT.xlsx")
```

---

## 2. `config.py`

### Purpose
Load and expose application configuration, UI placeholders, and styling.

### Module-Level Exports

#### `CONFIG` (dict)
**Source:** `utils/config.json`

Multi-user profile dictionary. Structure:
```python
CONFIG = {
  "papà": {
    "sourcedoc_namepattern": "...",  # Regex pattern for file identification
    "headers": {
      "loc_identif": "Data contabile",    # Header identifier
      "category": "Categoria",             # Category column name
      "date": "Data valuta",               # Date column name
      "descript": "Descrizione",           # Description column name
      "detail": "Dettaglio",               # Detail column name
      "value": "Importo"                   # Amount column name
    },
    "default_categories": {
      "Cibo": ["carrefour", "esselunga", ...],
      "Trasporti": ["parking", "parcheggio", ...],
      ...
    }
  },
  "teo": { ... },
  ...
}
```

**Usage:**
```python
from utils.config import CONFIG

user_headers = CONFIG["papà"]["headers"]
categories = CONFIG["papà"]["default_categories"]
```

#### `SIDEBAR_STYLE` (dict)
**Source:** `utils/sidebar_style.json`

CSS styling object for sidebar. Example:
```python
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    ...
}
```

**Usage:**
```python
from utils.config import SIDEBAR_STYLE
html.Div(sidebar, style=SIDEBAR_STYLE)
```

#### `home_page_placeholders` (list)
**Contents:** List of Dash components that need to be in layout but are hidden

```python
home_page_placeholders = [
    data_preview_msg_placeholder,       # html.Div(id='output-div')
    data_upload_timestamp_placeholder,  # dcc.Store(id='data-upload-timestamp')
    drag_and_drop_placeholder,          # dcc.Upload(id='upload-data')
]
```

**Purpose:** These components must exist in the main layout for callbacks to reference them, even if individual pages don't need them. Defined once here and unpacked into `app.layout`.

**Usage:**
```python
from utils.config import home_page_placeholders

app.layout = dbc.Container([
    *home_page_placeholders,  # Unpack into layout
    dcc.Location(id="url"),
    ...
])
```

---

## 3. `paths.py`

### Purpose
Resolve resource paths in a way that works in both development and PyInstaller bundles.

### Function: `resource_path(relative_path)`
```python
resource_path(relative_path: str) → str
```

**Purpose:** Convert relative path to absolute path, accounting for PyInstaller's temporary folder structure.

**Logic:**
1. Try to read `sys._MEIPASS` (set by PyInstaller)
2. If present, use it as base path (bundle context)
3. If not present, use parent directory of `utils/` (dev context)
4. Join with relative_path

**Returns:** Absolute path string

**Example:**
```python
from utils.paths import resource_path

# In development: /Users/user/code/conto/utils/config.json
# In bundle: /var/folders/temp/_internal/utils/config.json
config_path = resource_path("utils/config.json")

assets_path = resource_path("assets")
pages_path = resource_path("pages")
```

**Why This Matters:**
- PyInstaller bundles resources in a temporary directory structure (`_MEIPASS`)
- File paths are relative in both contexts, but absolute resolution differs
- This function provides a single interface for both

---

## 4. `graph.py`

### Purpose
Generate Plotly figures for expense visualization pages.

### Function: `category_graph(user, filtered_data)`
```python
category_graph(user: str, filtered_data: pd.DataFrame) → plotly.graph_objects.Figure
```

**Purpose:** Create histogram of transactions by date and category.

**Parameters:**
- `user` (str): User profile key (used to get column names from CONFIG)
- `filtered_data` (pd.DataFrame): Transactions to visualize (typically pre-filtered by category)

**Returns:** Plotly Express histogram with:
- **X-axis:** Date column (auto-binned, ~100 bins)
- **Y-axis:** Sum of amount values
- **Color:** Category (creates stacked bars per date range)
- **Title:** "Movimenti per Categoria nel Tempo" (Italian)
- **Interactive:** Hover, zoom, legend toggle

**Example:**
```python
from utils.graph import category_graph
import pandas as pd

df = pd.DataFrame([...])  # Filtered transactions
fig = category_graph("papà", df)
# fig is ready to pass to dcc.Graph(figure=fig)
```

### Function: `cumulative_graph(user, filtered_data)`
```python
cumulative_graph(user: str, filtered_data: pd.DataFrame) → plotly.graph_objects.Figure
```

**Purpose:** Create line chart of cumulative spending over time, split by category.

**Parameters:**
- `user` (str): User profile key
- `filtered_data` (pd.DataFrame): Transactions (typically pre-filtered by category)

**Process:**
1. Create new column 'Cumulative'
2. Group by category and apply cumsum() on amount column
3. Create line plot: Date × Cumulative Amount, colored by Category

**Returns:** Plotly Express line chart with:
- **X-axis:** Date
- **Y-axis:** Cumulative amount per category
- **Color:** Category (separate line per category)
- **Title:** "Spesa Cumulata per Categoria nel Tempo" (Italian)

**Example:**
```python
from utils.graph import cumulative_graph

fig = cumulative_graph("papà", filtered_df)
# Displays running total spent per category
```

---

## 5. `common_utils.py`

### Purpose
IPython/Jupyter-specific utilities for notebook development (traffic monitoring).

### Class: `TrafficMagic`

A Jupyter magic command class for monitoring network traffic during cell execution.

**Magic Command:** `%%nettraffic`

**Usage in Notebooks:**
```python
%%nettraffic
# Python code here
import requests
requests.get("https://example.com")
```

**Output:**
```
1.23 MB inviati; 4.56 MB ricevuti.
```

### Function: `register_traffic_magic()`
```python
register_traffic_magic() → None
```

**Purpose:** Register the magic command in the current IPython kernel.

**Usage:**
```python
from utils.common_utils import register_traffic_magic
register_traffic_magic()

# Now %%nettraffic is available in notebook cells
```

**Implementation:** Uses `psutil` to measure network I/O counters before/after cell execution.

---

## 6. Configuration File Format

### `config.json`

**Location:** `utils/config.json`

**Structure:**
```json
{
  "username": {
    "sourcedoc_namepattern": "RegexPattern_\\d{4}\\d{2}\\d{2}",
    "headers": {
      "loc_identif": "Identifier Column Name",
      "category": "Categoria",
      "date": "Data Valuta",
      "descript": "Descrizione",
      "detail": "Dettaglio",
      "value": "Importo"
    },
    "default_categories": {
      "Category Name": [
        "keyword1",
        "keyword2",
        "partial_match"
      ],
      ...
    }
  },
  ...
}
```

**Key Fields:**
- **sourcedoc_namepattern**: Regex to identify saved files for this user
- **headers**: Maps logical column roles to actual column names (supports different bank formats)
- **default_categories**: Keyword lists for automated categorization

### `sidebar_style.json`

**Location:** `utils/sidebar_style.json`

CSS properties dict for the navigation sidebar. Example:
```json
{
  "position": "fixed",
  "top": 0,
  "left": 0,
  "width": "16rem",
  "padding": "2rem 1rem",
  "background-color": "#f8f9fa"
}
```

---

## Extension Patterns

### Adding Support for New Bank Format

1. Add entry to `config.json`:
   ```json
   {
     "newbank_user": {
       "sourcedoc_namepattern": "NewBank_\\d{8}",
       "headers": {
         "loc_identif": "UNIQUE_IDENTIFIER_COLUMN",
         "date": "TransactionDate",
         ...
       },
       "default_categories": { ... }
     }
   }
   ```

2. User selects "newbank_user" from dropdown
3. `BankStatement` automatically uses correct headers and categories
4. No code changes needed

### Adding Custom Categorization Logic

Extend `BankStatement.categorize_expenses()`:
```python
class CustomBankStatement(BankStatement):
    def categorize_expenses(self):
        # Call parent first
        super().categorize_expenses()
        
        # Add custom rules
        # E.g., special handling for recurring vs one-time
        return self.data
```

### Adding New Graph Type

Add function to `graph.py`:
```python
def my_custom_graph(user, filtered_data):
    """Scatter plot of amount vs day-of-week."""
    filtered_data['dow'] = filtered_data[CONFIG[user]["headers"]["date"]].dt.day_name()
    return px.scatter(
        filtered_data,
        x='dow',
        y=CONFIG[user]["headers"]["value"],
        color=CONFIG[user]["headers"]["category"],
        title="Spending by Day of Week"
    )
```

Then import and use in pages.
