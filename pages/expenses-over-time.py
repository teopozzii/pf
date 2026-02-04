from utils.graph import category_graph
from dash import html, dcc, Input, Output, State
from dash import callback, register_page, no_update
import pandas as pd
from utils.config import CONFIG

register_page(__name__, name="Movimenti bancari, suddivisi per categoria.")

layout = html.Div([
    dcc.Dropdown(
        id='category-dropdown',
        options=[],
        value=[],
        multi=True
    ),
    dcc.Graph(id='statement-graph')
])

@callback(
    Output('category-dropdown', "options"),
    Output('category-dropdown', "value"),
    Input('app-state', 'modified_timestamp'),
    Input('user', 'data'),
    State('app-state', 'data')
)
def update_dropdown_options(_, user, statement_data):
    if statement_data is None: return no_update
    statement_data = pd.DataFrame(statement_data)
    categories = statement_data[CONFIG[user]["headers"]["category"]].unique()
    return (
        [{'label': c, 'value': c} for c in categories],
        categories.tolist()
    )

@callback(
    Output('statement-graph', 'figure'),
    Input('user', 'data'),
    Input('category-dropdown', 'value'),
    State('app-state', 'data')
)
def update_graph(user, selected_categories, statement_data):
    if statement_data is None: return no_update
    statement_data = pd.DataFrame(statement_data)
    filtered_data = statement_data[statement_data[CONFIG[user]["headers"]["category"]].isin(selected_categories)]
    filtered_data = filtered_data.sort_values(CONFIG[user]["headers"]["date"])
    return category_graph(user, filtered_data)
