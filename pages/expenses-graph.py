from utils.bankstatement import BankStatement
from utils.visualizations import cumulative_graph, category_graph
from dash import callback, html, dcc, Input, Output, State, register_page
import pandas as pd

register_page(__name__)

layout = html.Div([
    dcc.Dropdown(
        id='visualization-dropdown',
        options=[
            {'label': 'Grafico Movimenti per Categoria', 'value': 'category-graph'},
            {'label': 'Spesa Cumulata per Categoria', 'value': 'cumulative-graph'}
        ],
        value='category-graph'
    ),
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
    State('app-state', 'data')
)
def update_dropdown_options(_, statement_data):
    statement_data = pd.DataFrame(statement_data)
    # Reload the data only if needed
    if statement_data.empty:
        statement_data = BankStatement().categorize_expenses()

    categories = statement_data['Categoria'].unique()
    return (
        [{'label': c, 'value': c} for c in categories],
        categories.tolist()
    )

@callback(
    Output('statement-graph', 'figure'),
    Output('app-state', 'data'),
    Input('category-dropdown', 'value'),
    Input('visualization-dropdown', 'value'),
    State('app-state', 'data')
)
def update_graph(selected_categories, visualization_type, statement_data):
    statement_data = pd.DataFrame(statement_data)
    # Reload the data only if needed
    if statement_data.empty:
        statement_data = BankStatement().categorize_expenses()

    filtered_data = statement_data[statement_data['Categoria'].isin(selected_categories)]
    filtered_data = filtered_data.sort_values('Data valuta')
    if visualization_type == 'cumulative-graph':
        return cumulative_graph(filtered_data), statement_data.to_dict(orient='records')
    return category_graph(filtered_data), statement_data.to_dict(orient='records')
