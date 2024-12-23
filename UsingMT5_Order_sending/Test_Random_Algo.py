import MetaTrader5 as mt5
import time
import random
import numpy as np


mt5.initialize()

login = 52030081
password = 'hN$K0f!iGaDr3S'
server = 'ICMarketsSC-Demo'
mt5.login(login, password, server)

symbol = 'BTCUSD'
lot_size = 0.01

# Function to calculate variance (here, we'll simulate it with a random value)
def calculate_variance(symbol, period=mt5.TIMEFRAME_M1, bars=4):

    rates = mt5.copy_rates_from_pos(symbol, period, 0, bars)
    if rates is None or len(rates) < bars:
        print(f"Error: Not enough data to calculate variance for {symbol}.")
        return 0.0

    close_prices = [rate['close'] for rate in rates]

    mean_price = np.mean(close_prices)
    variance = np.var(close_prices)

    print(f"Close Prices: {close_prices}")
    print(f"Mean Price: {mean_price}")
    print(f"Calculated Variance: {variance}")
    return variance

def open_buy_trade():
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick:
        current_ask = symbol_tick.ask
        variance = calculate_variance(symbol)
        stop_loss = current_ask - variance
        take_profit = current_ask + variance

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'price': current_ask,
            'sl': stop_loss,
            'tp': take_profit,
            'type': mt5.ORDER_TYPE_BUY,
            'volume': lot_size,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
            'comment': 'Python Buy Order'
        }
        result = mt5.order_send(request)
        print(f"Buy Order Result: {result}")
        return result

def open_sell_trade():
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick:
        current_bid = symbol_tick.bid
        variance = calculate_variance(symbol)


        stop_loss = current_bid + variance
        take_profit = current_bid - variance

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'price': current_bid,
            'sl': stop_loss,
            'tp': take_profit,
            'type': mt5.ORDER_TYPE_SELL,
            'volume': lot_size,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
            'comment': 'Python Sell Order'
        }
        result = mt5.order_send(request)
        print(f"Sell Order Result: {result}")
        return result

def track_trade(position_ticket):
    max_profit = -float('inf')
    max_loss = float('inf')

    positions = mt5.positions_get()
    for pos in positions:
        if pos.ticket == position_ticket:
            current_profit = pos.profit
            max_profit = max(max_profit, current_profit)
            max_loss = min(max_loss, current_profit)
            return max_profit, max_loss

for trade_number in range(1, 101):
    print(f"\nStarting Trade #{trade_number}")

    if trade_number % 2 == 0:
        result = open_buy_trade()
    else:
        result = open_sell_trade()
    position_ticket = result.order
    max_profit, max_loss = track_trade(position_ticket)
    print(f"Trade #{trade_number} - Max Profit: {max_profit} | Max Loss: {max_loss}")

    time.sleep(60)

mt5.shutdown()