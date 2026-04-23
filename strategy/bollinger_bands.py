from collections import deque
import numpy as np
from events.events import SignalEvent

class BollingerBandsStrategy:

    def __init__(self, events, symbol, **params):
        self.events = events
        self.symbol = symbol

        # ---- PARAMETERS (dynamic) ----
        self.window = params.get("window", 20)
        self.num_std = params.get("num_std", 2)

        # ---- STATE ----
        self.prices = deque(maxlen=self.window)
        self.in_market = False

    def calculate_signals(self, event):

        if event.symbol != self.symbol:
            return

        self.prices.append(event.close)

        if len(self.prices) < self.window:
            return

        mean = np.mean(self.prices)
        std = np.std(self.prices)

        lower_band = mean - self.num_std * std

        # ---- SIGNALS ----
        if event.close < lower_band and not self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "LONG"))
            self.in_market = True

        elif event.close > mean and self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "EXIT"))
            self.in_market = False

    @staticmethod
    def parameter_grid():
        return {
            "window": [10, 20, 30],
            "num_std": [1.5, 2, 2.5]
        }
