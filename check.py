import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
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


# Initialize Dash app
app = dash.Dash(__name__)

# Layout for quick buy/sell and trade management
app.layout = html.Div([
    html.Button('Quick Buy', id='quick-buy', n_clicks=0),
    html.Button('Quick Sell', id='quick-sell', n_clicks=0),

    html.Div(id='trade-modal', style={'display': 'none'}, children=[
        dcc.Input(id='order-amount', type='number', placeholder="Amount", style={'margin': '10px'}),
        dcc.Input(id='stop-loss', type='number', placeholder="Stop Loss", style={'margin': '10px'}),
        dcc.Input(id='take-profit', type='number', placeholder="Take Profit", style={'margin': '10px'}),
        html.Button('Submit Order', id='submit-order', n_clicks=0),
        html.Button('Cancel', id='cancel-order', n_clicks=0),
    ]),

    dcc.Graph(
        id='live-candlestick-chart',
        style={'width': '100%', 'height': '100%'},
        config={'displayModeBar': False}
    ),

    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # Update every 1 second
        n_intervals=0
    ),
])


@app.callback(
    Output('trade-modal', 'style'),
    [Input('quick-buy', 'n_clicks'), Input('quick-sell', 'n_clicks')]
)
def show_trade_modal(buy_clicks, sell_clicks):
    if buy_clicks > 0 or sell_clicks > 0:
        return {'display': 'block'}  # Show modal
    return {'display': 'none'}  # Hide modal


@app.callback(
    Output('trade-modal', 'style'),
    Output('live-candlestick-chart', 'figure'),
    [Input('submit-order', 'n_clicks')],
    [State('order-amount', 'value'),
     State('stop-loss', 'value'),
     State('take-profit', 'value'),
     State('quick-buy', 'n_clicks'),
     State('quick-sell', 'n_clicks')]
)
def place_order(n_clicks, amount, stop_loss, take_profit, buy_clicks, sell_clicks):
    if n_clicks > 0:
        order_type = 'buy' if buy_clicks > sell_clicks else 'sell'
        stop_loss = float(stop_loss) if stop_loss else None
        take_profit = float(take_profit) if take_profit else None
        amount = float(amount)

        # Execute order via MetaTrader 5 (buy or sell market order)
        price = mt5.symbol_info_tick(SYMBOL).ask if order_type == 'buy' else mt5.symbol_info_tick(SYMBOL).bid

        # Prepare order request
        order = {
            'symbol': SYMBOL,
            'action': mt5.TRADE_ACTION_DEAL,
            'order_type': mt5.ORDER_TYPE_BUY if order_type == 'buy' else mt5.ORDER_TYPE_SELL,
            'volume': amount,
            'price': price,
            'sl': stop_loss,
            'tp': take_profit,
            'magic': 123456,
            'comment': "Quick Buy" if order_type == 'buy' else "Quick Sell"
        }

        # Send order
        result = mt5.order_send(order)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.comment}")
            return {'display': 'none'}, go.Figure()  # Hide modal if order failed

        print(f"Order successfully placed: {result.comment}")

        # Close the modal
        modal_style = {'display': 'none'}

        # Create figure and add horizontal lines for open, stop loss, and take profit
        fig = go.Figure()

        # Add Open price line
        fig.add_shape(
            type="line", x0=0, x1=1, y0=price, y1=price,
            line=dict(color="blue", width=2, dash="dash"),
            name="Open Price"
        )

        if stop_loss:
            fig.add_shape(
                type="line", x0=0, x1=1, y0=stop_loss, y1=stop_loss,
                line=dict(color="red", width=2, dash="dot"),
                name="Stop Loss"
            )

        if take_profit:
            fig.add_shape(
                type="line", x0=0, x1=1, y0=take_profit, y1=take_profit,
                line=dict(color="green", width=2, dash="dot"),
                name="Take Profit"
            )

        return modal_style, fig

    return {'display': 'none'}, go.Figure()  # Hide modal if no order placed


@app.callback(
    Output('live-candlestick-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_chart(n):
    df = get_data(SYMBOL, mt5.TIMEFRAME_M1, count=100)

    if df.empty:
        return go.Figure()

    fig = sp.make_subplots(rows=1, cols=1)

    # Create candlestick chart
    candlestick_trace = go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Candlesticks"
    )
    fig.add_trace(candlestick_trace)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
