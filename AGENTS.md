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

---

## 4. Working with This Project

### Key Files

- `utils/bankstatement.py:53-73` - Statement processing logic
- `pages/home.py:47-103` - File upload handling
- `utils/graph.py:4-22` - Chart generation

### Debugging Tips

1. Enable debug mode: `app.run(debug=True)`
2. Check browser console for JavaScript errors
3. Use `logger.info()` to trace callback execution
4. Print `ctx.triggered_id` to identify what triggered a callback

### Performance Considerations

- Avoid converting to/from DataFrame repeatedly in callbacks
- Use `derived_virtual_data` for filtered table data
- Limit preview rows (currently 100) to avoid memory issues
