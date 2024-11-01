import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.subplots as sp
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

# Available timeframes
TIMEFRAMES = {
    '1 Min': mt5.TIMEFRAME_M1,
    '5 Min': mt5.TIMEFRAME_M5,
    '15 Min': mt5.TIMEFRAME_M15,
    '1 Hour': mt5.TIMEFRAME_H1,
    '4 Hours': mt5.TIMEFRAME_H4
}

SYMBOL = "BTCUSD"  # You can change this to any other symbol

# Initialize MetaTrader 5 connection
mt5.initialize()

# Load the latest 50 candles initially
INITIAL_CANDLES = 50


def get_data(symbol, timeframe, start_date=None, count=None):
    if start_date:
        # Load data from a specified start date up to now
        rates = mt5.copy_rates_range(symbol, timeframe, start_date, datetime.now())
    elif count:
        # Load the last 'count' candles
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    else:
        rates = None

    if rates is None or len(rates) == 0:
        print(f"Failed to retrieve data for {symbol}")
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]


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
    dcc.DatePickerSingle(
        id='start-date-picker',
        min_date_allowed=datetime.now() - timedelta(days=365),
        max_date_allowed=datetime.now(),
        initial_visible_month=datetime.now(),
        display_format='YYYY-MM-DD',
        style={'margin-bottom': '10px'}
    ),
    html.Button('Load Data from Date', id='load-date-btn', n_clicks=0),
    dcc.Store(id='stored-data'),  # Store to hold data across updates
    dcc.Graph(
        id='live-candlestick-chart',
        style={'height': '90vh', 'overflow': 'hidden'},
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'modeBarButtonsToAdd': ['resetScale2d', 'zoomIn2d', 'zoomOut2d']
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # Update every second
        n_intervals=0
    )
], style={'width': '100vw', 'height': '100vh', 'overflow': 'hidden'})


@app.callback(
    Output('stored-data', 'data'),
    [Input('load-date-btn', 'n_clicks')],
    [State('timeframe-dropdown', 'value'),
     State('start-date-picker', 'date')]
)
def load_historical_data(n_clicks, selected_timeframe, start_date):
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=1)  # Default to 1 day if no date is provided

    # Load data from the selected date
    df = get_data(SYMBOL, selected_timeframe, start_date=start_date)
    return df.to_dict('records') if not df.empty else []


@app.callback(
    Output('live-candlestick-chart', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('volume-checkbox', 'value'),
     Input('stored-data', 'data')],
    [State('timeframe-dropdown', 'value')]
)
def update_chart(n_intervals, volume_option, stored_data, selected_timeframe):
    # Convert stored data back to DataFrame
    df = pd.DataFrame(stored_data)

    # Fetch the latest candle to update the chart
    latest_data = get_data(SYMBOL, selected_timeframe, count=1)
    if not latest_data.empty and not df.empty:
        df = pd.concat([df[:-1], latest_data])  # Update the last candle

    # Determine if volume is enabled
    show_volume = 'show_volume' in volume_option

    # Define colors for volume based on candle direction
    volume_colors = ['green' if row['close'] > row['open'] else 'red' for index, row in df.iterrows()]

    # Set up subplots: conditionally add second row if volume is checked
    if show_volume:
        fig = sp.make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.02,
        )
    else:
        fig = sp.make_subplots(
            rows=1, cols=1
        )

    # Create a candlestick chart trace
    candlestick_trace = go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candlesticks",
        hoverinfo="x+y"
    )

    # Create a volume bar chart trace if volume is enabled
    if show_volume:
        volume_trace = go.Bar(
            x=df['time'],
            y=df['tick_volume'],
            name="Volume",
            marker=dict(color=volume_colors),
            hoverinfo="x+y"
        )
        fig.add_trace(volume_trace, row=2, col=1)

    # Add candlestick trace to the figure
    fig.add_trace(candlestick_trace, row=1, col=1)

    # Determine the color based on price movement
    last_price = df['close'].iloc[-1]
    price_color = "green" if df['close'].iloc[-1] > df['close'].iloc[-2] else "red"

    # Update layout to add crosshair-style hovermode and dark theme
    fig.update_layout(
        title=f"Live Chart for {SYMBOL}",
        xaxis=dict(
            showgrid=True, gridcolor='DarkGray', showticklabels=True,
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            )
        ),
        yaxis=dict(showgrid=True, gridcolor='DarkGray', side="right", showticklabels=True),
        height=900 if show_volume else 600,
        margin=dict(l=0, r=80, t=50, b=0),
        xaxis_rangeslider_visible=True,
        showlegend=False,
        plot_bgcolor='rgb(20, 24, 31)',
        paper_bgcolor='rgb(20, 24, 31)',
        font=dict(color="white"),
        hovermode='x unified'
    )

    # Add a horizontal line at the live price level and a box with live price outside the grid
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

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
