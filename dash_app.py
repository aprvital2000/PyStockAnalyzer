import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Output, Input, no_update, Patch
from plotly.subplots import make_subplots

from analyse import analyze_symbol

DARK_BG  = '#0d1117'
PANEL_BG = '#161b22'
BORDER   = '#30363d'
TEXT     = '#e6edf3'
MUTED    = '#8b949e'
BLUE     = '#58a6ff'
GREEN    = '#3fb950'
RED      = '#f85149'
PURPLE   = '#bc8cff'
ORANGE   = '#d29922'

GRAPH_CONFIG = dict(
    displayModeBar=True,
    scrollZoom=False,
    modeBarButtonsToRemove=['select2d', 'lasso2d'],
)

SPIKE_STYLE = dict(
    showspikes=True,
    spikecolor='rgba(220,220,220,0.6)',
    spikethickness=1,
    spikedash='solid',
    spikemode='across',
    spikesnap='cursor',
)

XAXIS_STYLE = dict(
    showgrid=True, gridcolor=BORDER, gridwidth=1,
    zeroline=False, rangeslider_visible=False,
    **SPIKE_STYLE,
)

app = Dash(__name__, title='Stock Analyzer')
symbols_df = pd.read_json('securities.json')
symbols_df.sort_values(by=['ticker'], ascending=True, inplace=True)

app.layout = html.Div(
    style={'backgroundColor': DARK_BG, 'minHeight': '100vh',
           'fontFamily': "'Inter', 'Segoe UI', sans-serif"},
    children=[
        # ── Header (sticky) ────────────────────────────────────────────────
        html.Div(
            style={
                'position': 'sticky', 'top': '0', 'zIndex': 200,
                'backgroundColor': PANEL_BG,
                'borderBottom': f'1px solid {BORDER}',
                'padding': '14px 24px',
                'display': 'flex', 'alignItems': 'center', 'gap': '20px',
            },
            children=[
                html.Span('📈', style={'fontSize': '24px'}),
                html.H1('Stock Analyzer',
                        style={'color': TEXT, 'margin': 0, 'fontSize': '20px',
                               'fontWeight': '600', 'letterSpacing': '-0.3px'}),
                dcc.Dropdown(
                    id='dropdown-selection',
                    options=[{'label': f"{r[1]['ticker']}  —  {r[1]['name']}",
                              'value': r[1]['ticker']}
                             for r in symbols_df.iterrows()],
                    value=symbols_df.iloc[0]['ticker'],
                    searchable=True, clearable=False,
                    style={
                        'width': '400px', 'backgroundColor': DARK_BG,
                        'color': TEXT, 'border': f'1px solid {BORDER}',
                        'borderRadius': '6px', 'fontSize': '14px',
                    }
                ),
            ]
        ),

        # ── Price chart (sticky below header) ──────────────────────────────
        html.Div(
            style={
                'position': 'sticky', 'top': '53px', 'zIndex': 100,
                'backgroundColor': DARK_BG,
                'borderBottom': f'1px solid {BORDER}',
            },
            children=[
                dcc.Graph(
                    id='graph-price',
                    config=GRAPH_CONFIG,
                    style={'backgroundColor': DARK_BG},
                )
            ]
        ),

        # ── Indicator charts (scrollable) ──────────────────────────────────
        dcc.Graph(
            id='graph-indicators',
            config=GRAPH_CONFIG,
            style={'backgroundColor': DARK_BG},
        ),

        dcc.Store(id='hover-sync-store'),
    ]
)


def _apply_common_layout(fig, title_text, n_xaxes):
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=DARK_BG,
        plot_bgcolor=PANEL_BG,
        margin=dict(t=40, r=20, l=60, b=10),
        showlegend=True,
        legend=dict(
            orientation='h', y=1.02, x=1, xanchor='right', yanchor='bottom',
            font=dict(size=11, color=TEXT), bgcolor='rgba(0,0,0,0)',
        ),
        title=dict(text=title_text, font=dict(size=15, color=TEXT),
                   x=0.005, xanchor='left'),
        font=dict(color=TEXT, size=11),
        hovermode='x unified',
    )
    fig.update_annotations(font=dict(size=11, color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=BORDER, gridwidth=1, zeroline=False)
    for i in range(1, n_xaxes + 1):
        axis = 'xaxis' if i == 1 else f'xaxis{i}'
        fig.update_layout(**{axis: XAXIS_STYLE})


@app.callback(
    Output('graph-price', 'figure'),
    Output('graph-indicators', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graphs(symbol):
    name_map = {r[1]['ticker']: r[1]['name'] for r in symbols_df.iterrows()}
    name = name_map.get(symbol, '')
    df = analyze_symbol(symbol, name)

    title = f'<b>{symbol}</b>  <span style="color:{MUTED};font-weight:normal">{name}</span>'

    # ── Price figure ───────────────────────────────────────────────────────
    price_fig = go.Figure()
    price_fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='Price',
        increasing=dict(line=dict(color=GREEN, width=1), fillcolor=GREEN),
        decreasing=dict(line=dict(color=RED,   width=1), fillcolor=RED),
        showlegend=False,
    ))
    price_fig.add_trace(go.Scatter(
        x=df['Date'], y=df['macd_buy_reco'], name='Buy', mode='markers+text',
        text='B', textposition='top center',
        textfont=dict(color='#00ff88', size=9, family='monospace'),
        marker=dict(color='#00ff88', size=16, symbol='triangle-up',
                    line=dict(color='white', width=1.5)),
    ))
    price_fig.add_trace(go.Scatter(
        x=df['Date'], y=df['macd_sell_reco'], name='Sell', mode='markers+text',
        text='S', textposition='bottom center',
        textfont=dict(color='#ff6b35', size=9, family='monospace'),
        marker=dict(color='#ff6b35', size=16, symbol='triangle-down',
                    line=dict(color='white', width=1.5)),
    ))
    _apply_common_layout(price_fig, title, n_xaxes=1)
    price_fig.update_layout(height=300)

    # ── Indicators figure ──────────────────────────────────────────────────
    ind_heights = [150, 120, 120, 120, 130, 180, 120, 120, 140]
    ind_subtitles = (
        'MACD  ·  cross above/below zero line',
        'Rate of Change  ·  cross above/below 0',
        'Aroon Oscillator  ·  cross above/below 0',
        'RSI  ·  overbought ≥ 70  ·  oversold ≤ 30',
        'ADX  ·  trend strength ≥ 25',
        'Bollinger Bands  ·  price vs upper / lower band',
        'CCI  ·  overbought ≥ 100  ·  oversold ≤ −100',
        'Williams %R  ·  overbought ≥ −20  ·  oversold ≤ −80',
        'Stochastic  ·  overbought ≥ 80  ·  oversold ≤ 20',
    )
    ind_fig = make_subplots(
        rows=9, cols=1, shared_xaxes=True,
        vertical_spacing=0.018, row_heights=ind_heights,
        subplot_titles=ind_subtitles,
    )

    # MACD
    hist_colors = [GREEN if v >= 0 else RED for v in df['MACDh_12_26_9'].fillna(0)]
    ind_fig.add_trace(go.Bar(x=df['Date'], y=df['MACDh_12_26_9'], name='Histogram',
                             marker_color=hist_colors, opacity=0.55, showlegend=False), row=1, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD_12_26_9'], name='MACD',
                                 line=dict(color=PURPLE, width=1.5)), row=1, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['MACDs_12_26_9'], name='Signal',
                                 line=dict(color=ORANGE, width=1.5)), row=1, col=1)
    ind_fig.add_hline(y=0, row=1, col=1, line=dict(color=MUTED, width=1, dash='dot'))

    # ROC
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['ROC_10'], name='ROC',
                                 line=dict(color=BLUE, width=1.5),
                                 fill='tozeroy', fillcolor='rgba(88,166,255,0.08)',
                                 showlegend=False), row=2, col=1)
    ind_fig.add_hline(y=0, row=2, col=1, line=dict(color=MUTED, width=1, dash='dot'))

    # Aroon
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['AROONOSC_14'], name='Aroon Osc',
                                 line=dict(color=BLUE, width=1.5),
                                 fill='tozeroy', fillcolor='rgba(88,166,255,0.08)',
                                 showlegend=False), row=3, col=1)
    ind_fig.add_hline(y=0, row=3, col=1, line=dict(color=MUTED, width=1, dash='dot'))

    # RSI
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI_14'], name='RSI',
                                 line=dict(color=BLUE, width=1.5), showlegend=False), row=4, col=1)
    ind_fig.add_hrect(y0=70, y1=100, row=4, col=1, fillcolor=RED,   opacity=0.07, line_width=0)
    ind_fig.add_hrect(y0=0,  y1=30,  row=4, col=1, fillcolor=GREEN, opacity=0.07, line_width=0)
    ind_fig.add_hline(y=70, row=4, col=1, line=dict(color=RED,   width=1, dash='dash'))
    ind_fig.add_hline(y=30, row=4, col=1, line=dict(color=GREEN, width=1, dash='dash'))

    # ADX
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['ADX_14'], name='ADX',
                                 line=dict(color=ORANGE, width=1.5)), row=5, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['DMP_14'], name='+DMI',
                                 line=dict(color=GREEN, width=1, dash='dot')), row=5, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['DMN_14'], name='−DMI',
                                 line=dict(color=RED,   width=1, dash='dot')), row=5, col=1)
    ind_fig.add_hline(y=25, row=5, col=1, line=dict(color=MUTED, width=1, dash='dash'))

    # Bollinger Bands
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['BBU_20_2.0_2.0'], name='BB Upper',
                                 line=dict(color=RED,   width=1, dash='dot')), row=6, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['BBL_20_2.0_2.0'], name='BB Lower',
                                 line=dict(color=GREEN, width=1, dash='dot'),
                                 fill='tonexty', fillcolor='rgba(88,166,255,0.06)'), row=6, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Close',
                                 line=dict(color=BLUE, width=1.5), showlegend=False), row=6, col=1)

    # CCI
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['CCI_14_0.015'], name='CCI',
                                 line=dict(color=BLUE, width=1.5), showlegend=False), row=7, col=1)
    ind_fig.add_hrect(y0=100,  y1=400,  row=7, col=1, fillcolor=RED,   opacity=0.07, line_width=0)
    ind_fig.add_hrect(y0=-400, y1=-100, row=7, col=1, fillcolor=GREEN, opacity=0.07, line_width=0)
    ind_fig.add_hline(y= 100, row=7, col=1, line=dict(color=RED,   width=1, dash='dash'))
    ind_fig.add_hline(y=-100, row=7, col=1, line=dict(color=GREEN, width=1, dash='dash'))

    # Williams %R
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['WILLR_14'], name='Williams %R',
                                 line=dict(color=BLUE, width=1.5), showlegend=False), row=8, col=1)
    ind_fig.add_hrect(y0=-20,  y1=0,    row=8, col=1, fillcolor=RED,   opacity=0.07, line_width=0)
    ind_fig.add_hrect(y0=-100, y1=-80,  row=8, col=1, fillcolor=GREEN, opacity=0.07, line_width=0)
    ind_fig.add_hline(y=-20, row=8, col=1, line=dict(color=RED,   width=1, dash='dash'))
    ind_fig.add_hline(y=-80, row=8, col=1, line=dict(color=GREEN, width=1, dash='dash'))

    # Stochastic
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['STOCHk_14_3_3'], name='%K',
                                 line=dict(color=PURPLE, width=1.5)), row=9, col=1)
    ind_fig.add_trace(go.Scatter(x=df['Date'], y=df['STOCHd_14_3_3'], name='%D',
                                 line=dict(color=ORANGE, width=1.5)), row=9, col=1)
    ind_fig.add_hrect(y0=80,  y1=100, row=9, col=1, fillcolor=RED,   opacity=0.07, line_width=0)
    ind_fig.add_hrect(y0=0,   y1=20,  row=9, col=1, fillcolor=GREEN, opacity=0.07, line_width=0)
    ind_fig.add_hline(y=80, row=9, col=1, line=dict(color=RED,   width=1, dash='dash'))
    ind_fig.add_hline(y=20, row=9, col=1, line=dict(color=GREEN, width=1, dash='dash'))

    _apply_common_layout(ind_fig, '', n_xaxes=9)
    ind_fig.update_layout(height=sum(ind_heights) + 80, title=None)

    return price_fig, ind_fig


@app.callback(
    Output('graph-indicators', 'figure', allow_duplicate=True),
    Input('graph-price', 'relayoutData'),
    prevent_initial_call=True,
)
def sync_indicators_range(relayout):
    if not relayout:
        return no_update
    patched = Patch()
    if 'xaxis.range[0]' in relayout:
        patched['layout']['xaxis']['range'] = [relayout['xaxis.range[0]'],
                                               relayout['xaxis.range[1]']]
        patched['layout']['xaxis']['autorange'] = False
    elif relayout.get('xaxis.autorange'):
        patched['layout']['xaxis']['autorange'] = True
    else:
        return no_update
    return patched


@app.callback(
    Output('graph-price', 'figure', allow_duplicate=True),
    Input('graph-indicators', 'relayoutData'),
    prevent_initial_call=True,
)
def sync_price_range(relayout):
    if not relayout:
        return no_update
    patched = Patch()
    if 'xaxis.range[0]' in relayout:
        patched['layout']['xaxis']['range'] = [relayout['xaxis.range[0]'],
                                               relayout['xaxis.range[1]']]
        patched['layout']['xaxis']['autorange'] = False
    elif relayout.get('xaxis.autorange'):
        patched['layout']['xaxis']['autorange'] = True
    else:
        return no_update
    return patched


CROSSHAIR_SHAPE = """{
    type: 'line',
    x0: x, x1: x,
    y0: 0, y1: 1,
    xref: 'x', yref: 'paper',
    line: {color: 'rgba(220,220,220,0.55)', width: 1}
}"""

app.clientside_callback(
    f"""
    function(priceHover, indicatorsHover) {{
        var ctx = window.dash_clientside.callback_context;
        if (!ctx || !ctx.triggered || !ctx.triggered.length)
            return window.dash_clientside.no_update;

        var triggeredId = ctx.triggered[0].prop_id;
        var hoverData   = triggeredId.includes('price') ? priceHover : indicatorsHover;
        var targetId    = triggeredId.includes('price') ? 'graph-indicators' : 'graph-price';

        var shapes = [];
        if (hoverData && hoverData.points && hoverData.points.length) {{
            var x = hoverData.points[0].x;
            shapes = [{CROSSHAIR_SHAPE}];
        }}

        var target = document.getElementById(targetId);
        if (target && target._fullLayout !== undefined)
            Plotly.relayout(target, {{'shapes': shapes}});

        return window.dash_clientside.no_update;
    }}
    """,
    Output('hover-sync-store', 'data'),
    Input('graph-price', 'hoverData'),
    Input('graph-indicators', 'hoverData'),
    prevent_initial_call=True,
)


if __name__ == '__main__':
    app.run(debug=True)
