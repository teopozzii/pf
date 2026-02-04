# Conto: Personal Finance Dashboard

**Conto** is a personal finance analysis dashboard that enables you to upload bank statements, automatically categorize expenses, and visualize spending patterns with interactive charts. Built with Dash (Plotly) and distributed as standalone executables for Windows and macOS.

## Features

- 📊 **Interactive Charts** - Visualize transactions by category over time and cumulative spending trends
- 📤 **File Upload** - Support for CSV and Excel bank statements from various banks
- 🏷️ **Auto-Categorization** - Smart keyword-based expense categorization (customizable per user)
- 💾 **Data Persistence** - Automatically saves processed statements for quick access across sessions
- 👥 **Multi-User Support** - Different bank formats and categorization rules per user
- 🖥️ **Desktop App** - No Python installation required; runs as a standalone executable
- 📥 **Data Export** - Download filtered or full datasets as Excel files

## Quick Start

### For End Users

1. **Download the latest release** from the [Releases](../../releases) page
   - `BankStatementApp-Windows.exe` (Windows)
   - `BankStatementApp-MacOS` (macOS)

2. **Run the application**
   - **Windows:** Double-click the `.exe` file
   - **macOS:** 
     ```bash
     chmod +x /path/to/BankStatementApp-MacOS
     /path/to/BankStatementApp-MacOS
     ```
     (Grant permission when macOS prompts)

3. **Upload your bank statement**
   - Drag and drop a CSV or Excel file, or click to select
   - Application auto-categorizes transactions
   - Browse charts and download data

### For Developers

1. **Clone repository:**
   ```bash
   git clone <repo-url>
   cd conto
   ```

2. **Set up environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run in development mode:**
   ```bash
   python launcher.py
   # or for hot-reloading:
   python app.py
   ```

## Project Structure

```
conto/
├── app.py                      # Main Dash application
├── launcher.py                 # Desktop app entry point
├── requirements.txt            # Python dependencies
├── .github/
│   └── workflows/
│       └── build.yml          # CI/CD pipeline (PyInstaller)
├── pages/                      # Multi-page app pages
│   ├── home.py                # File upload & preview
│   ├── expenses-over-time.py  # Category histogram
│   └── expenses-cumulated.py  # Cumulative spending chart
├── utils/                      # Shared utilities
│   ├── bankstatement.py       # Bank statement processing
│   ├── config.py              # Configuration & UI components
│   ├── config.json            # User profiles & categories
│   ├── paths.py               # Cross-platform path resolution
│   ├── graph.py               # Plotly visualizations
│   └── common_utils.py        # Jupyter utilities
├── assets/                     # Images, icons, CSS
├── docs/                       # Detailed documentation
│   ├── ARCHITECTURE.md        # System design & dependencies
│   ├── DATA_FLOW.md           # Data processing pipeline
│   ├── UTILS.md               # Utility module reference
│   ├── PAGES.md               # Page & callback documentation
│   └── BUILD_AND_DEPLOYMENT.md # PyInstaller & CI/CD setup
└── README.md                   # This file
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Purpose |
|----------|---------|
| [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) | High-level system design, component interactions, dependency graph, and technology stack |
| [**DATA_FLOW.md**](docs/DATA_FLOW.md) | Complete data ingestion, processing, persistence, and visualization pipeline with examples |
| [**UTILS.md**](docs/UTILS.md) | Detailed reference for each utility module (BankStatement, config, paths, graph) |
| [**PAGES.md**](docs/PAGES.md) | Page layouts, callback signatures, and interaction patterns for all pages |
| [**BUILD_AND_DEPLOYMENT.md**](docs/BUILD_AND_DEPLOYMENT.md) | PyInstaller configuration, GitHub Actions CI/CD, and release instructions |

**Start with [ARCHITECTURE.md](docs/ARCHITECTURE.md) for a complete overview.**

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend Framework** | Dash (Plotly) |
| **UI Components** | Dash Bootstrap Components |
| **Data Processing** | pandas, NumPy |
| **Visualization** | Plotly Express |
| **Storage** | Excel (openpyxl), Filesystem |
| **Packaging** | PyInstaller |
| **CI/CD** | GitHub Actions |
| **Language** | Python 3.11+ |

## Key Design Decisions

1. **Dash Web Framework** - Enables reactive, Python-native UI without JavaScript
2. **Configuration-Driven** - Support for multiple users and bank formats via `config.json`
3. **PyInstaller Bundling** - Single executable; no Python installation required for users
4. **Session + Persistent Storage** - In-memory state for responsiveness, local files for durability
5. **Multi-Page Routing** - Separate pages for upload, histogram, and cumulative views

## How It Works

### Upload & Processing
1. User uploads CSV/Excel bank statement
2. `BankStatement` class parses file with user-specific column headers
3. Transactions are auto-categorized via keyword matching
4. Processed data stored locally and in session

### Visualization
1. Home page shows data preview with download options
2. "Expenses Over Time" displays histogram by category
3. "Expenses Cumulated" shows cumulative spending trend per category
4. Interactive charts allow filtering and export

### Persistence
- Processed statements saved to `~/.bankstatementapp/data/` (or `%APPDATA%` on Windows)
- Most recent 3 files kept; older ones auto-deleted
- Next app launch auto-loads previous session's data

## Configuration

User profiles and expense categories are defined in `utils/config.json`:

```json
{
  "username": {
    "sourcedoc_namepattern": "BankFilePattern_\\d{8}",
    "headers": {
      "loc_identif": "Unique Identifier Column",
      "date": "Transaction Date Column",
      "descript": "Description Column",
      "value": "Amount Column",
      "category": "Category Column"
    },
    "default_categories": {
      "Groceries": ["carrefour", "whole foods", "supermarket"],
      "Transport": ["parking", "gas station"],
      ...
    }
  }
}
```

Add new users without modifying code—the app auto-detects them in the user dropdown.

## Development

### Adding a New Page

1. Create `pages/my_page.py`:
   ```python
   from dash import register_page, html

   register_page(__name__, name="My Page")

   layout = html.Div([
       html.H1("My Page")
   ])
   ```
2. Auto-discovered and added to sidebar

### Adding Categories

Edit `utils/config.json` and add keywords to a category. Re-upload to apply.

### Building Executables

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Run platform-specific build:
   ```bash
   # Windows
   pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
     --add-data "assets;assets" --add-data "pages;pages" --add-data "utils;utils" \
     --hidden-import dash_pages --hidden-import dash_bootstrap_components \
     --hidden-import plotly.io._renderers

   # macOS (note : instead of ;)
   pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
     --add-data "assets:assets" --add-data "pages:pages" --add-data "utils:utils" \
     --hidden-import dash_pages --hidden-import dash_bootstrap_components \
     --hidden-import plotly.io._renderers
   ```

### Automated Releases

Push a git tag to trigger GitHub Actions build:

```bash
git tag v0.1.7
git push origin v0.1.7
```

Both Windows and macOS executables are built and attached to the GitHub Release automatically.

See [BUILD_AND_DEPLOYMENT.md](docs/BUILD_AND_DEPLOYMENT.md) for detailed instructions.

## macOS Installation

On first run, macOS may block execution. To grant permission:

1. Make executable:
   ```bash
   chmod +x /path/to/BankStatementApp-MacOS
   ```

2. Run it, and macOS will block it

3. Go to **System Settings** → **Privacy & Security** → **Security**

4. Find "BankStatementApp-MacOS" in the list and click **"Open Anyway"**

## Roadmap

See [TODO.md](TODO.md) for planned features and improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or feature requests, please open an issue in the repository.
