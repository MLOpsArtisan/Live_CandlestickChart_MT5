import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import csv
import numpy as np
import time

# Initialize MT5
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# Login details (replace with your credentials if needed)
login = 52030081
password = 'hN$K0f!iGaDr3S'
server = 'ICMarketsSC-Demo'
if not mt5.login(login, password, server):
    print("Failed to connect to account, error code =", mt5.last_error())
    quit()

# Configuration
symbol = 'BTCUSD'
lot_size = 0.01
csv_file = "trade_records.csv"


# Prepare the CSV file
def prepare_csv():
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["Time", "Symbol", "Ticket", "Type", "Volume", "Price", "S/L", "T/P", "Profit", "Balance"])


# Append trade data to the CSV file
def record_trade(trade):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            trade['time'],  # Time of trade
            trade['symbol'],  # Symbol
            trade['ticket'],  # Ticket number
            trade['type'],  # Type (Buy/Sell)
            trade['volume'],  # Volume
            trade['price'],  # Price
            trade['sl'],  # Stop Loss
            trade['tp'],  # Take Profit
            trade['profit'],  # Profit
            trade['balance']  # Balance after trade
        ])


# Function to calculate normalized variance
def calculate_variance(symbol, period=mt5.TIMEFRAME_M1, bars=4, max_percentage=0.005):
    rates = mt5.copy_rates_from_pos(symbol, period, 0, bars)
    if rates is None or len(rates) < bars:
        print(f"Error: Not enough data to calculate variance for {symbol}.")
        return 0.0

    close_prices = [rate['close'] for rate in rates]
    mean_price = np.mean(close_prices)
    variance = np.var(close_prices)

    # Normalize variance
    max_variance = mean_price * max_percentage
    normalized_variance = min(variance, max_variance)

    print(f"Close Prices: {close_prices}")
    print(f"Mean Price: {mean_price}")
    print(f"Calculated Variance: {variance} (Normalized: {normalized_variance})")
    return normalized_variance


# Function to open a buy trade
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


# Function to open a sell trade
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


# Monitor completed trades
def monitor_completed_trades():
    from_date = datetime.now() - timedelta(minutes=10)  # Fetch deals from the last 10 minutes
    to_date = datetime.now()
    deals = mt5.history_deals_get(from_date, to_date)

    if deals is None or len(deals) == 0:
        print(f"No deals found between {from_date} and {to_date}, error code={mt5.last_error()}")
        return

    # Convert deals to a DataFrame for easier processing
    deals_df = pd.DataFrame([deal._asdict() for deal in deals])
    deals_df['time'] = pd.to_datetime(deals_df['time'], unit='s')

    # Filter by relevant comments and log only unrecorded trades
    for _, deal in deals_df.iterrows():
        if deal['comment'] in ["Python Buy Order", "Python Sell Order"]:
            record_trade({
                "time": deal['time'].strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": deal['symbol'],
                "ticket": deal['ticket'],
                "type": "Buy" if deal['type'] == mt5.ORDER_TYPE_BUY else "Sell",
                "volume": deal['volume'],
                "price": deal['price'],
                "sl": deal['sl'],
                "tp": deal['tp'],
                "profit": deal['profit'],
                "balance": mt5.account_info().balance  # Current balance
            })



# Function to track max profit and loss
def track_all_trades():
    positions = mt5.positions_get()
    max_profit = -float('inf')
    max_loss = float('inf')
    total_profit = 0.0

    if positions:
        for pos in positions:
            current_profit = pos.profit
            max_profit = max(max_profit, current_profit)
            max_loss = min(max_loss, current_profit)
            total_profit += current_profit
    else:
        print("No open positions found.")
        max_profit = 0
        max_loss = 0
        total_profit = 0.0

    return max_profit, max_loss, total_profit


# Main trading loop
prepare_csv()  # Initialize CSV
for trade_number in range(1, 101):
    print(f"\nStarting Trade #{trade_number}")

    if trade_number % 2 == 0:
        result = open_buy_trade()
    else:
        result = open_sell_trade()

    time.sleep(5)  # Wait for trade to execute

    # Monitor and record completed trades
    monitor_completed_trades()

    max_profit, max_loss, total_profit = track_all_trades()
    print(f"Trade #{trade_number} - Max Profit (All Trades): {max_profit} | Max Loss (All Trades): {max_loss}")
    print(f"Trade #{trade_number} - Total Profit (All Trades): {total_profit}")

    time.sleep(55)  # Wait for the next trade

# Shutdown MT5
mt5.shutdown()