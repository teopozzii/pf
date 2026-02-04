from dash import html, register_page, dcc, dash_table
from dash import Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import logging
import warnings
import base64, io
from utils.bankstatement import BankStatement


logger = logging.getLogger(__name__)

register_page(__name__, path="/", name= "Home - tabella")  # Root path

preview_limit = 100  # Max number of rows to show in preview

layout = html.Div([
    dcc.Store(id="data-upload-timestamp", storage_type='session', data=None),
    html.Div(style={"height": "20px"}),
    html.H3("Caricamento dati:"),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            html.Img(
                src="/assets/upload_icon.png",
                style={'width': '24px', 'height': '24px', 'verticalAlign': 'middle', 'marginRight': '8px'}
            ),
            'Trascina qui il file o ', html.A('clicca per selezionare', style={'color': 'blue'})
        ]),
        style={
            'width': '100%',
            'height': '120px',
            'lineHeight': '120px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-div'),
    html.Div(id='preview-div') # Preview area for uploaded/processed data
])


@callback(
    Output('output-div', 'children'),
    Output('app-state', 'data'),
    Output('data-upload-timestamp', 'data'),
    Input('user-dropdown', 'value'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('data-upload-timestamp', 'data'),
)
def handle_upload(user, contents, filename, timestamp):
    """Parse uploaded CSV/XLS file, categorize if possible and store in app state.

    Returns a user-friendly message and the data as a list of records (or None on error).
    """

    if contents is None:
        last = BankStatement(user)
        last = last.load_last_available_statement()
        df = last["data"]
        if df is None:
            return "Carica i tuoi estratti conto per iniziare a monitorare le tue spese.", None, timestamp
        records = df.to_dict(orient="records")
        logger.info("Loaded default statement with %d records.", len(records))
        return f"Mostrando i dati caricati in sessione {last['time_saved']}.", records, last["time_saved"]

    # Logic for when data is directly uploaded
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        logger.info("Upload received: filename=%s, content_type=%s, bytes=%d", filename, content_type, len(decoded))

        if filename and (filename.lower().endswith('.csv') or 'csv' in content_type):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=None)
        elif filename and (filename.lower().endswith(('.xls', '.xlsx')) or 'excel' in content_type):
            df = pd.read_excel(io.BytesIO(decoded), header=None)
        else:
            logger.warning("Unsupported file type: %s (%s)", filename, content_type)
            return f"Formato file non supportato: {filename}", None

        st = BankStatement(user)
        st.data = st.process_statement(df)
        st.categorize_expenses()
        records = st.data.to_dict(orient="records")

        logger.info("Prepared %d records for storage in app-state.", len(records))

        if records:
            st.data = pd.DataFrame.from_records(records)
            st.write_data(filename=f"categorized_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}_{filename}.xlsx")
            updated_timestamp = pd.Timestamp.now().isoformat()
            return f"✅ File '{filename}' caricato con successo! (righe: {len(records)})", records, updated_timestamp
        else:
            return f"File '{filename}' elaborato ma senza righe da salvare.", None, timestamp

    except Exception as e:
        logger.exception("Error while processing upload: %s", e)
        return f"Errore durante il processamento del file: {e}", None, timestamp


@callback(
    Output('preview-div', 'children'),
    Input('app-state', 'data')
)
def render_preview(data):
    """Render a DataTable showing up to 100 rows from the stored app-state data."""
    if not data:
        return html.Div("Nessuna anteprima disponibile.")

    try:
        # Use raw records from app-state (limit to 100 rows)
        records = data[:preview_limit]

        # Build columns with basic type detection
        cols = []
        if records:
            first = records[0]
            for k, v in first.items():
                col_type = 'text'
                if isinstance(v, (int, float)):
                    col_type = 'numeric'
                else:
                    try:
                        sample = [row.get(k) for row in records if row.get(k) is not None]
                        if sample:
                            # Suppress pandas warning when formats are inconsistent; we just detect if parsing yields datetimes
                            with warnings.catch_warnings():
                                warnings.filterwarnings("ignore", message="Could not infer format")
                                parsed = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)
                            if parsed.notna().sum() > 0:
                                col_type = 'datetime'
                    except Exception:
                        pass
                cols.append({'name': k, 'id': k, 'type': col_type})

        table = dash_table.DataTable(
            id='preview-table',
            columns=cols,
            data=records,
            page_action='native',
            page_size=10,
            sort_action='native',
            filter_action='native',
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
            style_header={'background': '#f9f9f9', 'fontWeight': 'bold'}
        )

        return html.Div([
            html.H4("Anteprima dati"),
            table,
            html.Div(f"Mostrate {min(len(records), 100)} righe.", style={"marginTop": "8px", "fontSize": "12px", "color": "#666"}),
            dbc.Row([
                dbc.Col(
                    html.Button(
                        "Download visible rows",   
                        id="download-btn-preview",
                        style={"width": "100%"}
                    ),
                    width=6
                ),
                dbc.Col(
                    html.Button(
                        "Download all data", 
                        id="download-btn", 
                        style={"width": "100%"}  # Force button to fill column
                    ),
                    width=6  # Half width
                ),
                # Keep dcc.Download components anywhere (they are invisible)
                dcc.Download(id="download-excel-preview"),
                dcc.Download(id="download-excel")
            ], style={"marginTop": "20px"}),
            html.Hr()
        ])

    except Exception as e:
        logger.exception("Error while rendering preview: %s", e)
        return html.Div(f"Errore nel render della preview: {e}")


@callback(
    Output("download-excel-preview", "data"),
    Input("download-btn-preview", "n_clicks"),
    State('preview-table', 'derived_virtual_data'),
    prevent_initial_call=True
)
def download_excel_preview(n_clicks, derived_data):
    if not n_clicks:
        return None
    df = pd.DataFrame(derived_data if derived_data is not None else [])

    # Try to coerce datetime-like columns into real datetimes for a better Excel export.
    # Suppress the pandas 'Could not infer format' warning during detection/parsing.
    try:
        for col in df.select_dtypes(include=['object']).columns:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Could not infer format")
                parsed = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
            if parsed.notna().sum() > 0:
                df[col] = parsed
    except Exception:
        logger.exception("Failed to coerce datetime columns for export; proceeding without coercion.")

    return dcc.send_data_frame(
        df.to_excel,
        "statement_data_filtered.xlsx",
        sheet_name="Movimenti",
        index=False
    )

@callback(
    Output("download-excel", "data"),
    Input("download-btn", "n_clicks"),
    State('app-state', 'data'),
    prevent_initial_call=True
)
def download_excel(n_clicks, data):
    if not n_clicks: return None
    df = pd.DataFrame(data) # Convert list of dicts back to DataFrame
    return dcc.send_data_frame(
        df.to_excel,
        "statement_data.xlsx",
        sheet_name="Movimenti",
        index=False
    )
