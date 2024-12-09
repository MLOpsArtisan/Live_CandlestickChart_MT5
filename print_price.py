import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.subplots as sp
import MetaTrader5 as mt5
import pandas as pd
import os

# Available timeframes
TIMEFRAMES = {
    '1 Min': mt5.TIMEFRAME_M1,
    '5 Min': mt5.TIMEFRAME_M5,
    '15 Min': mt5.TIMEFRAME_M15,
    '1 Hour': mt5.TIMEFRAME_H1,
    '4 Hours': mt5.TIMEFRAME_H4
}

SYMBOL = "BTCUSD"
CSV_FILE = "price_data.csv"  # CSV file to store the data

# Initialize MetaTrader 5 connection
mt5.initialize()

def get_data(symbol, timeframe, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"Failed to retrieve data for {symbol}")
        return pd.DataFrame()  # Return empty DataFrame if there's an issue

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]

def save_to_csv(df, csv_file=CSV_FILE):
    # Append to existing CSV, or create new if it doesn't exist
    if not os.path.isfile(csv_file):
        df.to_csv(csv_file, index=False)
    else:
        df.to_csv(csv_file, mode='a', header=False, index=False)

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Checklist(
        id='volume-checkbox',
        options=[{'label': 'Show Volume', 'value': 'show_volume'}],
        value=['show_volume'],
        style={'margin': '10px'}
    ),
    dcc.Dropdown(
        id='timeframe-dropdown',
        options=[{'label': key, 'value': value} for key, value in TIMEFRAMES.items()],
        value=mt5.TIMEFRAME_M1,
        style={'width': '200px', 'margin-bottom': '10px'}
    ),
    dcc.Graph(
        id='live-candlestick-chart',
        style={'height': '90vh', 'overflow': 'hidden'},
        config={'displayModeBar': False}
    ),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,
        n_intervals=0
    )
], style={'width': '100vw', 'height': '100vh', 'overflow': 'hidden'})

@app.callback(
    Output('live-candlestick-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('timeframe-dropdown', 'value'),
     Input('volume-checkbox', 'value')]
)
def update_chart(n, selected_timeframe, volume_option):
    df = get_data(SYMBOL, selected_timeframe, count=100)

    if df.empty:
        return go.Figure()

    # Save data to CSV
    save_to_csv(df)

    # Determine if volume is enabled
    show_volume = 'show_volume' in volume_option
    volume_colors = ['green' if row['close'] > row['open'] else 'red' for index, row in df.iterrows()]

    if show_volume:
        fig = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.02)
    else:
        fig = sp.make_subplots(rows=1, cols=1)

    candlestick_trace = go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candlesticks",
        hoverinfo="x+y"
    )

    if show_volume:
        volume_trace = go.Bar(
            x=df['time'],
            y=df['tick_volume'],
            name="Volume",
            marker=dict(color=volume_colors),
            hoverinfo="x+y"
        )
        fig.add_trace(volume_trace, row=2, col=1)

    fig.add_trace(candlestick_trace, row=1, col=1)

    last_price = df['close'].iloc[-1]
    price_color = "green" if df['close'].iloc[-1] > df['close'].iloc[-2] else "red"

    fig.update_layout(
        title=f"Live Chart for {SYMBOL}",
        xaxis=dict(showgrid=True, gridcolor='DarkGray', showticklabels=True),
        yaxis=dict(showgrid=True, gridcolor='DarkGray', side="right", showticklabels=True),
        height=900 if show_volume else 600,
        margin=dict(l=0, r=80, t=50, b=0),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        plot_bgcolor='rgb(20, 24, 31)',
        paper_bgcolor='rgb(20, 24, 31)',
        font=dict(color="white"),
        hovermode='x unified',
    )

    fig.add_shape(
        type="line",
        x0=0, x1=1, y0=last_price, y1=last_price,
        xref="paper", yref="y",
        line=dict(color=price_color, width=2, dash="dash")
    )

    fig.update_yaxes(
        tickformat=".2f",
        showgrid=True,
        gridcolor='DarkGray',
        side="right"
    )

    fig.add_annotation(
        xref="paper", yref="y",
        x=1.035, y=last_price,
        text=f"{last_price:.2f}",
        showarrow=False,
        font=dict(color="white", size=12, family="Arial"),
        bgcolor=price_color,
        bordercolor="white",
        align="center",
        borderpad=4
    )

    fig.update_xaxes(showline=True, linecolor='DarkGray', linewidth=1)
    fig.update_yaxes(showline=True, linecolor='DarkGray', linewidth=1)
    fig.update_xaxes(tickformat="%H:%M", matches='x')
    fig.update_yaxes(showticklabels=True, title_text="")
    if show_volume:
        fig.update_yaxes(showticklabels=True, title_text="", row=2, col=1)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)