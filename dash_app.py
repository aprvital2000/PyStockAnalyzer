import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, callback, Output, Input
from plotly.subplots import make_subplots
import plotly.graph_objects as go

df2 = pd.DataFrame({"symbols": ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']})

app = Dash(__name__)

app.layout = html.Div([
    html.H1(style={'textAlign': 'center'}),
    dcc.Dropdown(df2.symbols.unique(), df2.symbols[0], id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])


@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    url = 'C:/Users/panumula/Downloads/data-analysis/{}-enriched-210923.csv'.format(value)
    print("URL => " + url)
    df1 = pd.read_csv(url)

    # Create figure with secondary y-axis
    fig = make_subplots(rows=4, cols=1, horizontal_spacing=0.01, vertical_spacing=0.01, print_grid=True,
                        shared_xaxes=True, x_title="Date", row_titles=("Cosing Price", "MACD", "AROON", "ROC"))

    # Add traces
    fig.add_trace(go.Scatter(x=df1['timestamp'], y=df1['close'], name="Cosing Price"), row=1, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df1['timestamp'], y=df1['MACD_12_26_9'], name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df1['timestamp'], y=df1['MACDs_12_26_9'], name="MACD Signal"), row=2, col=1)
    fig.add_trace(go.Bar(x=df1['timestamp'], y=df1['MACDh_12_26_9'], name="MACD Histogram"), row=2, col=1)
    fig.add_hline(y=0, row=2, col=1, line_width=1)

    # AROONOSC_14
    fig.add_trace(go.Scatter(x=df1['timestamp'], y=df1['AROONOSC_14'], name="AROONOSC_14"), row=3, col=1)
    fig.add_hline(y=0, row=3, col=1, line_width=1)

    fig.add_trace(go.Scatter(x=df1['timestamp'], y=df1['ROC_10'], name="ROC_10"), row=4, col=1)
    fig.add_hline(y=0, row=4, col=1, line_width=1)

    # fig.update_layout(title_text="Double Y Axis Example")
    fig.update_layout(height=800, showlegend=False, margin=dict(l=0, r=0, t=0, b=0), xaxis=dict(tickformat='%d-%b'))

    return fig

if __name__ == '__main__':
    app.run(debug=True)
