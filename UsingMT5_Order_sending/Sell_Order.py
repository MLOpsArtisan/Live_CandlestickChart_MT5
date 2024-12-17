import MetaTrader5 as mt5

# Initialize MetaTrader 5
mt5.initialize()

# Login details
login = 52030081
password = 'hN$K0f!iGaDr3S'
server = 'ICMarketsSC-Demo'
mt5.login(login, password, server)

symbol = 'BTCUSD'

# Function to open a buy trade
def open_buy_trade():
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick:
        current_ask = symbol_tick.ask
        print(f"Current price (Ask): {current_ask}")
        sl_distance = float(input("Enter stop loss distance (points below current price): "))
        tp_distance = float(input("Enter take profit distance (points above current price): "))
        stop_loss = current_ask - sl_distance
        take_profit = current_ask + tp_distance

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'price': current_ask,
            'sl': stop_loss,
            'tp': take_profit,
            'type': mt5.ORDER_TYPE_BUY,
            'volume': 0.01,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
            'comment': 'Python Open Buy Position'
        }
        result = mt5.order_send(request)
        print("Buy Order result:", result)

# Function to close a buy trade
def close_buy_trade():
    positions = mt5.positions_get(symbol=symbol)
    for pos in positions:
        if pos.type == mt5.ORDER_TYPE_BUY:
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': pos.volume,
                'type': mt5.ORDER_TYPE_SELL,
                'position': pos.ticket,
                'price': mt5.symbol_info_tick(symbol).bid,
                'type_filling': mt5.ORDER_FILLING_IOC,
                'comment': 'Python Close Buy Position'
            }
            result = mt5.order_send(request)
            print("Close Buy Order result:", result)

# Function to open a sell trade
def open_sell_trade():
    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick:
        current_bid = symbol_tick.bid
        print(f"Current price (bid): {current_bid}")
        sl_distance = float(input("Enter stop loss distance (points above current price): "))
        tp_distance = float(input("Enter take profit distance (points below current price): "))
        stop_loss = current_bid + sl_distance
        take_profit = current_bid - tp_distance

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'price': current_bid,
            'sl': stop_loss,
            'tp': take_profit,
            'type': mt5.ORDER_TYPE_SELL,
            'volume': 0.01,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
            'comment': 'Python Open Sell Position'
        }
        result = mt5.order_send(request)
        print("Sell Order result:", result)

# Function to close a sell trade
def close_sell_trade():
    positions = mt5.positions_get(symbol=symbol)
    for pos in positions:
        if pos.type == mt5.ORDER_TYPE_SELL:
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': pos.volume,
                'type': mt5.ORDER_TYPE_BUY,
                'position': pos.ticket,
                'price': mt5.symbol_info_tick(symbol).ask,
                'type_filling': mt5.ORDER_FILLING_IOC,
                'comment': 'Python Close Sell Position'
            }
            result = mt5.order_send(request)
            print("Close Sell Order result:", result)

# Menu loop
while True:
    print("\nChoose an action:")
    print("1. Open Buy Trade")
    print("2. Close Buy Trade")
    print("3. Open Sell Trade")
    print("4. Close Sell Trade")
    print("5. Exit")
    choice = int(input("Enter your choice (1-5): "))

    if choice == 1:
        open_buy_trade()
    elif choice == 2:
        close_buy_trade()
    elif choice == 3:
        open_sell_trade()
    elif choice == 4:
        close_sell_trade()
    elif choice == 5:
        print("Exiting...")
        break
    else:
        print("Invalid choice! Please select a valid option.")

# Shutdown MetaTrader 5 after execution
mt5.shutdown()

