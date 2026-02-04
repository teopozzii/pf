from dash import dash, Dash, html, dcc, dash_table, page_registry
import dash_bootstrap_components as dbc
from utils.paths import resource_path
from utils.config import CONFIG, SIDEBAR_STYLE, home_page_placeholders

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
    ),
    html.H2("Analisi spese", className="display-8"),
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

if __name__ == '__main__':
    app.run(debug=True)
