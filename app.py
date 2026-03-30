from dash import dash, Dash, html, dcc, dash_table, page_registry, callback, Input, Output
import dash_bootstrap_components as dbc
from utils.paths import resource_path
from utils.config import CONFIG, SIDEBAR_STYLE, HeartbeatTracker, home_page_placeholders
from flask import jsonify
import logging
import time

logger = logging.getLogger(__name__)

# Single global instance shared between server and launcher
heartbeat_tracker = HeartbeatTracker()

app = Dash(
    __name__,
    assets_folder=resource_path('assets'),
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

sidebar = html.Div([
    dcc.Dropdown(
        id='user-dropdown',
        options=(users := list(CONFIG.keys())),
        value=users[0],
        style={
            "marginTop": "-15px",
            "marginBottom": "10px"
            }
    ),
    html.H2("Analisi spese", className="display-8",
    style={"marginLeft": "10px"}),
    html.Hr(),
    html.P("Seleziona la visualizzazione desiderata."),
    dbc.Nav(
        [
            dbc.NavLink(page["name"], href=page["path"], active="exact")
            for page in page_registry.values()
            if page["module"] != "pages.not_found_404"
        ],
        vertical=True,
        pills=True,
    )
], style=SIDEBAR_STYLE)

app.layout = dbc.Container([
    # Heartbeat interval - triggers every 2 seconds
    dcc.Interval(id='heartbeat-interval', interval=2000, n_intervals=0),
    # Hidden div for heartbeat callback
    html.Div(id='heartbeat-dummy', style={'display': 'none'}),
    
    # void components that need to be accessible across callbacks
    *home_page_placeholders,
    dcc.Store(id='app-state', storage_type='session', data=None),
    dcc.Download(id="download-excel"),
    dcc.Download(id="download-excel-preview"),
    html.Button("Download visible rows", id="download-btn-preview", style={"display": "none"}), # Hidden
    html.Button("Download all data", id="download-btn", style={"display": "none"}),             # Hidden
    html.Div(dash_table.DataTable(id='preview-table'), style={"display": "none"}),              # Hidden

    # actual app layout:
    html.Div(
        children=[
            dcc.Location(id="url"),
            sidebar,
            html.Div(dash.page_container, style={"margin-left": SIDEBAR_STYLE["width"]}),  # ← Push content right
        ],
        style={
            "display": "flex",
            "flexDirection": "row",   # this is the HBox part
            "gap": "10px",            # spacing between items
            "alignItems": "center"    # vertical alignment
        }
    )
], fluid=True)


# Heartbeat endpoint - called by browser JavaScript every 2 seconds
@app.server.route('/heartbeat', methods=['POST'])
def browser_heartbeat():
    """
    Browser sends a heartbeat every 2 seconds to indicate it's still active.
    Launcher monitors this endpoint to detect when browser closes.
    """
    heartbeat_tracker.record_heartbeat()
    return jsonify({"status": "heartbeat_received"}), 200


# Monitor endpoint - launcher calls this to check if browser is still active
@app.server.route('/last_heartbeat', methods=['GET'])
def last_heartbeat_time():
    """
    Returns how many seconds since the last browser heartbeat.
    Launcher uses this to detect if browser is still connected.
    """
    elapsed = heartbeat_tracker.seconds_since_heartbeat()
    return jsonify({"seconds_since_heartbeat": elapsed}), 200


# Health check endpoint - simple server status
@app.server.route('/health')
def health_check():
    """Simple health check endpoint for server status."""
    return jsonify({"status": "ok", "service": "conto"}), 200


# Graceful shutdown endpoint
@app.server.route('/shutdown', methods=['POST'])
def shutdown_endpoint():
    """Endpoint to trigger graceful server shutdown."""
    logger.info("Shutdown endpoint called")
    # Flask/Werkzeug will handle the shutdown
    return jsonify({"message": "Server shutting down"}), 200


# Client-side callback: send heartbeat to server every 2 seconds
app.clientside_callback(
    """
    function(n_intervals) {
        // Send heartbeat to server asynchronously
        fetch('/heartbeat', {method: 'POST'})
            .catch(err => console.debug('Heartbeat send error:', err));
        // Return timestamp to update dummy div
        return Math.floor(Date.now() / 1000).toString();
    }
    """,
    Output('heartbeat-dummy', 'children'),
    Input('heartbeat-interval', 'n_intervals')
)


if __name__ == '__main__':
    app.run(debug=True)
