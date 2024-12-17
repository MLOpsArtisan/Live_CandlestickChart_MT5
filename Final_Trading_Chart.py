import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.subplots as sp
import MetaTrader5 as mt5
import pandas as pd

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


def get_data(symbol, timeframe, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"Failed to retrieve data for {symbol}")
        return pd.DataFrame()  # Return empty DataFrame if there's an issue

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
        value=mt5.TIMEFRAME_M1,  # Default timeframe
        style={'width': '200px', 'margin-bottom': '10px'}
    ),
    dcc.Graph(
        id='live-candlestick-chart',
        style={'width': '100%', 'height': '100%'},  # Responsive width and height
        config={'displayModeBar': False}  # Hide Plotly mode bar for a cleaner look
    ),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # Update every 1 second
        n_intervals=0
    )
], style={
    'width': '100vw',  # Full width of the viewport
    'height': '100vh',  # Full height of the viewport
    'overflow': 'hidden',  # Prevent scrollbars
    'display': 'flex',  # Use flexbox for better responsiveness
    'flexDirection': 'column',  # Arrange children in a column
    'alignItems': 'center',  # Center-align elements horizontally
    'justifyContent': 'center'  # Center-align elements vertically
})


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
        hoverinfo="x+y"  # Show crosshair with date and price
    )

    # Create a volume bar chart trace if volume is enabled
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

    # Determine the color based on price movement
    last_price = df['close'].iloc[-1]
    price_color = "green" if df['close'].iloc[-1] > df['close'].iloc[-2] else "red"

    # Update layout to add crosshair-style hovermode and dark theme
    fig.update_layout(
        title=f"Live Chart for {SYMBOL}",
        xaxis=dict(showgrid=True, gridcolor='DarkGray', showticklabels=True),
        yaxis=dict(showgrid=True, gridcolor='DarkGray', side="right", showticklabels=True),
        height=800 if show_volume else 600,  # Adjust height dynamically based on volume chart
        margin=dict(l=0, r=80, t=50, b=0),  # Increased right margin to display price
        xaxis_rangeslider_visible=False,
        showlegend=False,
        plot_bgcolor='rgb(20, 24, 31)',  # Dark background
        paper_bgcolor='rgb(20, 24, 31)',  # Dark background for paper
        font=dict(color="white"),  # White font for contrast
        hovermode='x unified',  # Crosshair style hover mode
    )

    # Add a horizontal line at the live price level and a box with live price outside the grid
    fig.add_shape(
        type="line",
        x0=0, x1=1, y0=last_price, y1=last_price,
        xref="paper", yref="y",
        line=dict(color=price_color, width=2, dash="dash")
    )

    fig.update_yaxes(
        tickformat=".2f",  # Display full numbers with two decimal places
        showgrid=True,
        gridcolor='DarkGray',
        side="right"
    )

    fig.add_annotation(
        xref="paper", yref="y",
        x=1.047, y=last_price,  # Adjust position to be slightly outside the chart
        text=f"{last_price:.2f}",  # Display live price with two decimal places
        showarrow=False,
        font=dict(color="white", size=12, family="Arial"),
        bgcolor=price_color,
        bordercolor="white",
        align="center",
        borderpad=4  # Padding inside the box to make it adapt to content width
    )

    # Customize hover appearance for crosshair-like effect
    fig.update_xaxes(showline=True, linecolor='DarkGray', linewidth=1)
    fig.update_yaxes(showline=True, linecolor='DarkGray', linewidth=1)

    # Set consistent time display format and avoid overflow
    fig.update_xaxes(tickformat="%H:%M", matches='x')

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)