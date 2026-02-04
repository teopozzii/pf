# Project Architecture

## Overview

**Conto** is a personal finance dashboard application built with **Dash** (Plotly's Python framework) that enables users to analyze bank statements with customizable expense categorization and visualization. The application is distributed as a standalone executable for Windows and macOS via PyInstaller.

## High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│              Standalone Executable              │
│         (PyInstaller - Windows/macOS)           │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│         Launcher (launcher.py)                  │
│   • Starts Dash server in background thread    │
│   • Opens default browser to http://127.0.0.1  │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│      Dash Application (app.py)                  │
│   • Multi-page layout with sidebar navigation  │
│   • Session-based state management             │
│   • User selection dropdown                    │
└─────────────────────────────────────────────────┘
         ↓                        ↓
┌──────────────────┐   ┌──────────────────┐
│  Page Modules    │   │  Utility Modules │
│  (pages/)        │   │  (utils/)        │
└──────────────────┘   └──────────────────┘
```

## Core Components

### 1. **Entry Points**

#### `launcher.py`
- Bootstraps the desktop application
- Runs Dash server in a daemon thread
- Automatically opens the default browser
- Handles keyboard interrupts gracefully
- Freezes multiprocessing support for PyInstaller compatibility

#### `app.py`
- Main Dash application factory
- Configures multi-page routing via `use_pages=True`
- Defines global layout with sidebar and content area
- Manages session-based data store (`dcc.Store`)
- Loads Bootstrap theme for styling

### 2. **Page Modules** (`pages/`)

All pages inherit from Dash's page registry system. Each page registers with its own route and name.

| File | Route | Purpose |
|------|-------|---------|
| `home.py` | `/` | Data upload interface; displays data preview with download options |
| `expenses-over-time.py` | (auto-route) | Category-filtered histogram showing transactions over time |
| `expenses-cumulated.py` | (auto-route) | Category-filtered line graph showing cumulative spending by category |

**Page Pattern:**
- Use `register_page(__name__, ...)` to auto-register
- Define `layout` as the page's visual structure
- Use `@callback` decorators for reactive updates
- Share state via `dcc.Store` components

### 3. **Utility Modules** (`utils/`)

#### `bankstatement.py`
Core data processing class (`BankStatement`) responsible for:
- **Loading**: Retrieves categorized bank statements from persistent storage
- **Processing**: Extracts headers from raw CSV/Excel files via pattern matching
- **Categorization**: Maps transaction descriptions to expense categories using keyword matching
- **Persistence**: Writes processed data to Excel files with timestamps

Key methods:
- `load_last_available_statement()` - Loads most recent categorized statement
- `process_statement(data)` - Parses raw bank data
- `categorize_expenses()` - Applies keyword-based categorization rules
- `write_data()` - Persists processed data locally

#### `config.py`
Loads and exposes:
- **`CONFIG`** - User profiles with column headers and category definitions (from `config.json`)
- **`SIDEBAR_STYLE`** - CSS styling for the sidebar
- **Placeholder components** - Hidden UI elements used across multiple pages (upload field, state stores)

#### `paths.py`
Cross-platform resource path resolution:
- Detects PyInstaller bundle context (`sys._MEIPASS`)
- Falls back to development mode directory structure
- Essential for accessing `assets/`, `pages/`, and `utils/` in both packaged and dev environments

#### `graph.py`
Plotly visualization helpers:
- `category_graph()` - Histogram of transactions by category over time
- `cumulative_graph()` - Line chart of cumulative spending per category

#### `common_utils.py`
IPython magic commands for Jupyter notebooks (traffic monitoring - used in `classificazione_spese.ipynb` and `conto.ipynb`)

### 4. **Configuration** (`utils/config.json`)

Multi-user profile system where each user has:

```json
{
  "username": {
    "sourcedoc_namepattern": "regex pattern for source files",
    "headers": {
      "loc_identif": "column name for header identifier",
      "date": "column name for transaction date",
      "descript": "column name for transaction description",
      "value": "column name for transaction amount",
      "category": "column name for expense category",
      "detail": "column name for transaction detail"
    },
    "default_categories": {
      "Category Name": ["keyword1", "keyword2", ...]
    }
  }
}
```

This enables the same app to handle multiple bank statement formats.

## Data Flow

### Initialization Flow
1. User launches the application (launcher.py)
2. Browser opens to `http://127.0.0.1:8050`
3. Dash app renders sidebar with user dropdown
4. Home page loads and checks for previously saved statements
5. If no upload yet, last saved statement is auto-loaded from persistent storage

### Upload & Processing Flow
1. User selects or drags CSV/Excel bank statement
2. `home.py::handle_upload()` callback triggered
3. `BankStatement` class:
   - Decodes uploaded file
   - Calls `process_statement()` to extract headers and structure data
   - Calls `categorize_expenses()` to apply keyword rules
   - Returns categorized records
4. Records stored in `app-state` store (session-based)
5. Save timestamp and Excel file locally for future sessions

### Visualization Flow
1. User navigates to visualization page
2. Dropdown updates to show available categories (from current state data)
3. User filters categories
4. Graph callback:
   - Filters data by selected categories
   - Calls `graph.py` to generate Plotly figure
   - Returns interactive chart

### Data Persistence
- **Session**: `dcc.Store(storage_type='session')` - in-memory, lost on refresh
- **Local**: `~/.bankstatementapp/data/` (macOS/Linux) or `%APPDATA%/BankStatementApp/data/` (Windows)
  - Stores processed Excel files with timestamp
  - Keeps 3 most recent files; older ones are pruned
  - Automatically loaded on next app start

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend Framework** | Dash (Plotly) |
| **UI Components** | Dash Bootstrap Components |
| **Data Processing** | pandas, numpy |
| **Visualization** | Plotly Express |
| **Storage** | Excel (openpyxl), Filesystem |
| **Packaging** | PyInstaller |
| **CI/CD** | GitHub Actions |
| **Language** | Python 3.11+ |

## Design Patterns

### 1. **Configuration-Driven Multi-User Support**
Users and their bank statement formats are defined in `config.json`, making the app extensible without code changes.

### 2. **Shared State via Store Components**
`dcc.Store` provides reactive state management:
- `app-state` - Current session's transaction records
- `data-upload-timestamp` - Timestamp of last upload
- Custom page stores for dropdown selections

### 3. **Placeholder Components**
Common UI elements (upload field, state stores) are defined once in `config.py` and reused across pages to ensure consistency.

### 4. **Lazy Page Registration**
Pages are auto-discovered and registered via Dash's `use_pages=True`, eliminating manual route definitions.

### 5. **Cross-Platform Path Resolution**
The `resource_path()` utility abstracts OS differences, allowing the same code to work in development and as a PyInstaller bundle.

## Dependency Graph

```
launcher.py
  ↓
app.py
  ├─→ utils/paths.py (resource path resolution)
  ├─→ utils/config.py
  │    ├─→ utils/config.json
  │    ├─→ utils/sidebar_style.json
  │    └─→ utils/paths.py
  └─→ pages/ (auto-discovered)
        ├─→ home.py
        │    ├─→ utils/bankstatement.py
        │    │    ├─→ utils/config.py
        │    │    └─→ pandas, re, logging
        │    └─→ pandas, base64, io
        ├─→ expenses-over-time.py
        │    ├─→ utils/graph.py
        │    ├─→ utils/config.py
        │    └─→ pandas
        └─→ expenses-cumulated.py
             ├─→ utils/graph.py
             ├─→ utils/config.py
             └─→ pandas

External Libraries:
  • dash[pages]
  • dash-bootstrap-components
  • plotly
  • pandas
  • openpyxl (Excel support)
  • pyinstaller (distribution)
```

## Key Design Decisions

1. **Dash for UI**: Provides reactive, Python-native frontend without JavaScript
2. **Session Storage + Local Persistence**: Balances responsiveness (session) with data durability (local files)
3. **PyInstaller Bundling**: Delivers app as single executable, no Python installation needed for end users
4. **Configuration-Driven Categories**: Users can customize keywords without touching code
5. **Multi-User via Config**: Supports different bank formats for different users in same application

## Extension Points

- **New Pages**: Add files to `pages/` directory following the Dash page pattern
- **New Graph Types**: Extend `utils/graph.py` with new visualization functions
- **New Categories**: Edit `utils/config.json` to add keywords or create user profiles
- **Data Sources**: Extend `BankStatement` class to support additional file formats
