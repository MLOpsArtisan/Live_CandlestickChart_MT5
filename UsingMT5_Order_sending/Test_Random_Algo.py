import MetaTrader5 as mt5
import time
import random

# Initialize MetaTrader 5
mt5.initialize()

# Login details
login = 52030081
password = 'hN$K0f!iGaDr3S'
server = 'ICMarketsSC-Demo'
mt5.login(login, password, server)

symbol = 'XAUUSD'
lot_size = 0.01

# Function to calculate variance (here, we'll simulate it with a random value)
def calculate_variance():
    return random.uniform(5, 15)  # Variance between 5 and 15 points (can be adjusted)

# Function to open a buy trade
def open_buy_trade():
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick:
        current_ask = symbol_tick.ask
        variance = calculate_variance()
        stop_loss = current_ask + variance
        take_profit = current_ask - variance

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
        variance = calculate_variance()
        stop_loss = current_bid - variance
        take_profit = current_bid + variance

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

# Function to track trade result: max profit and max loss
def track_trade(position_ticket):
    max_profit = -float('inf')  # Initialize with a very low value
    max_loss = float('inf')  # Initialize with a very high value

    # Monitor the trade until it's closed
    while True:
        positions = mt5.positions_get()
        for pos in positions:
            if pos.ticket == position_ticket:
                # Track max profit and max loss
                current_profit = pos.profit
                max_profit = max(max_profit, current_profit)
                max_loss = min(max_loss, current_profit)
                print(f"Max Profit: {max_profit} | Max Loss: {max_loss}")

                # If the position is closed, exit tracking
                if pos.volume == 0:
                    return max_profit, max_loss
        time.sleep(1)  # Wait for 1 second before checking again

# Simulate 100 trades
for trade_number in range(1, 101):
    print(f"\nStarting Trade #{trade_number}")

    # Open a trade every minute
    current_minute = time.localtime().tm_min
    if current_minute % 2 == 0:
        # Even minutes - Open buy order
        result = open_buy_trade()
    else:
        # Odd minutes - Open sell order
        result = open_sell_trade()

    # If trade was successful, track the result (max profit and max loss)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        position_ticket = result.order
        max_profit, max_loss = track_trade(position_ticket)
        print(f"Trade #{trade_number} - Max Profit: {max_profit} | Max Loss: {max_loss}")

    # Wait for 1 minute before opening the next trade
    time.sleep(60)

# Shutdown MetaTrader 5 after execution
mt5.shutdown()
vari = 0;