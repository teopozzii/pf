"""
Page for categorizing uncategorized transactions from current session.
Shows only truly unmapped descriptions (those with zero keyword matches).
"""

from dash import html, dcc, Input, Output, State, callback, register_page, no_update, callback_context as ctx, ALL
from dash.dash_table import DataTable
import pandas as pd
from typing import List, Dict, Any, Tuple
import logging

from utils.bankstatement import BankStatement
from utils.config import home_page_placeholders, CONFIG

logger = logging.getLogger(__name__)

register_page(__name__, path="/categorize-uncategorized", name="Categorizza Non Categorizzati")

# Helper function to get truly unmapped descriptions
def get_truly_unmapped_descriptions(df: pd.DataFrame, user: str) -> List[Dict[str, Any]]:
    """
    Filter to descriptions with ZERO keyword matches in merged categories.
    Returns list of dicts with 'Descrizione' and 'Count' columns.
    """
    bs = BankStatement(user)
    merged_categories = bs.merged_categories
    
    uncategorized = df[df['Categoria'] == 'Uncategorized']
    
    if uncategorized.empty:
        return []
    
    truly_unmapped = []
    for description in uncategorized['Descrizione'].unique():
        matches_any = False
        for keywords in merged_categories.values():
            if any(kw.lower() in str(description).lower() for kw in keywords):
                matches_any = True
                break
        if not matches_any:
            truly_unmapped.append(description)
    
    # Build result: descriptions + counts, sorted by count descending
    filtered_df = uncategorized[uncategorized['Descrizione'].isin(truly_unmapped)]
    grouped = filtered_df.groupby('Descrizione').size().reset_index(name='Count')
    grouped = grouped.sort_values('Count', ascending=False)
    grouped['Category'] = ''  # Empty dropdown selection
    
    return grouped[['Descrizione', 'Count', 'Category']].to_dict('records')


layout = html.Div([
    *home_page_placeholders,
    dcc.Store(id='category-options-store', data=[]),
    
    html.H1("Categorizza Transazioni Non Categorizzate"),
    
    html.Div(
        "Qui puoi assegnare manualmente le transazioni che non sono state categorizzate automaticamente. "
        "Verranno apprese per i futuri caricamenti.",
        style={'marginBottom': '20px', 'color': '#666'}
    ),
    
    # Info box
    html.Div(
        [
            html.Span("ℹ️ Una volta salvate, queste categorie vengono apprese per i futuri caricamenti. "
                     "Le parole chiave vengono aggiunte alle tue categorie."),
        ],
        style={
            'padding': '10px 15px',
            'backgroundColor': '#e3f2fd',
            'borderLeft': '4px solid #2196F3',
            'marginBottom': '20px',
            'borderRadius': '4px'
        }
    ),
    
    # Search and controls row
    html.Div([
        dcc.Input(
            id='search-description',
            type='text',
            placeholder='Cerca per descrizione...',
            style={'width': '300px', 'padding': '8px', 'marginRight': '10px'}
        ),
        dcc.Dropdown(
            id='rows-per-page',
            options=[
                {'label': '10 per pagina', 'value': 10},
                {'label': '25 per pagina', 'value': 25},
                {'label': '50 per pagina', 'value': 50},
            ],
            value=10,
            style={'width': '150px'}
        ),
        html.Button('🔄 Aggiorna', id='refresh-table-btn', n_clicks=0, style={'marginLeft': '10px'})
    ], style={'marginBottom': '20px', 'display': 'flex', 'gap': '10px'}),
    
    # DataTable
    DataTable(
        id='uncategorized-table',
        columns=[
            {'name': 'Descrizione', 'id': 'Descrizione', 'type': 'text'},
            {'name': 'Conteggio', 'id': 'Count', 'type': 'numeric'},
            {'name': 'Categoria', 'id': 'Category', 'type': 'text'},
        ],
        data=[],
        editable=False,
        row_selectable=False,
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
        ],
        page_size=10,
    ),
    
    # Hidden store to track current dropdown selections
    dcc.Store(id='dropdown-selections-store', data={}),
    
    # Dropdown controls (rendered dynamically per row)
    html.Div(id='dropdown-controls', style={'marginTop': '20px'}),
    
    # Action buttons
    html.Div([
        html.Button(
            'Salva Tutti i Cambiamenti',
            id='save-categorizations-btn',
            n_clicks=0,
            style={
                'padding': '10px 20px',
                'backgroundColor': '#4CAF50',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'cursor': 'pointer',
                'marginRight': '10px'
            }
        ),
        html.Button(
            'Cancella Selezioni',
            id='clear-selections-btn',
            n_clicks=0,
            style={
                'padding': '10px 20px',
                'backgroundColor': '#f44336',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'cursor': 'pointer'
            }
        ),
    ], style={'marginBottom': '20px'}),
    
    # Feedback message
    html.Div(id='feedback-message', style={
        'marginTop': '20px',
        'padding': '10px 15px',
        'borderRadius': '4px'
    }),
    
    # Modal for creating new category
    html.Div([
        html.Div([
            html.Div([
                html.H3("Crea Nuova Categoria"),
                html.Button('✕', id='close-modal-btn', n_clicks=0, style={
                    'position': 'absolute',
                    'right': '10px',
                    'top': '10px',
                    'background': 'none',
                    'border': 'none',
                    'fontSize': '20px',
                    'cursor': 'pointer'
                }),
            ], style={'position': 'relative', 'marginBottom': '20px'}),
            
            html.Label("Nome della categoria:"),
            dcc.Input(
                id='new-category-input',
                type='text',
                placeholder='Es: Shopping, Fitness, etc.',
                style={'width': '100%', 'padding': '8px', 'marginBottom': '10px', 'boxSizing': 'border-box'}
            ),
            
            html.Div(id='create-category-input-error', style={'color': '#f44336', 'marginBottom': '10px'}),
            
            html.Div([
                html.Span("⚠️ Attenzione: ", style={'fontWeight': 'bold'}),
                "Questa categoria non può essere eliminata tramite l'interfaccia. Assicurati prima di confermare.",
            ], style={
                'padding': '10px',
                'backgroundColor': '#fff3cd',
                'borderLeft': '4px solid #ffc107',
                'marginBottom': '20px',
                'borderRadius': '4px'
            }),
            
            html.Div([
                html.Button(
                    'Annulla',
                    id='cancel-modal-btn',
                    n_clicks=0,
                    style={'marginRight': '10px', 'padding': '8px 16px'}
                ),
                html.Button(
                    'Crea Categoria',
                    id='confirm-new-category-btn',
                    n_clicks=0,
                    style={'padding': '8px 16px', 'backgroundColor': '#4CAF50', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer'}
                ),
            ], style={'textAlign': 'right'}),
        ], style={
            'backgroundColor': 'white',
            'padding': '30px',
            'borderRadius': '8px',
            'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'maxWidth': '400px',
            'margin': '0 auto'
        }),
    ], id='modal-overlay', style={
        'display': 'none',
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'width': '100%',
        'height': '100%',
        'backgroundColor': 'rgba(0, 0, 0, 0.5)',
        'zIndex': '1000',
        'justifyContent': 'center',
        'alignItems': 'center'
    }),
])


def toggle_modal_visibility(is_open: bool) -> Dict[str, str]:
    """Helper to toggle modal visibility"""
    return {
        'display': 'flex' if is_open else 'none',
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'width': '100%',
        'height': '100%',
        'backgroundColor': 'rgba(0, 0, 0, 0.5)',
        'zIndex': '1000',
        'justifyContent': 'center',
        'alignItems': 'center'
    }


@callback(
    Output('uncategorized-table', 'data'),
    Output('feedback-message', 'children'),
    Input('refresh-table-btn', 'n_clicks'),
    State('user-dropdown', 'value'),
    State('app-state', 'data'),
    State('search-description', 'value'),
    prevent_initial_call=False
)
def load_uncategorized_items(
    n_clicks: int,
    user: str,
    statement_data: Any,
    search_text: str
) -> Tuple[List[Dict], str]:
    """Load truly unmapped descriptions and optionally filter by search"""
    if not statement_data or not user:
        return [], ""
    
    df = pd.DataFrame(statement_data)
    table_data = get_truly_unmapped_descriptions(df, user)
    
    # Filter by search text if provided
    if search_text and search_text.strip():
        table_data = [row for row in table_data if search_text.lower() in row['Descrizione'].lower()]
    
    count = len(table_data)
    message = f"Trovate {count} transazioni non categorizzate" if count > 0 else "Nessuna transazione senza categoria!"
    
    return table_data, message


@callback(
    Output('dropdown-controls', 'children'),
    Output('category-options-store', 'data'),
    Input('uncategorized-table', 'data'),
    State('user-dropdown', 'value')
)
def populate_dropdowns(table_data: List[Dict], user: str):
    """Create dropdowns for each row and populate with categories"""
    if not table_data or not user:
        return [], []
    
    # Load category options
    bs = BankStatement(user)
    category_options = list(bs.merged_categories.keys())
    
    # Build dropdown list for storage
    dropdown_options = [{'label': cat, 'value': cat} for cat in category_options]
    dropdown_options.append({'label': '➕ Crea Nuova Categoria', 'value': '__CREATE_NEW__'})
    
    # Create dropdown for each row
    dropdowns = []
    for i, row in enumerate(table_data):
        dropdowns.append(
            html.Div([
                html.Span(f"{row['Descrizione']}", style={'marginRight': '20px', 'fontWeight': 'bold'}),
                html.Span(f"({row['Count']} transazioni)", style={'marginRight': '20px', 'color': '#666'}),
                dcc.Dropdown(
                    id={'type': 'category-dropdown', 'index': i},
                    options=dropdown_options,
                    value=row.get('Category', ''),
                    placeholder='Seleziona categoria...',
                    style={'width': '300px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'gap': '10px'})
        )
    
    return dropdowns, dropdown_options


@callback(
    Output('dropdown-selections-store', 'data'),
    [Input({'type': 'category-dropdown', 'index': ALL}, 'value')],
    State('uncategorized-table', 'data'),
    prevent_initial_call=True
)
def update_dropdown_selections(dropdown_values, table_data):
    """Collect all dropdown selections into a Store for the save callback"""
    if not table_data or not dropdown_values:
        return {}
    
    selections = {}
    for i, row in enumerate(table_data):
        if i < len(dropdown_values):
            selections[row['Descrizione']] = dropdown_values[i]
    
    return selections


@callback(
    Output('modal-overlay', 'style', allow_duplicate=True),
    Input({'type': 'category-dropdown', 'index': ALL}, 'value'),
    prevent_initial_call=True,
    allow_duplicate=True
)
def show_modal_on_create_new(dropdown_values):
    """Show modal if any dropdown is set to __CREATE_NEW__"""
    if not dropdown_values or '__CREATE_NEW__' not in dropdown_values:
        return no_update
    
    return toggle_modal_visibility(True)


@callback(
    Output('new-category-input', 'value'),
    Output('create-category-input-error', 'children'),
    Output('modal-overlay', 'style', allow_duplicate=True),
    Input('confirm-new-category-btn', 'n_clicks'),
    State('new-category-input', 'value'),
    State('category-options-store', 'data'),
    prevent_initial_call=True,
    allow_duplicate=True
)
def confirm_new_category(
    n_clicks: int,
    category_name: str,
    existing_categories: List[Dict]
) -> Tuple[str, str, Dict]:
    """Validate and confirm new category creation"""
    if not n_clicks:
        return no_update, no_update, no_update
    
    if not category_name or not category_name.strip():
        return '', "⚠️ Il nome della categoria non può essere vuoto", no_update
    
    existing_names = [opt['value'] for opt in existing_categories if opt['value'] != '__CREATE_NEW__']
    if category_name in existing_names:
        return '', f"⚠️ La categoria '{category_name}' già esiste", no_update
    
    # Valid - clear input and close modal
    return '', "", toggle_modal_visibility(False)


@callback(
    Output('modal-overlay', 'style', allow_duplicate=True),
    [Input('close-modal-btn', 'n_clicks'), Input('cancel-modal-btn', 'n_clicks')],
    prevent_initial_call=True,
    allow_duplicate=True
)
def close_modal(close_clicks, cancel_clicks):
    """Close modal on close or cancel button"""
    if not (close_clicks or cancel_clicks):
        return no_update
    
    return toggle_modal_visibility(False)


@callback(
    [Output('app-state', 'data', allow_duplicate=True),
     Output('feedback-message', 'children', allow_duplicate=True),
     Output('uncategorized-table', 'data', allow_duplicate=True),
     Output('dropdown-selections-store', 'data', allow_duplicate=True)],
    Input('save-categorizations-btn', 'n_clicks'),
    [State('dropdown-selections-store', 'data'),
     State('new-category-input', 'value'),
     State('uncategorized-table', 'data'),
     State('user-dropdown', 'value'),
     State('app-state', 'data')],
    prevent_initial_call=True,
    allow_duplicate=True
)
def save_categorizations(
    n_clicks: int,
    dropdown_selections: Dict,
    new_category_value: str,
    table_data: List[Dict],
    user: str,
    statement_data: List[Dict]
) -> Tuple[List[Dict], str, List[Dict], Dict]:
    """Save learned categorizations and re-categorize session"""
    if not n_clicks:
        return no_update, "Nessun cambio da salvare", no_update, no_update
    
    if not table_data or not user or not dropdown_selections:
        return no_update, "Errore: dati di sessione non trovati", no_update, no_update
    
    bs = BankStatement(user)
    
    # If user created a new category, add it first
    if new_category_value and new_category_value.strip():
        try:
            bs.add_new_category(new_category_value)
        except Exception as e:
            logger.error(f"Error adding new category: {e}")
            return no_update, f"❌ Errore nella creazione della categoria: {e}", no_update, no_update
    
    # Save each learned category assignment
    saved_count = 0
    for description, category in dropdown_selections.items():
        if category and category != '__CREATE_NEW__':
            # Extract first 3-5 words as keyword
            keyword = " ".join(description.split()[:3])
            try:
                bs.save_learned_category(keyword, category)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving learned category for {description}: {e}")
    
    # Re-categorize current session with merged (defaults + learned)
    if statement_data:
        df = pd.DataFrame(statement_data)
        description_col = CONFIG[user]["headers"]["descript"]
        category_col = CONFIG[user]["headers"]["category"]
        
        def categorize_row(description: Any) -> str:
            for category, keywords in bs.merged_categories.items():
                if any(kw.lower() in str(description).lower() for kw in keywords):
                    return category
            return 'Uncategorized'
        
        df[category_col] = df[description_col].apply(categorize_row)
        
        # Reload uncategorized list (should be smaller now)
        new_table_data = get_truly_unmapped_descriptions(df, user)
        
        message = f"✓ Salvate {saved_count} nuove categorie. Sessione aggiornata."
        
        return df.to_dict(orient='records'), message, new_table_data, {}
    
    return no_update, f"✓ Salvate {saved_count} nuove categorie", no_update, no_update


@callback(
    Output('uncategorized-table', 'data', allow_duplicate=True),
    Input('clear-selections-btn', 'n_clicks'),
    State('uncategorized-table', 'data'),
    prevent_initial_call=True,
    allow_duplicate=True
)
def clear_selections(n_clicks: int, table_data: List[Dict]) -> List[Dict]:
    """Clear all dropdown selections"""
    if not n_clicks or not table_data:
        return no_update
    
    for row in table_data:
        row['Category'] = ''
    
    return table_data
