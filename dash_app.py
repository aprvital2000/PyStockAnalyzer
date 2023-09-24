import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input
from plotly.subplots import make_subplots

from analyse import analyze_symbol

app = Dash(__name__)
symbols_df = pd.read_json('securities.json')
symbols_df.sort_values(by=['ticker'], ascending=True, inplace=True)

app.layout = html.Div([
    html.H1(style={'textAlign': 'center'}),
    dcc.Dropdown(options=symbols_df['ticker'], value=symbols_df.iloc[0]['ticker'], id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])


@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(symbol):
    df = analyze_symbol(symbol)

    # Create figure with secondary y-axis
    fig = make_subplots(rows=10, cols=1, horizontal_spacing=0, vertical_spacing=0.03, print_grid=True,
                        shared_xaxes=True,
                        # x_title="Date",
                        row_heights=[200, 200, 200, 200, 200, 200, 200, 200, 200, 200],
                        row_titles=(
                        "Closing Price", "MACD", "ROC", "AROON", "RSI", "ADX", "B-BANDS", "CCI", "WILL-R", "STOCH"),
                        subplot_titles=("<b>Closing Price</b> - Buy at Green up arrow, Sell at Red down arrow",
                                        "<b>MACD</b> - Buy when red line crosses blue line upwards below 0, Sell when red line crosses blue line downwards below 0",
                                        "<b>Rate Of Change</b> - Buy when ROC crosses 0 upwards, Sell when ROC crosses 0 downwards",
                                        "<b>AROON</b> - Buy when AROON crosses 0 upwards, Sell when AROON crosses 0 downwards",
                                        "<b>Relative Strength Indicator</b> - Buy when RSI >=50, Strong Buy when RSI >=70, Sell when RSI <= 50, Strong Sell when RSI <= 30",
                                        "<b>Average Directional Index</b> - Buy/Sell when ADX >=25",
                                        "<b>Bollinger Bands</b> - Buy when blue line crosses lower band, Sell when blue line crosses upper band",
                                        "<b>CCI</b> - Buy when CCI <= -100, Sell when CCI >= 100",
                                        "<b>WILL-R</b> - Buy when WILLR <= -80, Sell when WILLR >= -20",
                                        "<b>STOCH</b> - Buy when STOCHk <= 20, Sell when STOCHk >= 80",
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
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACDh_12_26_9'], name="MACD Histogram", stackgroup='1',
                             marker=dict(color='#7F7F7F')), row=2, col=1)
    fig.add_hline(y=0, row=2, col=1, line_width=1)

    # ROC
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ROC_10'], name="ROC_10", stackgroup='2',
                             marker=dict(color='#636EFA')), row=3, col=1)
    fig.add_hline(y=0, row=3, col=1, line_width=1)

    # AROON
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['AROONOSC_14'], name="AROONOSC_14", stackgroup='3',
                             marker=dict(color='#636EFA')), row=4, col=1)
    fig.add_hline(y=0, row=4, col=1, line_width=1)

    # RSI
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI_14'], name="RSI_14", stackgroup='4',
                             marker=dict(color='#636EFA')), row=5, col=1)
    fig.add_hline(y=30, row=5, col=1, line_width=1, name='30')
    fig.add_hline(y=50, row=5, col=1, line_width=1, name='50')
    fig.add_hline(y=70, row=5, col=1, line_width=1, name='70')

    # ADX
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['ADX_14'], name="ADX_14", stackgroup='5', marker=dict(color='#636EFA')),
        row=6, col=1)
    fig.add_hline(y=30, row=6, col=1, line_width=1)
    fig.add_hline(y=70, row=6, col=1, line_width=1)

    # BBands
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['BBU_20_2.0'], name="BBU_20_2.0",
                             marker=dict(color='#FFA1FA')), row=7, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['BBL_20_2.0'], name="BBL_20_2.0",
                             marker=dict(color='#2ca02c')), row=7, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="close",
                             marker=dict(color='#636EFA')), row=7, col=1)

    # CCI
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['CCI_14_0.015'], name="CCI_14_0.015", stackgroup='6',
                             marker=dict(color='#636EFA')), row=8, col=1)
    fig.add_hline(y=100, row=8, col=1, line_width=1)
    fig.add_hline(y=-100, row=8, col=1, line_width=1)

    # WILLR
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['WILLR_14'], name="WILLR_14", stackgroup='7',
                             marker=dict(color='#636EFA')), row=9, col=1)
    fig.add_hline(y=-80, row=9, col=1, line_width=1)
    fig.add_hline(y=-20, row=9, col=1, line_width=1)

    # STOCH
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['STOCHk_14_3_3'], name="STOCHk_14_3_3",
                             marker=dict(color='#FFA1FA')), row=10, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['STOCHd_14_3_3'], name="STOCHd_14_3_3",
                             marker=dict(color='#636EFA')), row=10, col=1)
    fig.add_hline(y=80, row=10, col=1, line_width=1)
    fig.add_hline(y=20, row=10, col=1, line_width=1)

    fig.update_annotations(font_size=11)
    fig.update_layout(showlegend=False, height=1200, margin=dict(t=30, r=5, l=5, b=0))
    return fig


if __name__ == '__main__':
    app.run(debug=True)
