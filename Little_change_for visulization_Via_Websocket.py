import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.subplots as sp
import websocket
import threading
import pandas as pd
import json
import requests
import time

# Binance WebSocket URL template
BINANCE_SOCKET_URL_TEMPLATE = "wss://stream.binance.com:9443/ws/{}@kline_{}"
BINANCE_REST_API_URL_TEMPLATE = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit=50"

# Initialize Dash app
app = dash.Dash(__name__)

# Shared DataFrame to store live prices
live_data = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])

# Default symbol and timeframe
SYMBOL = "btcusdt"
DEFAULT_TIMEFRAME = "1m"  # Default to 1-minute candlesticks

# Global WebSocket connection and lock
websocket_connection = None
websocket_lock = threading.Lock()


def fetch_historical_data(symbol, interval, limit=50):
    """
    Fetch the historical data for the given symbol and interval from Binance's REST API.
    This data will be used to initialize the chart.
    """
    url = BINANCE_REST_API_URL_TEMPLATE.format(symbol.upper(), interval)
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        historical_data = []
        for entry in data:
            historical_data.append({
                'time': pd.to_datetime(entry[0], unit='ms'),
                'open': float(entry[1]),
                'high': float(entry[2]),
                'low': float(entry[3]),
                'close': float(entry[4]),
                'volume': float(entry[5]),
            })
        return pd.DataFrame(historical_data)
    else:
        print("Error fetching historical data")
        return pd.DataFrame()


def start_websocket(symbol, interval):
    """
    Start a WebSocket connection for the given symbol and interval.
    """
    global websocket_connection, live_data

    with websocket_lock:
        # Fetch historical data and set initial live_data
        live_data = fetch_historical_data(symbol, interval)

        # Close any existing WebSocket connection
        if websocket_connection:
            try:
                websocket_connection.close()
                time.sleep(1)  # Ensure the connection is fully closed
            except Exception as e:
                print(f"Error while closing WebSocket: {e}")

        # WebSocket URL for the selected symbol and interval
        url = BINANCE_SOCKET_URL_TEMPLATE.format(symbol, interval)

        def on_message(ws, message):
            global live_data
            try:
                data = json.loads(message)
                kline = data['k']

                # Extract relevant kline data
                row = {
                    'time': pd.to_datetime(kline['t'], unit='ms'),
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v']),
                }

                # Append the new row to the live_data DataFrame
                live_data = pd.concat([live_data, pd.DataFrame([row])]).tail(500)  # Keep last 500 rows
            except Exception as e:
                print(f"Error processing WebSocket message: {e}")

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket Closed for {symbol} at {interval} interval")

        def on_open(ws):
            print(f"WebSocket Connection Opened for {symbol} at {interval} interval")

        # Start the WebSocket connection
        websocket_connection = websocket.WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        websocket_connection.on_open = on_open

        # Run WebSocket in a separate thread
        websocket_thread = threading.Thread(target=websocket_connection.run_forever, daemon=True)
        websocket_thread.start()


# Start the WebSocket for the default timeframe
start_websocket(SYMBOL, DEFAULT_TIMEFRAME)

# Dash Layout
app.layout = html.Div([
    dcc.Dropdown(
        id='timeframe-dropdown',
        options=[
            {'label': '1 Second', 'value': '1s'},
            {'label': '1 Minute', 'value': '1m'},
            {'label': '15 Minutes', 'value': '15m'},
            {'label': '1 Hour', 'value': '1h'},
            {'label': '4 Hours', 'value': '4h'},
            {'label': '1 Day', 'value': '1d'}
        ],
        value=DEFAULT_TIMEFRAME,
        style={'width': '200px', 'margin-bottom': '10px'}
    ),
    dcc.Graph(
        id='live-candlestick-chart',
        style={'width': '100%', 'height': '100%'},
        config={
            'displayModeBar': True,  # Enable mode bar for zoom and pan
            'scrollZoom': True  # Enable mouse scroll zooming
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=1000,  # Update every 1 second
        n_intervals=0
    )
], style={
    'width': '100vw', 'height': '100vh', 'overflow': 'hidden',
    'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center'
})


# Update chart callback
@app.callback(
    Output('live-candlestick-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('timeframe-dropdown', 'value')]
)
def update_chart(n, selected_timeframe):
    global live_data

    # Update WebSocket connection if timeframe changes
    if websocket_connection and websocket_connection.url != BINANCE_SOCKET_URL_TEMPLATE.format(SYMBOL,
                                                                                               selected_timeframe):
        start_websocket(SYMBOL, selected_timeframe)

    if live_data.empty:
        return go.Figure()

    # Set up the candlestick trace
    candlestick_trace = go.Candlestick(
        x=live_data['time'],
        open=live_data['open'],
        high=live_data['high'],
        low=live_data['low'],
        close=live_data['close'],
        name="Candlesticks"
    )

    # Set up the layout
    layout = go.Layout(
        title=f"Live Chart for {SYMBOL.upper()} ({selected_timeframe})",
        xaxis=dict(showgrid=True, gridcolor='DarkGray', type='category'),
        yaxis=dict(showgrid=True, gridcolor='DarkGray', side="right"),
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_rangeslider_visible=True,  # Enable range slider for backtracking
        plot_bgcolor='rgb(20, 24, 31)',
        paper_bgcolor='rgb(20, 24, 31)',
        font=dict(color="white"),
        hovermode='x unified'
    )

    return go.Figure(data=[candlestick_trace], layout=layout)


if __name__ == '__main__':
    app.run_server(debug=True)
