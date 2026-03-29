# AGENTS.md - Conto Development Guide

This file provides guidelines for agentic coding agents working on the Conto project (personal finance dashboard).

---

## 1. Build, Run & Test Commands

### Running the Application

```bash
# Development mode with hot-reload
python app.py

# Desktop app launcher
python launcher.py
```

### Installing Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Testing

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest pytest-mock pytest-cov

# Run all tests
pytest

# Run a single test file
pytest tests/test_bankstatement.py

# Run a single test function
pytest tests/test_bankstatement.py::TestCategorizeExpenses::test_categorize_expenses_keyword_matching

# Run with coverage
pytest --cov=utils --cov-report=html
```

### Test Structure

Tests are located in `tests/` directory:

- `tests/conftest.py` - Shared fixtures for DataFrames and test data
- `tests/test_paths.py` - Path resolution tests
- `tests/test_config.py` - Configuration loading tests
- `tests/test_bankstatement.py` - Core business logic (categorization, parsing)

### Building Executables

```bash
# Windows
pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
  --add-data "assets;assets" --add-data "pages;pages" --add-data "utils;utils" \
  --hidden-import dash_pages --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers

# macOS
pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
  --add-data "assets:assets" --add-data "pages:pages" --add-data "utils:utils" \
  --hidden-import dash_pages --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers
```

---

## 2. Code Style Guidelines

### General Principles

- **Follow existing code patterns** - Match the style of existing files in the project
- **Keep it simple** - Prefer readable, maintainable code over clever one-liners
- **No premature abstraction** - Don't add generalization that isn't needed

### Imports

```python
# Standard library first
import os
import sys
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Third-party libraries (alphabetical)
import pandas as pd
import plotly.express as px

# Dash and related (specific order)
from dash import html, dcc, Input, Output, State, callback, register_page
import dash_bootstrap_components as dbc

# Local utilities
from utils.bankstatement import BankStatement
from utils.config import CONFIG
```

### Formatting

- **Line length**: Maximum 100 characters
- **Indentation**: 4 spaces (no tabs)
- **Blank lines**: Two blank lines between top-level definitions, one between methods
- **Trailing commas**: Use when appropriate for cleaner diffs

### Type Hints

Always use type hints for function signatures and variable annotations:

```python
# Good
def process_statement(self, data: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
    categories: Dict[str, List[str]] = {}

# Avoid
def process_statement(self, data=None):
    categories = {}
```

#### Project-Specific Type Conventions

- **Session data (dcc.Store)**: Use `List[Dict[str, Any]]` for data stored in session state
- **Callback Input/State**: Leave untyped (Dash dynamic nature)
- **Plotly figures**: Use `plotly.graph_objs.Figure` for return types:

```python
import plotly.graph_objs as go

def update_graph(...) -> go.Figure:
    return px.bar(...)
```

- **Callback return tuples**: Use explicit tuple types:

```python
def handle_upload(...) -> tuple[str, None, str | None]:
    return "message", None, timestamp
```

- **Dash components**: Can use type annotations for variables holding components:

```python
app: Dash = Dash(...)
sidebar: html.Div = html.Div([...])
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `bankstatement.py` |
| Classes | PascalCase | `BankStatement` |
| Functions/methods | snake_case | `categorize_expenses()` |
| Variables | snake_case | `statement_data` |
| Constants | UPPER_SNAKE | `PREVIEW_LIMIT = 100` |
| Private methods | prefix with `_` | `_update_logger()` |

### Error Handling

```python
# Use specific exception types
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    logger.warning(f"File not found: {file_path}")
    return None
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise

# Always log errors with context
logger.exception("Error while processing upload: %s", e)

# Return user-friendly messages, not raw exceptions
return f"Errore durante il processamento del file: {e}", None, timestamp
```

### Logging

- Use the module-level logger pattern
- Log levels: `DEBUG` (dev), `INFO` (normal), `WARNING` (recoverable), `ERROR` (failure)

```python
logger = logging.getLogger(__name__)
```

### Dash/Plotly Specific

- Use `callback_context as ctx` to determine which input triggered the callback
- Return `no_update` from callbacks when no change is needed
- Use `dcc.Store` for client-side session state
- Always include `prevent_initial_call=True` for download callbacks

### File Structure

```
conto/
├── app.py                    # Main Dash app (DO NOT modify layout directly)
├── launcher.py               # Desktop app entry point
├── pages/                   # Dash pages (one file per route)
│   ├── home.py
│   ├── expenses-over-time.py
│   └── expenses-cumulated.py
├── utils/                   # Shared utilities
│   ├── bankstatement.py    # Core business logic
│   ├── config.py           # Configuration loading
│   ├── graph.py            # Plotly visualizations
│   └── paths.py            # Path resolution
├── tests/                   # Test files (create when needed)
├── docs/                    # Documentation
└── assets/                  # Static files (CSS, images)
```

### Configuration

- User-specific settings go in `utils/config.json`
- Never hardcode user data or paths
- Use `resource_path()` for cross-platform path resolution

### Git Conventions

- Commit message format: `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- Example: `feat(home): add file type validation`

---

## 3. Common Patterns

### Adding a New Page

```python
from dash import html, register_page

register_page(__name__, path="/my-page", name="My Page Name")

layout = html.Div([
    html.H1("My Page"),
    # ...
])

# Add callbacks with proper Input/Output patterns
```

### Processing Uploaded Files

```python
import base64, io

content_type, content_string = contents.split(',')
decoded = base64.b64decode(content_string)

if filename.endswith('.csv'):
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=None)
elif filename.endswith(('.xls', '.xlsx')):
    df = pd.read_excel(io.BytesIO(decoded), header=None)
```

### Storing and Retrieving Session Data

```python
# Store: convert DataFrame to dict
dcc.Store(id='app-state', data=df.to_dict(orient="records"))

# Retrieve: convert back to DataFrame
df = pd.DataFrame(statement_data)
```

### Advanced Callback Patterns

#### Distinguishing Multiple Triggers

```python
from dash import callback_context as ctx

@callback(
    Output('app-state', 'data'),
    [Input('user-dropdown', 'value'), Input('upload-data', 'contents')],
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def handle_upload(user, contents, filename) -> tuple[List[Dict[str, Any]], str]:
    if ctx.triggered_id == "user-dropdown":
        # User switched profiles: load their last statement
        return load_last_available_statement(user), current_timestamp()
    elif ctx.triggered_id == "upload-data":
        # File uploaded: process through pipeline
        return process_and_store(contents, filename)
    
    return no_update, no_update
```

**Key Pattern**: Use `ctx.triggered_id` to identify which input caused the callback. This is essential when multiple inputs share the same callback.

#### Watching Store Data Changes

```python
@callback(
    Output('graph-container', 'children'),
    Input('app-state', 'modified_timestamp'),  # Triggers on any Store data change
    State('app-state', 'data'),
    State('user-dropdown', 'value')
)
def update_graph(timestamp, statement_data, user) -> go.Figure:
    # Dash automatically triggers this callback when app-state data changes
    # modified_timestamp is cleaner than listening to data prop directly
    if not statement_data:
        return no_update
    
    df = pd.DataFrame(statement_data)
    return category_graph(user, df)
```

**Key Pattern**: Listening to `modified_timestamp` is Dash's way to respond to Store changes without iterating the entire data object.

#### Download Callbacks

```python
@callback(
    Output("download-excel", "data"),
    Input("btn-export", "n_clicks"),
    State('app-state', 'data'),
    prevent_initial_call=True  # Critical: prevents spurious downloads on page load
)
def download_data(n_clicks, statement_data):
    if not statement_data:
        return no_update
    
    df = pd.DataFrame(statement_data)
    return dcc.send_data_frame(df.to_excel, "statement.xlsx", index=False)
```

### BankStatement Class Details

The `BankStatement` class is the core of the application. Instantiate it per user:

```python
from utils.bankstatement import BankStatement

bs = BankStatement("papà")  # User name from CONFIG keys
```

**Initialization behavior:**
- Creates user-specific data directory: `~/.bankstatementapp/data/` (macOS/Linux) or `%APPDATA%/BankStatementApp` (Windows)
- Loads headers and categories from `CONFIG[user_name]`
- Uses relative path resolution via `resource_path()` for cross-platform compatibility

**File output naming:**
```
categorized_<YYYYMMDD>_<HHMMSS>_<original_filename>.xlsx
```

**Automatic cleanup**: Only keeps 3 most recent files; deletes older ones to prevent directory bloat.

**Key methods:**
- `process_statement(df)` - Header detection + type parsing (returns DataFrame)
- `categorize_expenses(df)` - Apply keyword matching (returns DataFrame with "Categoria" column)
- `write_data(df, filename)` - Persist to Excel with timestamp

### Transaction Data Shape

Each record stored in `app-state` follows this structure:

```python
{
    "Data contabile": "2024-01-01",      # Accountable date (datetime string ISO format)
    "Data valuta": "2024-01-02",         # Value date (datetime string ISO format)
    "Descrizione": "Pagamento CARREFOUR",  # Description (str)
    "Dettaglio": "Acquisti",             # Detail/category hint (str)
    "Importo": -50.0,                    # Amount (float; negative for expenses)
    "Categoria": "Cibo"                  # Assigned category from config (str)
}
```

**Data Type Transitions:**
- **Upload**: Base64 file → `io.StringIO()`/`io.BytesIO()` → pandas DataFrame (all columns str initially)
- **Processing**: `BankStatement.process_statement()` parses dates and amounts to proper types
- **Storage**: `df.to_dict(orient="records")` → JSON-serializable list of dicts
- **Graph/Preview**: `pd.DataFrame(records)` converts back to typed DataFrame for analysis

**Key Constraint**: When converting to dict format, datetime columns become ISO format strings; floating point amounts are preserved.

### Configuration & Initialization

#### Config Loading Pattern

```python
# In utils/config.py (executed at import time)
import json
from utils.paths import resource_path

CONFIG = json.load(open(resource_path("utils/config.json")))
SIDEBAR_STYLE = json.load(open(resource_path("utils/sidebar_style.json")))

# Shared UI components defined here
home_page_placeholders = [
    dcc.Store(id='app-state', data=[]),
    dcc.Store(id='data-upload-timestamp'),
    dcc.Upload(id='upload-data', ...),
    # ... other shared components
]
```

**Important**: Configuration is loaded **once at import time**. Changes to `config.json` require restarting the development server or the deployed application.

#### Per-User Configuration Structure

Each user profile in `config.json` contains:

```json
{
    "papà": {
        "sourcedoc_namepattern": "MovimentiCC_\\d{4}-\\d{2}-\\d{2}",
        "headers": {
            "loc_identif": "Data contabile",     // Sentinel column for header detection
            "date": "Data valuta",               // Which column contains dates
            "value": "Importo",                  // Which column contains amounts
            "descript": "Descrizione",           // Which column has descriptions
            "category": "Categoria",             // Output column name
            "detail": "Dettaglio"                // Detail/note column
        },
        "default_categories": {
            "Medici": ["dentistico", "medical", "odontoiatrico"],
            "Utenze": ["enel energia", "vodafone", "gas"],
            "Cibo": ["carrefour", "salumeria", "supermercato"]
        }
    }
}
```

**Header Detection**: `BankStatement.process_statement()` scans the first 30×30 cells for the sentinel value (`headers.loc_identif`). This allows flexibility when bank statement layouts change.

#### Placeholder Components Pattern

```python
# In pages/home.py
from utils.config import home_page_placeholders

layout = html.Div([
    html.Div(id='page-content', style={'flex': '1'}),
    *home_page_placeholders,  # Unpack shared Store, Upload, etc.
    html.Div(id='upload-output')
])
```

**Why This Pattern**: Shared UI components (Store, Upload) are defined once in `config.py` and imported into every page. Prevents duplication and avoids circular imports (pages would be circular if they all tried to import from home.py).

---

## 4. Working with This Project

### Key Files

**Core Business Logic:**
- [utils/bankstatement.py](utils/bankstatement.py) - `BankStatement` class with processing pipeline (header detection, type parsing, categorization)
- [utils/config.py](utils/config.py) - Configuration loading and shared placeholder components
- [utils/graph.py](utils/graph.py) - Plotly graph generation (`category_graph()`, `cumulative_graph()`)

**API & State Management:**
- [pages/home.py](pages/home.py) - Upload handler and user dropdown callback (`handle_upload()`)
- [app.py](app.py) - Main Dash app factory (DO NOT modify page layout directly)

**Page Implementations:**
- [pages/expenses-over-time.py](pages/expenses-over-time.py) - Time-series graph callback subscribes to `app-state.modified_timestamp`
- [pages/expenses-cumulated.py](pages/expenses-cumulated.py) - Cumulative graph with filtering

**Configuration & Paths:**
- [utils/config.json](utils/config.json) - User profiles, headers, and categories (restart required after changes)
- [utils/sidebar_style.json](utils/sidebar_style.json) - CSS styles for sidebar
- [utils/paths.py](utils/paths.py) - Cross-platform path resolution (PyInstaller support)

### Debugging Tips

1. Enable debug mode: `app.run(debug=True)`
2. Check browser console for JavaScript errors
3. Use `logger.info()` to trace callback execution
4. Print `ctx.triggered_id` to identify what triggered a callback

### Testing Fixtures

Tests in this project use a **hierarchical fixture pattern**:

```python
# Minimal reference data (from conftest.py)
@pytest.fixture
def sample_categories():
    return {
        "Cibo": ["carrefour", "salumeria"],
        "Medici": ["farmacia", "dental"]
    }

# Level 1: Raw statement (30×7 grid with sentinel header)
@pytest.fixture
def raw_statement_data():
    return pd.DataFrame({
        "Data contabile": [None] * 5 + ["01/01/2024", ...],  # Padding rows
        "Data valuta": [...],
        "Descrizione": [...],
        # ... other columns
    })

# Level 2: After process_statement() (headers extracted, types parsed)
@pytest.fixture
def processed_statement_data(raw_statement_data):
    bs = BankStatement("papà")
    return bs.process_statement(raw_statement_data)
    # Now has: proper dates, numeric amounts, no padding rows

# Level 3: After categorize_expenses() (final output)
@pytest.fixture
def categorized_statement_data(processed_statement_data):
    bs = BankStatement("papà")
    return bs.categorize_expenses(processed_statement_data)
    # Now has: Categoria column with matched categories
```

Use Level 1 when testing header detection, Level 2 for date/amount parsing, and Level 3 for categorization logic. This makes tests focused and reusable.

### BankStatement Processing Pipeline

The `BankStatement` class processes statements in three distinct stages:

#### Stage 1: Header Detection & Cleaning

```python
# Scans first 30×30 cells for sentinel (e.g., "Data contabile")
# Once found, extracts header row and removes padding rows above it
processed_df = statement.process_statement(raw_df)
# Returns: DataFrame with headers extracted, same columns as input
```

#### Stage 2: Type Parsing

```python
# Automatic type conversion happens inside process_statement():
# - Dates: pd.to_datetime(..., format="%d/%m/%Y")
# - Amounts: .str.replace(',', '.').astype(float)
# Result: properly typed columns for analysis
```

#### Stage 3: Categorization

```python
# Iterates CONFIG[user]["default_categories"] in order
# First matching keyword wins (order matters!)
# Unmatched descriptions get "Uncategorized"
statement.categorize_expenses(processed_df)
# Returns: same DataFrame + "Categoria" column
```

### Performance Constraints

- **Preview limit**: Fixed at 100 rows (`PREVIEW_LIMIT = 100`) to prevent browser memory issues
- **Store size**: Client-side session storage has ~5MB limit (large statements may not fit)
- **Download efficiency**: Uses `derived_virtual_data` from DataTable (only exports visible/sorted data)
- **File cleanup**: Only keeps 3 most recent processed files; older ones auto-deleted
