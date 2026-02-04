# Data Flow & Processing Pipeline

## Overview

This document details how bank statements flow through the system from upload to visualization.

## 1. Data Ingestion

### User Upload Trigger
- User navigates to Home page (`/`)
- User either:
  - Drags a CSV/Excel file onto the upload zone
  - Clicks to select file from filesystem
- Upload event is captured by the `upload-data` component

### Supported Formats
- **CSV** files (bank export format)
- **Excel** files (.xls, .xlsx)
- Content type detection via MIME type or file extension

## 2. Upload Handler Flow

**Callback:** `home.py::handle_upload()`

### Inputs
- `user-dropdown` value - Current user profile
- `upload-data` contents - Base64-encoded file data
- `upload-data` filename - Original filename
- Previous `data-upload-timestamp` (if any)

### Logic Steps

```
1. Check if file is None
   ├─ YES: Load last available statement from disk
   │   └─ Return: "Loaded session X" message, records, timestamp
   └─ NO: Continue to step 2

2. Decode base64 file content
   └─ Log: filename, content type, file size

3. Detect file type & parse
   ├─ CSV: pandas.read_csv()
   └─ Excel: pandas.read_excel()
   └─ Unsupported: Return error

4. Create BankStatement instance
   └─ Load user profile from CONFIG[user]

5. Process raw data
   └─ Call: process_statement(df)
      ├─ Scan header area for identifier (e.g., "Data contabile")
      ├─ Extract column indices
      ├─ Rename columns to standard names
      ├─ Convert date strings to datetime
      ├─ Convert value strings to numeric (handle ',' decimals)
      └─ Return cleaned DataFrame

6. Categorize transactions
   └─ Call: categorize_expenses()
      ├─ For each transaction description
      ├─ Match against keyword lists in CONFIG[user]["default_categories"]
      ├─ Assign category; default to "Uncategorized"
      └─ Return DataFrame with category column

7. Persist to local storage
   └─ Call: write_data(f"categorized_YYYYMMDD_HHMMSS_{filename}.xlsx")
      ├─ Creates directory: ~/.bankstatementapp/data/ (or %APPDATA%)
      ├─ Writes Excel file
      ├─ Logs save location

8. Return to callback
   └─ Convert records to list of dicts: df.to_dict(orient="records")
   └─ Return: Success message, records list, timestamp
```

### Outputs (to Dash state)
1. **Message** → `output-div` - User feedback ("File loaded" / "Error")
2. **Records** → `app-state` - List of dicts, one per transaction
3. **Timestamp** → `data-upload-timestamp` - ISO format timestamp

## 3. Data Storage States

### In-Session Storage (`dcc.Store`)
```python
dcc.Store(
    id='app-state',
    storage_type='session',  # Lost on page refresh
    data=None  # None until first upload
)
```
**Contains:** List of transaction records (dicts)
```json
[
  {
    "Data valuta": "2025-01-15",
    "Descrizione": "CARREFOUR ROMA",
    "Importo": -45.50,
    "Categoria": "Cibo"
  },
  ...
]
```

### Persistent Storage (Filesystem)

**Path:**
- **macOS/Linux:** `~/.bankstatementapp/data/`
- **Windows:** `%APPDATA%/BankStatementApp/data/`

**Files:**
```
categorized_20250115_143022_REVOLUT_statement.xlsx
categorized_20250114_090530_REVOLUT_statement.xlsx
categorized_20250113_165145_REVOLUT_statement.xlsx
[older files are auto-deleted - only 3 kept]
```

**File Format:** Excel workbook with sheet "Movimenti" containing:
- Standard columns: Date, Description, Amount, Category, etc.
- One row per transaction
- Preserves numeric types and date formatting

## 4. Data Preview & Download

**Callback:** `home.py::render_preview()`

### Trigger
- `app-state` modified (data uploaded/loaded)

### Process
1. Check if data exists (not None)
2. Limit to first 100 rows (preview_limit)
3. Build column definitions with type detection:
   - Numeric → `type='numeric'`
   - Datetime → `type='datetime'` (if parseable)
   - Default → `type='text'`
4. Render `dash_table.DataTable` with:
   - Pagination (10 rows per page)
   - Sorting & filtering enabled
   - Auto-width styling

### Download Options

#### Download Visible Rows
**Callback:** `home.py::download_excel_preview()`
- Exports currently displayed/filtered table rows
- Filename: `statement_data_filtered.xlsx`
- Coerces datetime columns before export

#### Download All Data
**Callback:** `home.py::download_excel()`
- Exports entire dataset from `app-state`
- Filename: `statement_data.xlsx`

## 5. Visualization Pages

### Category-Over-Time Graph

**Page:** `pages/expenses-over-time.py`

#### Update Dropdown Callback
**Inputs:** `app-state` modified timestamp, user selection
**Process:**
1. Extract unique categories from DataFrame
2. Return list of category labels for dropdown
3. Auto-select all categories

**Output:** Category dropdown options and values

#### Update Graph Callback
**Inputs:** Selected categories, user profile, app-state data
**Process:**
1. Load records from `app-state`
2. Filter by selected categories
3. Sort by date
4. Call `graph.py::category_graph(user, filtered_data)`
5. Returns Plotly histogram:
   - **X-axis:** Date (binned, ~100 bins)
   - **Y-axis:** Sum of Importo (amount)
   - **Color:** Category (creates stacked/grouped bars)

**Output:** Interactive Plotly Figure

### Cumulative Spending Graph

**Page:** `pages/expenses-cumulated.py`

#### Process
1. Filter by selected categories (same as above)
2. Sort by date
3. Call `graph.py::cumulative_graph(user, filtered_data)`
4. Returns Plotly line chart:
   - Creates new column: `Cumulative = cumsum(amount) grouped by category`
   - **X-axis:** Date
   - **Y-axis:** Cumulative amount
   - **Color:** Category (separate line per category)

**Output:** Interactive Plotly Figure

## 6. Data Persistence Across Sessions

### On Next App Launch

**Callback:** `home.py::handle_upload()` with `contents=None`

```
1. Check if user changed
2. Create BankStatement(user)
3. Call: load_last_available_statement()
   ├─ Search data_dir for files matching pattern:
   │  "categorized_YYYYMMDD_HHMMSS_<sourcedoc_namepattern>.xlsx"
   ├─ Sort by filename (newest first)
   ├─ Prune files older than 3rd newest
   └─ Load most recent file with pandas.read_excel()
4. Return: {"data": df, "time_saved": timestamp_str}
5. Convert to records and populate app-state
6. Display: "Loaded from previous session YYYY-MM-DD HH:MM:SS"
```

This ensures users see their previous analysis without re-uploading.

## 7. Key Data Transformations

| Stage | Input | Transformation | Output |
|-------|-------|-----------------|--------|
| **Upload** | Base64 file | Decode, parse CSV/Excel | pandas DataFrame |
| **Processing** | Raw DataFrame | Extract headers, type conversion | Cleaned DataFrame |
| **Categorization** | Cleaned DataFrame + keywords | Keyword matching per row | DataFrame + Category column |
| **Storage** | DataFrame | Convert to records, write Excel | JSON (session), Excel (disk) |
| **Preview** | Records list | Type detection, pagination | DataTable component |
| **Visualization** | Records + filters | Filter, aggregate, plot | Plotly Figure |

## 8. Error Handling

### Upload Errors
- **Unsupported format:** Returns user-friendly message, no crash
- **Parse error:** Exception caught, logged, error message returned
- **File too large:** Handled by browser's file upload limits

### Processing Errors
- **Missing identifier column:** Raises ValueError with suggestion
- **Invalid date format:** Coerces to NaT (Not-a-Time), logged as warning
- **Non-numeric value:** Coerces to NaN, logged as warning

### Rendering Errors
- **No data in state:** Displays "No preview available"
- **Type detection fails:** Falls back to 'text' type
- **Graph filter error:** No_update (returns nothing, no change)

All errors are logged via Python's `logging` module for debugging.

## 9. User Workflow Example

```
1. Launch app
2. Home page loads
3. Check for previous data
   ├─ Found: Load last statement, display message
   └─ Not found: Show "Upload data" prompt
4. Upload new REVOLUT_statement.csv
5. File processed, categorized, saved locally
6. Preview shows first 100 rows with download buttons
7. Click "Expenses Over Time"
8. Page loads, dropdown shows all categories (checked by default)
9. Histogram displays transactions by date/category
10. User unchecks some categories
11. Graph updates in real-time (reactive)
12. User clicks "Expenses Cumulated"
13. Line chart shows running totals per category over time
14. User downloads filtered visible rows as Excel
15. Next week, user launches app
16. Previous statement auto-loads from ~/.bankstatementapp/data/
17. User uploads new statement
18. Cycle repeats
```

## 10. Configuration Example

For a new user profile, add to `config.json`:

```json
{
  "newuser": {
    "sourcedoc_namepattern": "Statement_\\d{4}\\d{2}\\d{2}",
    "headers": {
      "loc_identif": "Date",
      "category": "Categoria",
      "date": "Transaction Date",
      "descript": "Description",
      "detail": "Details",
      "value": "Amount"
    },
    "default_categories": {
      "Groceries": ["walmart", "target", "whole foods"],
      "Gas": ["shell", "exxon", "bp"]
    }
  }
}
```

The app will immediately support this user with their specific headers and keywords.
