import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input
from plotly.subplots import make_subplots

from analyse import analyze_symbol

symbols_df = pd.DataFrame(
    {"symbols": ['SPY', 'DOW', 'MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TSLA']})

app = Dash(__name__)

app.layout = html.Div([
    html.H1(style={'textAlign': 'center'}),
    dcc.Dropdown(symbols_df.symbols.unique(), symbols_df.symbols[0], id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])


@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(symbol):
    df = analyze_symbol(symbol)

    # Create figure with secondary y-axis
    fig = make_subplots(rows=7, cols=1, horizontal_spacing=0, vertical_spacing=0.03, print_grid=True,
                        shared_xaxes=True,
                        # x_title="Date",
                        row_heights=[200, 200, 200, 200, 200, 200, 200],
                        row_titles=("Closing Price", "MACD", "ROC", "AROON", "RSI", "ADX", "B-BANDS"),
                        subplot_titles=("<b>Closing Price</b> - Buy at Green up arrow, Sell at Red down arrow",
                                        "<b>MACD</b> - Buy when red line crosses down blue line above 0, Sell when red line crosses up blue line below 0",
                                        "<b>Rate Of Change</b> - Buy when ROC crosses 0 upwards, Sell when ROC crosses 0 downwards",
                                        "<b>AROON</b> - Buy when AROON crosses 0 upwards, Sell when AROON crosses 0 downwards",
                                        "<b>Relative Strength Indicator</b> - Buy when RSI >=50, Strong Buy when RSI >=70, Sell when RSI <= 50, Strong Sell when RSI <= 30",
                                        "<b>Average Directional Index</b> - Buy/Sell when ADX >=25",
                                        "<b>Bollinger Bands</b> - Buy when blue line crosses lower band, Sell when blue line crosses upper band",
                                        )
                        )

    # Add traces
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Closing Price",
                             marker=dict(color='#636EFA')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd_buy_reco'], name="Buy", mode='markers',
                             marker=dict(color='#2ca02c', size=15, symbol='arrow', angle=0)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd_sell_reco'], name="Sell", mode='markers',
                             marker=dict(color='#EF553B', size=15, symbol='arrow', angle=180)), row=1, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD_12_26_9'], name="MACD",
                             marker=dict(color='#FFA1FA')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACDs_12_26_9'], name="MACD Signal",
                             marker=dict(color='#636EFA')), row=2, col=1)
    fig.add_trace(go.Bar(x=df['timestamp'], y=df['MACDh_12_26_9'], name="MACD Histogram",
                         marker=dict(color='#7F7F7F')), row=2, col=1)
    fig.add_hline(y=0, row=2, col=1, line_width=1)

    # ROC
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ROC_10'], name="ROC_10",
                             marker=dict(color='#636EFA')), row=3, col=1)
    fig.add_hline(y=0, row=3, col=1, line_width=1)

    # AROON
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['AROONOSC_14'], name="AROONOSC_14",
                             marker=dict(color='#636EFA')), row=4, col=1)
    fig.add_hline(y=0, row=4, col=1, line_width=1)

    # RSI
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI_14'], name="RSI_14",
                             marker=dict(color='#636EFA')), row=5, col=1)
    fig.add_hline(y=30, row=5, col=1, line_width=1, name='30')
    fig.add_hline(y=50, row=5, col=1, line_width=1, name='50')
    fig.add_hline(y=70, row=5, col=1, line_width=1, name='70')

    # ADX
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ADX_14'], name="ADX_14",
                             marker=dict(color='#636EFA')), row=6, col=1)
    fig.add_hline(y=30, row=6, col=1, line_width=1)
    fig.add_hline(y=70, row=6, col=1, line_width=1)

    # BBands
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['BBU_20_2.0'], name="BBU_20_2.0",
                             marker=dict(color='#FFA1FA')), row=7, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['BBL_20_2.0'], name="BBL_20_2.0",
                             marker=dict(color='#2ca02c')), row=7, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="close",
                             marker=dict(color='#636EFA')), row=7, col=1)

    fig.update_annotations(font_size=12)
    fig.update_layout(showlegend=False, height=800, margin=dict(t=30, r=5, l=5, b=0))
    return fig


if __name__ == '__main__':
    app.run(debug=True)
