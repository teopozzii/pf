"""
Pivot page for analyzing expenses by category and date with monthly subtotals.
Shows transactions in a continuous scroll with sticky total and month subtotal rows.
Supports multi-select category filtering and customizable date range.
"""

from dash import html, dcc, register_page, Input, Output, State, callback, no_update
from dash.dash_table import DataTable
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

from utils.config import home_page_placeholders, CONFIG

logger = logging.getLogger(__name__)

register_page(__name__, path="/pivot", name="Pivot")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_default_date_range() -> Tuple[str, str]:
    """
    Calculate default date range: last 90 days from today.
    Returns: (start_date, end_date) as ISO date strings
    """
    today = datetime.now().date()
    start_date = today - timedelta(days=90)
    return start_date.isoformat(), today.isoformat()


def insert_subtotal_rows(
    df: pd.DataFrame,
    user: str,
    config: Dict
) -> List[Dict[str, Any]]:
    """
    Insert subtotal rows at month boundaries in a sorted DataFrame.
    
    Args:
        df: Sorted DataFrame with transactions (newest first)
        user: User profile name
        config: CONFIG[user] from config.json
        
    Returns:
        List of dicts ready for DataTable, with row_type field ('total', 'subtotal', 'transaction')
    """
    date_col = config['headers']['date']
    amount_col = config['headers']['value']
    
    result = []
    total_amount = 0.0
    total_count = 0
    
    # Add placeholder for total row at top (will be updated at the end)
    total_placeholder_idx = len(result)
    result.append({
        'row_type': 'total',
        'Data': 'TOTAL',
        'Descrizione': '',
        'Dettaglio': '',
        'Importo': 0.0,
    })
    
    if df.empty:
        return result
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Group by year-month and process each group
    df_sorted = df.sort_values(date_col, ascending=False)  # Newest first
    
    current_month = None
    month_amount = 0.0
    month_count = 0
    
    for idx, row in df_sorted.iterrows():
        transaction_date = row[date_col]
        
        # Extract year-month from transaction date
        if pd.isna(transaction_date):
            continue
            
        transaction_month = pd.Timestamp(transaction_date).strftime('%Y-%m')
        amount = float(row[amount_col]) if pd.notna(row[amount_col]) else 0.0
        
        # Check if we've entered a new month
        if current_month is not None and transaction_month != current_month:
            # Insert subtotal row for the previous month
            result.append({
                'row_type': 'subtotal',
                'Data': f'Month {current_month}',
                'Descrizione': '',
                'Dettaglio': f'({month_count} transazioni)',
                'Importo': month_amount,
            })
            month_amount = 0.0
            month_count = 0
        
        current_month = transaction_month
        
        # Add transaction row
        date_str = pd.Timestamp(transaction_date).strftime('%Y-%m-%d')
        result.append({
            'row_type': 'transaction',
            'Data': date_str,
            'Descrizione': row.get(config['headers'].get('descript', 'Descrizione'), ''),
            'Dettaglio': row.get(config['headers'].get('detail', 'Dettaglio'), ''),
            'Importo': amount,
        })
        
        # Accumulate
        month_amount += amount
        month_count += 1
        total_amount += amount
        total_count += 1
    
    # Add final month subtotal
    if current_month is not None:
        result.append({
            'row_type': 'subtotal',
            'Data': f'Month {current_month}',
            'Descrizione': '',
            'Dettaglio': f'({month_count} transazioni)',
            'Importo': month_amount,
        })
    
    # Update total row with actual values
    result[total_placeholder_idx] = {
        'row_type': 'total',
        'Data': 'TOTAL',
        'Descrizione': '',
        'Dettaglio': f'({total_count} transazioni)',
        'Importo': total_amount,
    }
    
    return result


# ============================================================================
# LAYOUT
# ============================================================================

layout = html.Div([
    *home_page_placeholders,
    
    html.H1("Pivot"),
    
    html.Div(
        "Visualizza tutte le tue spese categorizzate con subtotali mensili. "
        "Filtra per categoria e personalizza l'intervallo di date.",
        style={'marginBottom': '20px', 'color': '#666'}
    ),
    
    # Filters row
    html.Div([
        html.Div([
            html.Label("Categorie:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='pivot-category-dropdown',
                multi=True,
                searchable=True,
                placeholder='Seleziona categorie...',
                style={'width': '100%'}
            ),
        ], style={'flex': '0 1 auto', 'maxWidth': '550px', 'minWidth': '200px', 'marginRight': '20px'}),
        
        html.Div([
            html.Label("Data inizio:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.DatePickerSingle(
                id='pivot-start-date',
                date=None,
                display_format='YYYY-MM-DD',
                style={'width': '100%'}
            ),
        ], style={'flex': '0.5', 'marginRight': '20px'}),
        
        html.Div([
            html.Label("Data fine:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.DatePickerSingle(
                id='pivot-end-date',
                date=None,
                display_format='YYYY-MM-DD',
                style={'width': '100%'}
            ),
        ], style={'flex': '0.5', 'marginRight': '20px'}),
        
        html.Button(
            '🔄 Aggiorna',
            id='pivot-refresh-btn',
            n_clicks=0,
            style={
                'padding': '8px 16px',
                'backgroundColor': '#2196F3',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'cursor': 'pointer',
                'height': '36px'
            }
        ),
    ], style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'alignItems': 'flex-end',
        'marginBottom': '20px',
        'gap': '10px',
        'position': 'relative',
        'zIndex': '100'
    }),
    
    # Info box
    html.Div(
        id='pivot-info-box',
        style={
            'padding': '15px',
            'backgroundColor': '#e3f2fd',
            'borderLeft': '4px solid #2196F3',
            'marginBottom': '20px',
            'borderRadius': '4px'
        }
    ),
    
    # Export button
    html.Div([
        html.Button(
            '📥 Esporta Dati',
            id='pivot-export-btn',
            n_clicks=0,
            style={
                'padding': '10px 20px',
                'backgroundColor': '#4CAF50',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'cursor': 'pointer'
            }
        ),
        dcc.Download(id='pivot-download'),
    ], style={'marginBottom': '20px'}),
    
    # Table container
    html.Div([
        DataTable(
            id='pivot-table',
            columns=[
                {'name': 'Data', 'id': 'Data', 'type': 'text'},
                {'name': 'Descrizione', 'id': 'Descrizione', 'type': 'text'},
                {'name': 'Dettaglio', 'id': 'Dettaglio', 'type': 'text'},
                {'name': 'Importo', 'id': 'Importo', 'type': 'numeric'},
            ],
            data=[],
            editable=False,
            row_selectable=False,
            style_table={
                'overflowY': 'auto',
                'maxHeight': '80vh',
                'maxWidth': '100%',
                'tableLayout': 'fixed'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'minWidth': '50px'
            },
            style_cell_conditional=[
                {'if': {'column_id': 'Data'}, 'width': '100px'},
                {'if': {'column_id': 'Importo'}, 'width': '100px'},
            ],
            style_header={'backgroundColor': '#f9f9f9', 'fontWeight': 'bold'},
            style_data_conditional=[],
        )
    ], style={'width': '100%', 'overflow': 'hidden'}),
    html.Div(
        style={'height': '20px'}
    ),  # Extra div to ensure proper spacing at the bottom
])


# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    Output('pivot-category-dropdown', 'options'),
    Output('pivot-category-dropdown', 'value'),
    Input('app-state', 'modified_timestamp'),
    State('user-dropdown', 'value'),
    State('app-state', 'data'),
)
def populate_category_options(timestamp, user, statement_data):
    """
    Populate category dropdown with unique categories from the data.
    Default to all categories.
    """
    if not statement_data or not user:
        return [], []
    
    df = pd.DataFrame(statement_data)
    category_col = CONFIG[user]['headers']['category']
    
    if category_col not in df.columns:
        logger.warning(f"Category column '{category_col}' not found in data for user {user}")
        return [], []
    
    categories = sorted(df[category_col].unique().tolist())
    options = [{'label': cat, 'value': cat} for cat in categories]
    
    return options, categories  # Default: all categories (user can clear/filter via dropdown)


@callback(
    Output('pivot-start-date', 'date'),
    Output('pivot-end-date', 'date'),
    Input('app-state', 'modified_timestamp'),
)
def initialize_date_range(timestamp):
    """
    Initialize date picker with default range (last 90 days).
    """
    start_date, end_date = get_default_date_range()
    return start_date, end_date


@callback(
    Output('pivot-table', 'data'),
    Output('pivot-table', 'style_data_conditional'),
    Output('pivot-info-box', 'children'),
    Input('pivot-category-dropdown', 'value'),
    Input('pivot-start-date', 'date'),
    Input('pivot-end-date', 'date'),
    Input('pivot-refresh-btn', 'n_clicks'),
    State('user-dropdown', 'value'),
    State('app-state', 'data'),
)
def load_and_transform_data(
    selected_categories,
    start_date,
    end_date,
    n_clicks,
    user,
    statement_data
) -> Tuple[List[Dict], List[Dict], html.Div]:
    """
    Main callback: filter data by categories and date range,
    sort by date (newest first), insert subtotal rows, and prepare for display.
    """
    if not statement_data or not user:
        return [], [], html.Div("Nessun dato disponibile. Carica un estratto conto per iniziare.")
    
    df = pd.DataFrame(statement_data)
    
    # Validate date range
    if not start_date or not end_date:
        return [], [], html.Div("Errore: seleziona un intervallo di date valido.")
    
    try:
        # DatePickerSingle returns dates as strings in YYYY-MM-DD format
        start_dt = pd.Timestamp(start_date).date()
        end_dt = pd.Timestamp(end_date).date()
        if start_dt > end_dt:
            return [], [], html.Div("Errore: la data di inizio deve essere prima della data di fine.")
    except Exception as e:
        logger.error(f"Date parsing error: {e}")
        return [], [], html.Div("Errore nel parsing delle date.")
    
    # Get config
    config = CONFIG[user]
    date_col = config['headers']['date']
    category_col = config['headers']['category']
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Filter by categories
    if selected_categories:
        df = df[df[category_col].isin(selected_categories)]
    
    if df.empty:
        info_text = f"Nessuna transazione trovata per {start_date} - {end_date}."
        return [], [], html.Div(info_text)
    
    # Filter by date range
    df = df[
        (df[date_col].dt.date >= start_dt) &
        (df[date_col].dt.date <= end_dt)
    ]
    
    if df.empty:
        info_text = f"Nessuna transazione trovata per {start_date} - {end_date}."
        return [], [], html.Div(info_text)
    
    # Sort by date (newest first)
    df = df.sort_values(date_col, ascending=False)
    
    # Insert subtotal rows
    table_data = insert_subtotal_rows(df, user, config)
    
    # Calculate info
    transaction_count = sum(1 for row in table_data if row['row_type'] == 'transaction')
    total_amount = sum(row['Importo'] for row in table_data if row['row_type'] == 'transaction')
    
    # Build conditional styling for row types
    style_data_conditional = [
        # Total row: sticky at top
        {
            'if': {'filter_query': '{row_type} = total'},
            'fontWeight': 'bold',
            'backgroundColor': '#d0f0c0',
            'position': 'sticky',
            'top': '0px',
            'left': '0px',
            'zIndex': '10',
        },
        # Subtotal rows: sticky at offset
        {
            'if': {'filter_query': '{row_type} = subtotal'},
            'fontStyle': 'italic',
            'backgroundColor': '#e8f5e9',
            'position': 'sticky',
            'top': '35px',  # Total row ≈40px; 5px buffer for visual separation
            'left': '0px',
            'zIndex': '9',
        },
        # Alternating row colors for transactions
        {
            'if': {
                'filter_query': '{row_type} = transaction',
                'row_index': 'odd'
            },
            'backgroundColor': '#f5f5f5',
        },
    ]
    
    # Build info box
    categories_text = ', '.join(selected_categories) if selected_categories else 'Tutte'
    start_date_str = str(start_date) if start_date else 'N/A'
    end_date_str = str(end_date) if end_date else 'N/A'
    info_text = f"Mostrando {transaction_count} transazioni (from {start_date_str} to {end_date_str}) | Categorie: {categories_text} | Totale: €{total_amount:.2f}"
    
    return table_data, style_data_conditional, html.Div(info_text)


@callback(
    Output('pivot-download', 'data'),
    Input('pivot-export-btn', 'n_clicks'),
    State('pivot-table', 'data'),
    State('user-dropdown', 'value'),
    prevent_initial_call=True
)
def export_to_excel(n_clicks, table_data, user):
    """
    Export filtered table data to Excel, excluding row_type column.
    """
    if not table_data or not user:
        return no_update
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(table_data)
        
        # Remove row_type column
        if 'row_type' in df.columns:
            df = df.drop(columns=['row_type'])
        
        # Send as Excel
        from dash import dcc
        return dcc.send_data_frame(
            df.to_excel,
            "pivot_export.xlsx",
            index=False,
            engine='openpyxl'
        )
    except Exception as e:
        logger.exception(f"Error exporting data: {e}")
        return no_update
