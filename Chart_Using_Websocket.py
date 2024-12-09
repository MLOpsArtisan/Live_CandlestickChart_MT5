import asyncio
import websockets
import threading
import json
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.subplots as sp
import pandas as pd
from datetime import datetime
import time

# Initialize Dash app
app = dash.Dash(__name__)

# WebSocket URI for live BTC market data (Binance)
uri = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"  # Replace with your WebSocket URI

# Buffer to store live data from the WebSocket
live_data_buffer = []

# Function to get live data from WebSocket and print it
async def live_data():
    global live_data_buffer
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connection established.")
            while True:
                # Receive the data from WebSocket
                data = await websocket.recv()
                parsed_data = json.loads(data)

                # Extract relevant candlestick data
                kline = parsed_data['k']
                open_time = datetime.utcfromtimestamp(kline['t'] / 1000)  # Convert milliseconds to seconds
                open_price = float(kline['o'])
                high_price = float(kline['h'])
                low_price = float(kline['l'])
                close_price = float(kline['c'])
                volume = float(kline['v'])

                # Store the parsed data in the live data buffer
                live_data_buffer.append({
                    'time': open_time,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'tick_volume': volume
                })

                # Print the last few entries in the buffer for monitoring
                if len(live_data_buffer) % 10 == 0:
                    df = pd.DataFrame(live_data_buffer)
                    df['time'] = pd.to_datetime(df['time'], errors='coerce')  # Ensure time is in datetime format
                    print(df.tail())  # Print last few rows

                # Limit the buffer size to 100 data points
                if len(live_data_buffer) > 100:
                    live_data_buffer = live_data_buffer[-100:]

                time.sleep(1)

    except Exception as e:
        print(f"Error occurred: {e}")
        await asyncio.sleep(1)  # Retry connection on error

# Start the WebSocket connection in a separate thread
def start_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(live_data())

# Start WebSocket listener in the background
threading.Thread(target=start_websocket, daemon=True).start()

# Layout of Dash app
app.layout = html.Div([
    dcc.Checklist(
        id='volume-checkbox',
        options=[{'label': 'Show Volume', 'value': 'show_volume'}],
        value=['show_volume'],
        style={'margin': '10px'}
    ),
    dcc.Dropdown(
        id='timeframe-dropdown',
        options=[{'label': '1 Minute', 'value': '1m'}],
        value='1m',  # Default timeframe
        style={'width': '200px', 'margin-bottom': '10px'}
    ),
    dcc.Graph(
        id='live-candlestick-chart',
        style={'width': '100%', 'height': '100%'},
        config={'displayModeBar': False}  # Hide Plotly mode bar for a cleaner look
    ),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # Update every 1 second
        n_intervals=0
    )
], style={
    'width': '100vw',
    'height': '100vh',
    'overflow': 'hidden',
    'display': 'flex',
    'flexDirection': 'column',
    'alignItems': 'center',
    'justifyContent': 'center'
})

# Callback to update the chart with new data
@app.callback(
    Output('live-candlestick-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('timeframe-dropdown', 'value'),
     Input('volume-checkbox', 'value')]
)
def update_chart(n, selected_timeframe, volume_option):
    # Check if there is enough data
    if len(live_data_buffer) == 0:
        print("No data available for chart update.")
        return go.Figure()  # Return an empty figure if no data

    # Convert live data buffer into DataFrame
    df = pd.DataFrame(live_data_buffer)
    df['time'] = pd.to_datetime(df['time'], errors='coerce')  # Ensure time is in datetime format
    df.dropna(subset=['time'], inplace=True)  # Drop rows with invalid time

    # Ensure that there is data in the last 100 data points
    if df.empty:
        print("Data is empty, skipping chart update.")
        return go.Figure()  # Avoid returning an empty figure

    # Debugging the incoming data
    print("Data to plot:")
    print(df.tail())

    # Determine if volume should be shown
    show_volume = 'show_volume' in volume_option

    # Define colors for volume based on candle direction
    volume_colors = ['green' if row['close'] > row['open'] else 'red' for _, row in df.iterrows()]

    # Create figure with subplots (volume subplot if enabled)
    if show_volume:
        fig = sp.make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.02
        )
    else:
        fig = sp.make_subplots(
            rows=1, cols=1
        )

    # Create candlestick trace
    candlestick_trace = go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candlesticks",
        increasing=dict(line=dict(color='green')),  # Green for upward movement
        decreasing=dict(line=dict(color='red')),   # Red for downward movement
        wickwidth=1,  # Set wick width for clearer candlesticks
        hoverinfo="x+y"  # Show crosshair with date and price on hover
    )

    # Create volume bar chart trace if volume is enabled
    if show_volume:
        volume_trace = go.Bar(
            x=df['time'],
            y=df['tick_volume'],
            name="Volume",
            marker=dict(color=volume_colors),
            hoverinfo="x+y"  # Display volume information on hover
        )
        fig.add_trace(volume_trace, row=2, col=1)

    # Add candlestick trace to the figure
    fig.add_trace(candlestick_trace, row=1, col=1)

    # Layout for styling
    fig.update_layout(
        title="Live Market Data",
        xaxis_title="Time",
        yaxis_title="Price",
        plot_bgcolor='rgb(20, 20, 20)',  # Dark background
        paper_bgcolor='rgb(20, 20, 20)',  # Dark paper background
        font=dict(color='white'),  # White text for contrast
        hovermode="x unified",  # Unified hover mode for better UX
        xaxis=dict(
            showgrid=True,
            gridcolor='DarkGray',
            showline=True,
            linecolor='white',
            tickformat="%H:%M",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='DarkGray',
            side="right",  # Display y-axis on the right
        ),
        showlegend=True
    )

    # Update y-axis range for volume (if enabled)
    if show_volume:
        fig.update_yaxes(range=[0, df['tick_volume'].max() * 1.2], row=2, col=1)

    return fig

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
