from utils.bankstatement import BankStatement
from utils.visualizations import cumulative_graph, category_graph
from dash import Dash, html, dcc, Input, Output

statement = BankStatement()
statement.categorize_expenses()

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Analisi Movimenti Conto Corrente"),
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
        options=[{'label': cat, 'value': cat} for cat in statement.data['Categoria'].unique()],
        value=statement.data['Categoria'].unique().tolist(),
        multi=True
    ),
    dcc.Graph(id='statement-graph')
])

@app.callback(
    Output('statement-graph', 'figure'),
    Input('category-dropdown', 'value'),
    Input('visualization-dropdown', 'value')
)
def update_graph(selected_categories, visualization_type):
    filtered_data = statement.data[statement.data['Categoria'].isin(selected_categories)]
    filtered_data = filtered_data.sort_values('Data valuta')
    if visualization_type == 'cumulative-graph':
        return cumulative_graph(filtered_data)    
    return category_graph(filtered_data)

if __name__ == '__main__':
    app.run(debug=True)
