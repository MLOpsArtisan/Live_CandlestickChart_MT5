import MetaTrader5 as mt5
import time
import numpy as np

# Initialize MetaTrader 5
mt5.initialize()

# Login details
login = 52030081
password = 'hN$K0f!iGaDr3S'
server = 'ICMarketsSC-Demo'
mt5.login(login, password, server)

symbol = 'BTCUSD'
lot_size = 0.01

# Function to fetch minimum stop level
def get_min_stop_level(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        return symbol_info.trade_stops_level * symbol_info.trade_tick_size
    return 0.0

# Function to calculate variance from last 15 candles
def calculate_variance(symbol, bars=3):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, bars)
    if rates is None or len(rates) < bars:
        print("Not enough price data to calculate variance.")
        return 0.1
    close_prices = [rate['close'] for rate in rates]
    return np.var(close_prices)

# Function to track max profit and loss
def track_trade(ticket):
    max_profit = -float("inf")
    max_loss = float("inf")

    while True:
        positions = mt5.positions_get(ticket=ticket)
        if not positions:  # Trade is closed
            break
        profit = positions[0].profit
        max_profit = max(max_profit, profit)
        max_loss = min(max_loss, profit)
        time.sleep(1)

    return max_profit, max_loss

# Function to open trades with variance-based SL and TP
def open_trade(trade_type):
    symbol_tick = mt5.symbol_info_tick(symbol)
    if not symbol_tick:
        print("Symbol data not available.")
        return None

    price = symbol_tick.ask if trade_type == "buy" else symbol_tick.bid
    variance = calculate_variance(symbol)
    min_stop_level = get_min_stop_level(symbol)

    # Ensure SL/TP respect the minimum stop level
    sl_distance = max(variance, min_stop_level)
    tp_distance = max(variance, min_stop_level)

    # Calculate SL and TP
    if trade_type == "buy":
        stop_loss = price - sl_distance
        take_profit = price + tp_distance
        trade_type_mt5 = mt5.ORDER_TYPE_BUY
    else:  # sell
        stop_loss = price + sl_distance
        take_profit = price - tp_distance
        trade_type_mt5 = mt5.ORDER_TYPE_SELL

    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot_size,
        'type': trade_type_mt5,
        'price': price,
        'sl': stop_loss,
        'tp': take_profit,
        'type_filling': mt5.ORDER_FILLING_IOC,
        'type_time': mt5.ORDER_TIME_GTC,
        'comment': f"Python {trade_type.capitalize()} Order"
    }

    result = mt5.order_send(request)
    print(f"{trade_type.capitalize()} Order Result: {result}")
    return result

# Main trading logic: 100 sequential trades
for trade_number in range(1, 101):
    print(f"\nStarting Trade #{trade_number}")

    trade_type = "buy" if trade_number % 2 == 0 else "sell"

    # Open the trade
    result = open_trade(trade_type)

    ticket = result.order
    max_profit, max_loss = track_trade(ticket)
    print(f"Trade #{trade_number} Completed.")
    print(f"Max Profit: {max_profit:.2f} | Max Loss: {max_loss:.2f}")

# Shutdown MT5 connection
mt5.shutdown()
