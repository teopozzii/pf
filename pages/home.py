from dash import html, register_page, callback, Input, Output, State, dcc
import pandas as pd
import logging
import base64
import io
from utils.bankstatement import BankStatement

logger = logging.getLogger(__name__)

register_page(__name__, path="/")  # Root path

layout = html.Div([
    dcc.Store(id="data-upload-timestamp", storage_type='session', data=None),
    html.H1("Benvenuto!"),

    # Drag-and-drop upload component
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

    # Preview area for uploaded/processed data
    html.Div(id='preview-div')
])

@callback(
    Output('output-div', 'children'),
    Output('app-state', 'data'),
    Output('data-upload-timestamp', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('app-state', 'data'),
    State('data-upload-timestamp', 'data')
)
def handle_upload(contents, filename, existing_data, timestamp):
    """Parse uploaded CSV/XLS file, categorize if possible and store in app state.

    Returns a user-friendly message and the data as a list of records (or None on error).
    """
    if existing_data and (not contents):
        logger.info("Existing data in app-state, preserving it across uploads.")
        return f"Dati caricati in sessione {timestamp} preservati.", existing_data, timestamp
    if not (contents or existing_data):
        return "Carica i tuoi estratti conto per iniziare a monitorare le tue spese.", None, timestamp

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

        st = BankStatement()
        st.data = st.process_statement(df)
        st.categorize_expenses()
        records = st.data.to_dict(orient="records")

        logger.info("Prepared %d records for storage in app-state.", len(records))

        if records:
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
    """Render a small HTML table showing up to 10 rows from the stored app-state data."""
    if not data:
        return html.Div("Nessuna anteprima disponibile.")

    # data is expected to be a list of dicts
    try:
        rows = data[:10]
        # determine columns from first row
        cols = list(rows[0].keys()) if rows else []

        header = html.Tr([html.Th(c) for c in cols])
        body = []
        for r in rows:
            body.append(html.Tr([html.Td(str(r.get(c, ''))) for c in cols]))

        table = html.Table([
            html.Thead(header),
            html.Tbody(body)
        ], style={"width": "100%", "border": "1px solid #ccc", "borderCollapse": "collapse"})

        return html.Div([
            html.H4("Anteprima dati"),
            table,
            html.Div(f"Mostrate {len(rows)} righe." , style={"marginTop": "8px", "fontSize": "12px", "color": "#666"})
        ])

    except Exception as e:
        logger.exception("Error while rendering preview: %s", e)
        return html.Div(f"Errore nel render della preview: {e}")
