# Pages Reference

## Overview

Conto is built on Dash's multi-page framework. Each page in the `pages/` directory is auto-discovered and registered with its own route. Pages are Python modules that define a `layout` and optional `@callback` decorated functions for interactivity.

## Page Registration

All pages use Dash's page registry pattern:

```python
from dash import register_page

register_page(__name__, path="/route-path", name="Display Name")
```

This auto-registers the module as a page accessible at `/route-path` with "Display Name" appearing in the sidebar navigation menu.

---

## 1. Home Page (`pages/home.py`)

### Overview
The home page handles file uploads, data preview, and download options. It's the primary interface for loading bank statements into the application.

### Registration
```python
register_page(__name__, path="/", name="Home - tabella")
```
- **Route:** `/` (root path)
- **Sidebar Label:** "Home - tabella"

### Layout Components

#### File Upload Zone
```python
dcc.Upload(
    id='upload-data',
    children=html.Div([...]),
    multiple=False  # Single file only
)
```
- Drag-and-drop area for CSV/Excel files
- Styled as dashed border box with upload icon
- Accepts `.csv`, `.xls`, `.xlsx`

#### Output Messages
- `html.Div(id='output-div')` - Displays result of upload/processing
- Shows success message with row count or error details

#### Preview Area
- `html.Div(id='preview-div')` - Rendered by `render_preview()` callback
- Shows `dash_table.DataTable` with first 100 rows
- Includes pagination, sorting, filtering

#### Download Buttons
- "Download visible rows" - Exports currently displayed/filtered rows
- "Download all data" - Exports entire dataset

### Callbacks

#### `handle_upload(user, contents, filename, timestamp)`

**ID:** Implicitly named from outputs

**Inputs:**
- `user-dropdown` value - Selected user profile
- `upload-data` contents - Base64-encoded file
- `upload-data` filename - Original filename
- `data-upload-timestamp` data - Previous timestamp (state)

**Outputs:**
1. `output-div` children - Status message
2. `app-state` data - List of transaction dicts
3. `data-upload-timestamp` data - Current timestamp

**Flow:**

```python
if contents is None:
    # No new upload; load last saved statement
    last = BankStatement(user).load_last_available_statement()
    if last:
        return msg, records, timestamp
    else:
        return "Please upload a file", None, timestamp
else:
    # Process uploaded file
    try:
        # Decode base64
        # Detect file type (CSV vs Excel)
        # Create BankStatement instance
        # Call process_statement()
        # Call categorize_expenses()
        # Save to disk
        # Return records to app-state
    except Exception as e:
        return f"Error: {e}", None, timestamp
```

**Key Features:**
- Auto-loads last saved statement if no new file uploaded
- Supports CSV and Excel formats
- Handles Revolut-style comma decimal separators
- Persists processed data locally
- Returns user-friendly success/error messages

**Return Example:**
```python
(
    "✅ File 'REVOLUT_2025-01-01.csv' loaded! (rows: 127)",
    [
        {
            "Data valuta": "2025-01-15",
            "Descrizione": "CARREFOUR ROMA",
            "Importo": -45.50,
            "Categoria": "Cibo"
        },
        ...
    ],
    "2025-01-15T14:30:22"
)
```

#### `render_preview(data)`

**Inputs:**
- `app-state` data - Current transaction records

**Outputs:**
- `preview-div` children - DataTable component or message

**Process:**
1. Check if data is not None
2. Limit to 100 rows (preview_limit)
3. Type-detect columns:
   - Numeric columns → type='numeric'
   - Datetime-parseable → type='datetime'
   - Everything else → type='text'
4. Create DataTable with:
   - Page size: 10 rows per page
   - Sorting: enabled
   - Filtering: enabled
   - Auto-width cells

**Return Structure:**
```python
html.Div([
    html.H4("Anteprima dati"),
    dash_table.DataTable([...]),
    html.Div(f"Mostrate {min(len(records), 100)} righe."),
    dbc.Row([
        dbc.Col(html.Button("Download visible rows", ...)),
        dbc.Col(html.Button("Download all data", ...))
    ])
])
```

#### `download_excel_preview(n_clicks, derived_virtual_data)`

**Inputs:**
- `download-btn-preview` n_clicks - Button clicks
- `preview-table` derived_virtual_data - Visible/filtered rows (State)

**Outputs:**
- `download-excel-preview` data - Download trigger

**Process:**
1. Get visible table rows from derived_virtual_data
2. Create DataFrame from rows
3. Coerce datetime columns (suppress pandas warnings)
4. Send as Excel file: `statement_data_filtered.xlsx`

**Special Handling:** Suppress "Could not infer format" warnings during datetime parsing

#### `download_excel(n_clicks, data)`

**Inputs:**
- `download-btn` n_clicks - Button clicks
- `app-state` data - All records (State)

**Outputs:**
- `download-excel` data - Download trigger

**Process:**
1. Get all records from app-state
2. Create DataFrame from records
3. Send as Excel file: `statement_data.xlsx`

---

## 2. Expenses Over Time (`pages/expenses-over-time.py`)

### Overview
Displays a histogram of transactions binned by date and colored by expense category. Users can filter by category using a multi-select dropdown.

### Registration
```python
register_page(__name__, name="Movimenti bancari, suddivisi per categoria.")
```
- **Route:** Auto-generated from filename (e.g., `/expenses-over-time`)
- **Sidebar Label:** "Movimenti bancari, suddivisi per categoria."

### Layout

```python
html.Div([
    *home_page_placeholders,  # Upload field, state stores (hidden)
    dcc.Dropdown(
        id='category-dropdown',
        options=[],
        value=[],
        multi=True  # Allow multiple selections
    ),
    dcc.Graph(id='statement-graph')  # Interactive Plotly figure
])
```

### Callbacks

#### `update_dropdown_options(_, user, statement_data)`

**Inputs:**
- `app-state` modified_timestamp - Triggers when app-state is modified (Signal)
- `user-dropdown` value - Current user profile (State)
- `app-state` data - Transaction records (State)

**Outputs:**
1. `category-dropdown` options - List of available categories
2. `category-dropdown` value - Pre-selected values (all categories by default)

**Process:**
1. Check if statement_data is not None
2. Convert records to DataFrame
3. Extract unique categories from category column
4. Return options list and default (all selected)

**Return Example:**
```python
(
    [
        {"label": "Cibo", "value": "Cibo"},
        {"label": "Trasporti", "value": "Trasporti"},
        {"label": "Utilities", "value": "Utilities"}
    ],
    ["Cibo", "Trasporti", "Utilities"]  # All selected by default
)
```

#### `update_graph(selected_categories, user, statement_data)`

**Inputs:**
- `category-dropdown` value - Selected categories
- `user-dropdown` value - Current user (State)
- `app-state` data - All transactions (State)

**Outputs:**
- `statement-graph` figure - Plotly figure

**Process:**
1. Check if statement_data exists
2. Convert records to DataFrame
3. Filter by selected categories: `df[category_col].isin(selected_categories)`
4. Sort by date
5. Call `graph.category_graph(user, filtered_data)`
6. Return Plotly figure

**Graph Details:**
- **X-axis:** Date (auto-binned, ~100 bins)
- **Y-axis:** Sum of transaction amounts
- **Color:** Category (stacked histogram)
- **Interactive:** Hover shows date range and total; legend toggle filters

---

## 3. Expenses Cumulated (`pages/expenses-cumulated.py`)

### Overview
Displays a line chart of cumulative spending over time, with a separate line for each expense category. Users can filter categories.

### Registration
```python
register_page(__name__, name="Spesa cumulata nel tempo, per categoria.")
```
- **Route:** Auto-generated from filename (e.g., `/expenses-cumulated`)
- **Sidebar Label:** "Spesa cumulata nel tempo, per categoria."

### Layout

```python
html.Div([
    *home_page_placeholders,
    dcc.Dropdown(
        id='category-dropdown-csum',
        options=[],
        value=[],
        multi=True
    ),
    dcc.Graph(id='statement-graph-csum')
])
```

### Callbacks

#### `update_dropdown_options(_, user, statement_data)`

**Identical to expenses-over-time page**, but:
- Output to `category-dropdown-csum` (unique ID)
- Same logic: extract categories and pre-select all

#### `update_graph(selected_categories, user, statement_data)`

**Identical setup to expenses-over-time page**, but:
- Takes input from `category-dropdown-csum`
- Output to `statement-graph-csum`
- Calls `graph.cumulative_graph()` instead of `category_graph()`

**Graph Details:**
- **X-axis:** Date (chronological)
- **Y-axis:** Cumulative amount per category
- **Color:** Category (separate line per category)
- **Calculation:** `cumsum(amount) grouped by category`
- **Shows:** Running total spent in each category over time

---

## Shared State & Components

### Session State: `app-state`

**Definition:** `dcc.Store(id='app-state', storage_type='session')`

**Contents:** List of transaction dicts
```python
[
    {
        "Data valuta": "2025-01-15",
        "Descrizione": "CARREFOUR",
        "Importo": -45.50,
        "Categoria": "Cibo"
    },
    ...
]
```

**Lifetime:** Persists across page navigation within session; lost on refresh/close

**Modified Timestamp:** `app-state` includes hidden `.modified_timestamp` property that triggers whenever data changes. Used to update dependent components (dropdowns).

### Shared Upload Components

**Location:** Defined in `utils/config.py` as `home_page_placeholders`

**Components:**
- `upload-data` (dcc.Upload) - File upload input
- `data-upload-timestamp` (dcc.Store) - Timestamp of last upload
- `output-div` (html.Div) - Upload status message

**Included in:** Main `app.layout` to make them accessible from all pages

**Why Shared:** Allows pages other than home to react to file uploads or access the timestamp

### User Dropdown

**ID:** `user-dropdown`
**Location:** Sidebar in `app.py`
**Usage:** Controls which CONFIG profile is used for headers and categories

---

## Callback Patterns

### Pattern 1: Dropdown Population
```python
@callback(
    Output('dropdown-id', 'options'),
    Output('dropdown-id', 'value'),
    Input('app-state', 'modified_timestamp'),  # Signal when data changes
    State('user-dropdown', 'value'),
    State('app-state', 'data')
)
def update_dropdown(_, user, data):
    # Extract unique values from data
    # Return options list and default value
```

### Pattern 2: Graph Update
```python
@callback(
    Output('graph-id', 'figure'),
    Input('filter-dropdown', 'value'),
    State('user-dropdown', 'value'),
    State('app-state', 'data')
)
def update_graph(selected_filters, user, data):
    # Filter data
    # Call graph function
    # Return Plotly figure
```

### Pattern 3: File Download
```python
@callback(
    Output('download-component', 'data'),
    Input('download-button', 'n_clicks'),
    State('table', 'derived_virtual_data'),  # Visible rows only
    prevent_initial_call=True
)
def download_file(n_clicks, visible_data):
    # Convert to DataFrame
    # Return dcc.send_data_frame()
```

---

## Extension: Adding a New Page

1. **Create file:** `pages/my_page.py`
2. **Register page:**
   ```python
   from dash import register_page, html, dcc

   register_page(__name__, name="My Custom Page")
   ```
3. **Define layout:**
   ```python
   layout = html.Div([
       # Your components
   ])
   ```
4. **Add callbacks (optional):**
   ```python
   from dash import callback, Input, Output, State

   @callback(
       Output('my-output', 'children'),
       Input('my-input', 'value')
   )
   def update_output(value):
       return f"You entered: {value}"
   ```
5. **Auto-discovered:** Page appears in sidebar immediately; accessible at `/my-page`

---

## Error Handling in Callbacks

### Pattern: `no_update`
Used when a callback should not trigger output changes:

```python
@callback(Output('graph', 'figure'), Input('data', 'data'))
def update_graph(data):
    if data is None:
        return no_update  # Don't change graph if no data
    # Otherwise, update graph
```

### Pattern: Try-Except
Most callbacks wrap logic in try-except to provide fallback UI:

```python
@callback(Output('div', 'children'), Input('data', 'data'))
def render_preview(data):
    try:
        # Process data
        return table_component
    except Exception as e:
        return html.Div(f"Error: {e}")
```

---

## Performance Notes

- **Large Datasets:** DataTable pagination (`page_size=10`) keeps DOM lean
- **Filtering:** Client-side sorting/filtering in DataTable (100-row limit for preview)
- **Graph Rendering:** Plotly graphs are responsive; hover/zoom handled client-side
- **Category Dropdown:** Uniqueness extracted only when `app-state` changes (efficient)

---

## Internationalization (i18n)

All user-facing strings are in **Italian**:
- "Caricamento dati:" - "Loading data:"
- "Anteprima dati" - "Data preview"
- "Spesa cumulata nel tempo" - "Cumulative spending over time"

To support other languages, centralize strings in a translation dict (future enhancement).
