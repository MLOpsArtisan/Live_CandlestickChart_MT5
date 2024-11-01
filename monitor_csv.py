import time
import pandas as pd

csv_file = "price_data.csv"  # Path to your CSV file

def tail_csv(file_path, interval=1):
    last_seen_row = None
    while True:
        try:
            data = pd.read_csv(file_path)
            if not data.empty:
                latest_row = data.iloc[-1]  # Get the last row only
                # Check if it's a new row compared to the last seen row
                if last_seen_row is None or not latest_row.equals(last_seen_row):
                    print(latest_row)
                    last_seen_row = latest_row
            time.sleep(interval)
        except pd.errors.EmptyDataError:
            print("CSV is empty or not yet created.")
            time.sleep(interval)
        except FileNotFoundError:
            print("CSV file not found, waiting...")
            time.sleep(interval)

if __name__ == "__main__":
    tail_csv(csv_file)
