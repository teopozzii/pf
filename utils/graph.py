import plotly.express as px
from utils.config import CONFIG

def category_graph(user, filtered_data):
    return px.histogram(
        filtered_data,
        x=CONFIG[user]["headers"]["date"],
        y=CONFIG[user]["headers"]["value"],
        color=CONFIG[user]["headers"]["category"],
        title='Movimenti per Categoria nel Tempo',
        nbins=100
    )

def cumulative_graph(user, filtered_data):
    filtered_data['Cumulative'] = filtered_data.groupby(CONFIG[user]["headers"]["category"])[CONFIG[user]["headers"]["value"]].cumsum()
    fig = px.line(
        filtered_data,
        x=CONFIG[user]["headers"]["date"],
        y='Cumulative',
        color=CONFIG[user]["headers"]["category"],
        title='Spesa Cumulata per Categoria nel Tempo'
    )
    return fig
