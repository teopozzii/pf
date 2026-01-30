from utils import Movimenti
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

movimenti = Movimenti()
movimenti.categorize_movimenti()

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Analisi Movimenti Conto Corrente"),
    dcc.Dropdown(
        id='category-dropdown',
        options=[{'label': cat, 'value': cat} for cat in movimenti.data['Categoria'].unique()],
        value=movimenti.data['Categoria'].unique().tolist(),
        multi=True
    ),
    dcc.Graph(id='movimenti-graph')
])

@app.callback(
    Output('movimenti-graph', 'figure'),
    Input('category-dropdown', 'value')
)
def update_graph(selected_categories):
    filtered_data = movimenti.data[movimenti.data['Categoria'].isin(selected_categories)]
    fig = px.histogram(filtered_data, x='Data contabile', y='Importo', color='Categoria',
                       title='Movimenti per Categoria nel Tempo', nbins=50)
    return fig

if __name__ == '__main__':
    app.run(debug=True)
