import MetaTrader5 as mt5
import time

mt5.initialize()

login = 52030081
password = 'hN$K0f!iGaDr3S'
server = 'ICMarketsSC-Demo'
mt5.login(login,password,server)

request = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': 'BTCUSD',
    'price': mt5.symbol_info_tick('BTCUSD').ask,
    'sl':   98821.0,
    'tp':  100168.0,
    'type': mt5.ORDER_TYPE_BUY,
    'volume': 0.01,
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
    'comment': 'Python Open Position'
}


result = mt5.order_send(request)
print(result);
# request the result as a dictionary and display it element by element
result_dict=result._asdict()


