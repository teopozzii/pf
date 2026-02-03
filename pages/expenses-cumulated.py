from utils.bankstatement import _load_statement_data_from_dict
from utils.graph import cumulative_graph
from dash import callback, html, dcc, Input, Output, State, register_page

register_page(__name__, name="Spesa cumulata nel tempo, per categoria.")

layout = html.Div([
    dcc.Dropdown(
        id='category-dropdown-csum',
        options=[],
        value=[],
        multi=True
    ),
    dcc.Graph(id='statement-graph-csum')
])

@callback(
    Output('category-dropdown-csum', "options"),
    Output('category-dropdown-csum', "value"),
    Input('app-state', 'modified_timestamp'),
    State('app-state', 'data')
)
def update_dropdown_options(_, statement_data):
    statement_data = _load_statement_data_from_dict(statement_data)
    categories = statement_data['Categoria'].unique()
    return (
        [{'label': c, 'value': c} for c in categories],
        categories.tolist()
    )

@callback(
    Output('statement-graph-csum', 'figure'),
    Input('category-dropdown-csum', 'value'),
    State('app-state', 'data')
)
def update_graph(selected_categories, statement_data):
    statement_data = _load_statement_data_from_dict(statement_data)

    filtered_data = statement_data[statement_data['Categoria'].isin(selected_categories)]
    filtered_data = filtered_data.sort_values('Data valuta')
    return cumulative_graph(filtered_data)
