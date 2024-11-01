import matplotlib.pyplot as plt
import mplfinance as mpf
import MetaTrader5 as mt5
import pandas as pd
import time
from tkinter import Tk, StringVar, OptionMenu

# Available timeframes
TIMEFRAMES = {
    '1 Min': mt5.TIMEFRAME_M1,
    '5 Min': mt5.TIMEFRAME_M5,
    '15 Min': mt5.TIMEFRAME_M15,
    '1 Hour': mt5.TIMEFRAME_H1,
    '4 Hours': mt5.TIMEFRAME_H4
}

SYMBOL = "BTCUSD"  # You can change this to any other symbol
CSV_FILE = "data.csv"  # File to store data

# Initialize MetaTrader 5 connection
mt5.initialize()


def get_data_and_save(symbol, timeframe, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        print(f"Failed to retrieve data for {symbol}")
        return pd.DataFrame()  # Return empty DataFrame if there's an issue

    # Create DataFrame and format time
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)

    # Append data to CSV
    df.to_csv(CSV_FILE, mode='a', header=not pd.io.common.file_exists(CSV_FILE), index=False)

    return df


def plot_realtime_chart(selected_interval):
    selected_timeframe = TIMEFRAMES[selected_interval]

    fig, (ax, ax_volume) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})
    plt.ion()  # Turn on interactive mode
    plt.show(block=False)

    while True:
        df = get_data_and_save(SYMBOL, selected_timeframe, count=100)

        if not df.empty:
            ax.cla()
            ax_volume.cla()

            # Plot the latest 100 candles with volume
            mpf.plot(
                df.set_index('time'),
                type='candle',
                style='charles',
                ax=ax,
                volume=ax_volume,
                ylabel="Price",
                ylabel_lower="Volume"
            )

            ax.set_title(f"Live Chart for {SYMBOL} ({selected_interval})")

            plt.pause(1)  # Adjust update interval if needed

        time.sleep(1)  # Fetch new data every second


def on_dropdown_change(value):
    plot_realtime_chart(value)


# GUI for selecting time frame using Tkinter
root = Tk()
root.title("Select Timeframe")

selected_interval = StringVar(root)
selected_interval.set("1 Min")  # Default value

dropdown = OptionMenu(root, selected_interval, *TIMEFRAMES.keys(), command=on_dropdown_change)
dropdown.pack()

root.mainloop()

mt5.shutdown()  # Disconnect from MetaTrader 5 when done