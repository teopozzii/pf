from dash import html, register_page

register_page(__name__, path="/")  # Root path

layout = html.Div([
    html.H1("Benvenuto!"),
    html.P("Seleziona una pagina dal menu laterale."),
    # Add welcome content, stats, etc.
])
