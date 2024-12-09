import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.subplots as sp
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

# Initialize MetaTrader 5 connection
if not mt5.initialize():
    print("Failed to initialize MetaTrader 5")
    exit()
else:
    print("MetaTrader 5 initialized successfully.")

# Constants
SYMBOL = "BTCUSD"
TIMEFRAMES = {
    '1 Min': mt5.TIMEFRAME_M1,
    '5 Min': mt5.TIMEFRAME_M5,
    '1 Hour': mt5.TIMEFRAME_H1,
    '4 Hours': mt5.TIMEFRAME_H4,
    '1 Day': mt5.TIMEFRAME_D1
}
INITIAL_CANDLES = 50  # Number of candles to load initially


# Function to fetch data
def fetch_data(symbol, timeframe, start_date=None, count=None):
    try:
        print(f"Fetching data for {symbol} at {timeframe} timeframe...")
        if start_date:
            rates = mt5.copy_rates_range(symbol, timeframe, start_date, datetime.now())
        elif count:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        else:
            rates = None

        if rates is None or len(rates) == 0:
            print(f"Failed to retrieve data for {symbol} at {timeframe} timeframe")
            return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"Data fetched successfully: {len(df)} rows")
        return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])


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
    html.Button('Load Data', id='load-data-btn', n_clicks=0),
    dcc.Store(id='stored-data'),  # Store component for persistent data
    dcc.Graph(
        id='live-candlestick-chart',
        style={'height': '90vh'},
        config={'displayModeBar': True, 'scrollZoom': True, 'modeBarButtonsToAdd': ['resetScale2d']}
    ),
    dcc.Interval(id='interval-component', interval=1 * 1000, n_intervals=0)  # Update every second
], style={'width': '100vw', 'height': '100vh', 'overflow': 'hidden'})


# Callback to load historical data based on selected timeframe
@app.callback(
    Output('stored-data', 'data'),
    [Input('load-data-btn', 'n_clicks')],
    [State('timeframe-dropdown', 'value')]
)
def load_historical_data(n_clicks, selected_timeframe):
    print(f"Loading historical data with {n_clicks} clicks on timeframe {selected_timeframe}")

    # Adjust the number of candles fetched based on the selected timeframe
    if selected_timeframe == mt5.TIMEFRAME_M1:
        count = 2880  # Approx. 2 days for 1-minute timeframe
    elif selected_timeframe == mt5.TIMEFRAME_H1:
        count = 1440  # Approx. 2 months for 1-hour timeframe
    elif selected_timeframe == mt5.TIMEFRAME_D1:
        count = 60  # 2 months for daily timeframe
    else:
        count = INITIAL_CANDLES  # Fallback

    df = fetch_data(SYMBOL, selected_timeframe, count=count)
    if df.empty:
        print("Warning: No data retrieved for the selected timeframe.")
    return df.to_dict('records') if not df.empty else []


# Callback to update chart with real-time data and manage user view
@app.callback(
    Output('live-candlestick-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('volume-checkbox', 'value'),
     Input('stored-data', 'data')],
    [State('timeframe-dropdown', 'value')]
)
def update_chart(n_intervals, volume_option, stored_data, selected_timeframe):
    print(f"Updating chart at interval {n_intervals} with timeframe {selected_timeframe}")

    if not stored_data:
        print("No data available in stored-data.")
        fig = go.Figure()
        fig.update_layout(title="No data available", xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        return fig

    # Convert stored data back to DataFrame
    df = pd.DataFrame(stored_data)
    df['time'] = pd.to_datetime(df['time'])  # Ensure 'time' column is in datetime format

    # Fetch the latest candle and check for updates
    latest_data = fetch_data(SYMBOL, selected_timeframe, count=1)
    if not latest_data.empty and not df.empty:
        latest_data['time'] = pd.to_datetime(latest_data['time'])  # Ensure 'time' is datetime
        # Update the last candle if the timestamp matches; otherwise, append a new one
        if latest_data['time'].iloc[0] > df['time'].iloc[-1]:
            df = pd.concat([df, latest_data], ignore_index=True)
        else:
            df.iloc[-1] = latest_data.iloc[0]

    df = df[-INITIAL_CANDLES:]

    show_volume = 'show_volume' in volume_option
    volume_colors = ['green' if row['close'] > row['open'] else 'red' for index, row in df.iterrows()]

    fig = sp.make_subplots(
        rows=2 if show_volume else 1, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3] if show_volume else [1],
        vertical_spacing=0.02
    )

    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candlesticks"
    ), row=1, col=1)

    if show_volume:
        fig.add_trace(go.Bar(
            x=df['time'],
            y=df['tick_volume'],
            name="Volume",
            marker=dict(color=volume_colors)
        ), row=2, col=1)

    fig.update_layout(
        title="Live BTC/USD Chart",
        xaxis_rangeslider_visible=False,
        xaxis=dict(range=[df['time'].iloc[0], df['time'].iloc[-1]]),
        yaxis=dict(showgrid=True, gridcolor='DarkGray'),
        plot_bgcolor='rgb(20, 24, 31)',
        paper_bgcolor='rgb(20, 24, 31)',
        font=dict(color="white")
    )

    last_price = df['close'].iloc[-1]
    price_color = "green" if df['close'].iloc[-1] > df['close'].iloc[-2] else "red"
    fig.add_shape(
        type="line",
        x0=0, x1=1, y0=last_price, y1=last_price,
        xref="paper", yref="y",
        line=dict(color=price_color, width=2, dash="dash")
    )

    return fig


# Callback to update the interval based on the selected timeframe
@app.callback(
    Output('interval-component', 'interval'),
    [Input('timeframe-dropdown', 'value')]
)
def update_interval(selected_timeframe):
    print(f"Selected timeframe for interval update: {selected_timeframe}")
    if selected_timeframe == mt5.TIMEFRAME_M1:
        return 60 * 1000  # 1 minute in milliseconds
    elif selected_timeframe == mt5.TIMEFRAME_H1:
        return 60 * 60 * 1000  # 1 hour in milliseconds
    elif selected_timeframe == mt5.TIMEFRAME_D1:
        return 24 * 60 * 60 * 1000  # 1 day in milliseconds
    else:
        return 1 * 1000  # Default to 1 second for testing


if __name__ == '__main__':
    app.run_server(debug=True)
