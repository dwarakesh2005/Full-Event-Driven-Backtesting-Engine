# data_handler/csv_data_handler.py

import pandas as pd
from events.events import MarketEvent


class CSVDataHandler:
    """
    Reads CSV files and generates MarketEvents one bar at a time.
    """

    def __init__(self, events, csv_path, symbol):
        self.events = events
        self.csv_path = csv_path
        self.symbol = symbol

        self.data = None
        self.latest_index = 0
        self.continue_backtest = True

        self._load_data()

    def _load_data(self):
        
        self.data = pd.read_csv(self.csv_path, parse_dates=["Date"])
        self.data.sort_values("Date", inplace=True)
        self.data.reset_index(drop=True, inplace=True)

# ---- IMPORTANT FIX ----
        numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in numeric_cols:
            self.data[col] = pd.to_numeric(self.data[col], errors="coerce")


    def update_bars(self):
        """
        Pushes the next MarketEvent onto the event queue.
        """
        if self.latest_index >= len(self.data):
            self.continue_backtest = False
            return

        row = self.data.iloc[self.latest_index]

        event = MarketEvent(
            symbol=self.symbol,
            time=row["Date"],
            open=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
            volume=row["Volume"],
        )

        self.events.put(event)
        self.latest_index += 1
