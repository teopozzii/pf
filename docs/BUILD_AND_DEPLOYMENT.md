# Build, Packaging & Deployment

## Overview

Conto is packaged as standalone executables for Windows and macOS using **PyInstaller**. Builds are automated via **GitHub Actions** and distributed as downloadable releases.

---

## Development Setup

### Prerequisites
- Python 3.11 or later
- pip or conda for package management

### Installation

1. **Clone repository:**
   ```bash
   git clone <repo-url>
   cd conto
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running in Development

**Option 1: Direct execution**
```bash
python launcher.py
```
Browser opens to `http://127.0.0.1:8050`

**Option 2: Dash debug mode (with code reloading)**
```bash
python app.py
```
Runs with `debug=True` and hot reloading enabled

---

## PyInstaller Configuration

### Why PyInstaller?

- **No Python installation required** for end users
- **Single executable file** per platform
- **Bundles all dependencies** (pandas, plotly, dash, etc.)
- **Works offline** after build

### Build Process

#### Step 1: Dependency Collection
PyInstaller scans code for imports and bundles:
- All explicitly imported modules (pandas, plotly, dash, etc.)
- Hidden imports (specified via `--hidden-import`)

#### Step 2: Bundle Creation
- Creates temporary directory with Python interpreter + libraries
- Includes data files (assets, pages, utils directories)
- Generates single executable

#### Step 3: Resource Packaging

**Data Files Included:**
- `assets/` - Images, CSS, static files
- `pages/` - Python page modules
- `utils/` - Utility modules (config.json, sidebar_style.json included)

### PyInstaller Command (Windows)

```bash
pyinstaller launcher.py \
  --onefile \
  --windowed \
  --name BankStatementApp \
  --add-data "assets;assets" \
  --add-data "pages;pages" \
  --add-data "utils;utils" \
  --hidden-import dash_pages \
  --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers
```

**Flags:**
- `--onefile` - Single executable (vs. directory)
- `--windowed` - No console window on Windows
- `--name` - Output executable name
- `--add-data` - Include data directories (semicolon separator on Windows)
- `--hidden-import` - Force inclusion of dynamically loaded modules

### PyInstaller Command (macOS)

```bash
pyinstaller launcher.py \
  --onefile \
  --windowed \
  --name BankStatementApp \
  --add-data "assets:assets" \
  --add-data "pages:pages" \
  --add-data "utils:utils" \
  --hidden-import dash_pages \
  --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers
```

**Difference:** Colon `:` separator instead of semicolon for `--add-data`

### Output Artifacts

**Windows:**
```
dist/BankStatementApp.exe    (~200-300 MB)
```

**macOS:**
```
dist/BankStatementApp        (~300-400 MB, unsigned)
```

### Local Build Instructions

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run appropriate command (Windows or macOS above)

3. Test executable:
   ```bash
   # Windows
   .\BankStatementApp.exe

   # macOS
   ./dist/BankStatementApp
   ```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/build.yml`

#### Trigger
- **Event:** Push tag matching pattern `v*` (e.g., `v1.0.0`, `v0.1.7`)
- **Example:**
  ```bash
  git tag v0.1.7
  git push origin v0.1.7
  ```

#### Build Matrix
Builds run in parallel on two runners:

| Runner | OS | Output | Release Name |
|--------|----|---------|----|
| `windows-latest` | Windows Server 2022 | `BankStatementApp.exe` | `BankStatementApp-Windows.exe` |
| `macos-latest` | macOS 12+ | `dist/BankStatementApp` | `BankStatementApp-MacOS` |

#### Workflow Steps

**Step 1: Checkout Code**
```yaml
- uses: actions/checkout@v3
```
Clones repository at tagged commit

**Step 2: Setup Python**
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'
```
Installs Python 3.11 on runner

**Step 3: Install Dependencies**
```yaml
- name: Install Dependencies
  run: |
    pip install --upgrade pip
    pip install -r requirements.txt
```
Installs all packages from requirements.txt

**Step 4: Build with PyInstaller**

*Windows:*
```yaml
- name: Build with PyInstaller
  if: matrix.os == 'windows-latest'
  run: |
    pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
      --add-data "assets;assets" --add-data "pages;pages" --add-data "utils;utils" \
      --hidden-import dash_pages --hidden-import dash_bootstrap_components \
      --hidden-import plotly.io._renderers
```

*macOS:*
```yaml
- name: Build with PyInstaller
  if: matrix.os == 'macos-latest'
  run: |
    pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
      --add-data "assets:assets" --add-data "pages:pages" --add-data "utils:utils" \
      --hidden-import dash_pages --hidden-import dash_bootstrap_components \
      --hidden-import plotly.io._renderers
```

**Step 5: Rename Artifact**

*Windows:*
```yaml
- name: Rename Artifact (for clear Release filenames)
  if: matrix.os == 'windows-latest'
  run: move dist/BankStatementApp.exe BankStatementApp-Windows.exe
```

*macOS:*
```yaml
- name: Rename Artifact (MacOS)
  if: matrix.os == 'macos-latest'
  run: mv dist/BankStatementApp BankStatementApp-MacOS
```

**Step 6: Create Release**
```yaml
- name: Release
  uses: softprops/action-gh-release@v1
  if: startsWith(github.ref, 'refs/tags/')
  with:
    files: ${{ matrix.asset_name }}
```
Creates GitHub Release with executable as downloadable asset

---

## Release & Distribution

### Creating a Release

1. **Merge code to main branch**
   ```bash
   git checkout main
   git pull
   ```

2. **Create annotated tag**
   ```bash
   git tag -a v0.1.7 -m "Release version 0.1.7"
   ```

3. **Push tag to trigger build**
   ```bash
   git push origin v0.1.7
   ```

4. **Wait for Actions to complete**
   - Monitor: GitHub repo → Actions tab
   - ~5-10 minutes per platform
   - All builds must complete before release is created

5. **Verify release**
   - GitHub repo → Releases
   - Two assets available for download
   - Download URLs provided on release page

### Version Numbering

Use **semantic versioning:** `vMAJOR.MINOR.PATCH`
- `v1.0.0` - Major release (breaking changes)
- `v0.1.7` - Minor/patch releases

---

## Installation for End Users

### Windows

1. Download `BankStatementApp-Windows.exe` from Releases
2. Double-click to run
3. Windows may show security warning (unverified publisher)
   - Click "More info" → "Run anyway"
   - Or add to antivirus whitelist

### macOS

1. Download `BankStatementApp-MacOS` from Releases
2. Open Terminal
3. Make executable:
   ```bash
   chmod +x /path/to/BankStatementApp-MacOS
   ```
4. Run:
   ```bash
   /path/to/BankStatementApp-MacOS
   ```
5. On first run, macOS may block execution
   - Go to **System Settings** → **Privacy & Security**
   - Find "BankStatementApp-MacOS" in "Security" section
   - Click "Open Anyway"

---

## Dependencies

### Core Runtime Dependencies

From `requirements.txt`:

```txt
pandas          # Data manipulation
plotly          # Interactive charts
numpy           # Numerical computing
dash            # Web framework
dash[pages]     # Multi-page routing
dash-bootstrap-components  # Bootstrap theme
pyinstaller     # Packaging tool
openpyxl        # Excel file support
```

### Build-Time Hidden Imports

These are dynamically loaded and must be explicitly bundled:

- `dash_pages` - Dash's page routing system (loaded by `use_pages=True`)
- `dash_bootstrap_components` - Bootstrap theme components
- `plotly.io._renderers` - Plotly rendering engine

### Development Dependencies (Optional)

For development, consider adding:

```bash
pip install jupyter  # For notebook analysis
```

---

## Troubleshooting

### macOS Code Signing Issues

**Problem:** "BankStatementApp cannot be opened because the developer cannot be verified"

**Solutions:**
1. Use `chmod +x` and "Open Anyway" (recommended for personal use)
2. Self-sign executable:
   ```bash
   codesign -s - /path/to/BankStatementApp-MacOS
   ```

### PyInstaller: Missing Module

**Problem:** `ModuleNotFoundError` when running bundled app

**Solution:** Add to `--hidden-import` in build.yml if module is dynamically loaded:
```bash
--hidden-import module_name
```

### PyInstaller: Asset Files Not Found

**Problem:** `FileNotFoundError` for `assets/`, `config.json`, etc.

**Solution:** Ensure files are included in `--add-data`:
```bash
--add-data "assets:assets"
--add-data "utils:utils"
```

And use `resource_path()` utility for file resolution (already implemented).

---

## Build Requirements Summary

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Runtime |
| pandas | latest | Data processing |
| plotly | latest | Charting |
| dash[pages] | latest | Web framework + routing |
| dash-bootstrap-components | latest | UI theme |
| openpyxl | latest | Excel I/O |
| PyInstaller | 6.0+ | Packaging |

---

## Future Enhancements

- **Code signing:** Add Apple Developer certificate for macOS
- **Auto-updates:** Implement in-app update checker
- **Installer:** Create .msi (Windows) or .dmg (macOS) installers
- **Continuous monitoring:** Monitor Action logs for build failures
- **Test builds:** Add testing step before release build

---

## CI/CD File Reference

Full workflow file: `.github/workflows/build.yml`

Key sections:
- `on:` - Trigger conditions
- `permissions:` - GitHub API permissions (needed for release creation)
- `jobs:` - Build jobs (Windows + macOS)
- `strategy:` - Matrix for parallel builds
- `steps:` - Build steps (checkout, install, build, release)
