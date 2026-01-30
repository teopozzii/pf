import pandas as pd
import plotly.express as px

def category_graph(filtered_data):
    return px.histogram(
        filtered_data,
        x='Data valuta',
        y='Importo',
        color='Categoria',
        title='Movimenti per Categoria nel Tempo',
        nbins=100
    )

def cumulative_graph(filtered_data):
    filtered_data['Cumulative'] = filtered_data.groupby('Categoria')['Importo'].cumsum()
    fig = px.line(
        filtered_data,
        x='Data valuta',
        y='Cumulative',
        color='Categoria',
        title='Spesa Cumulata per Categoria nel Tempo'
    )
    return fig