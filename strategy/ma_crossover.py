# strategy/ma_crossover.py

from collections import deque
import numpy as np
from events.events import SignalEvent


class MovingAverageCrossStrategy:
    """
    Moving Average Crossover Strategy

    Logic:
    - LONG when short MA crosses above long MA
    - EXIT when short MA crosses below long MA
    """

    def __init__(self, events, symbol, **params):
        self.events = events
        self.symbol = symbol

        # ---- PARAMETERS (dynamic for optimization) ----
        self.short_window = params.get("short_window", 20)
        self.long_window = params.get("long_window", 50)

        # ---- STATE ----
        self.prices = deque(maxlen=self.long_window)
        self.in_market = False

    def calculate_signals(self, event):

        # Ensure correct symbol
        if event.symbol != self.symbol:
            return

        # Store price
        self.prices.append(event.close)

        # Wait until enough data
        if len(self.prices) < self.long_window:
            return

        # ---- CALCULATIONS ----
        prices_list = list(self.prices)
        short_ma = np.mean(prices_list[-self.short_window:])
        long_ma = np.mean(prices_list)

        # ---- SIGNAL LOGIC ----
        if short_ma > long_ma and not self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "LONG"))
            self.in_market = True

        elif short_ma < long_ma and self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "EXIT"))
            self.in_market = False

    @staticmethod
    def parameter_grid():
        """
        Parameter grid for optimization
        """
        return {
            "short_window": [5, 10, 20],
            "long_window": [30, 50, 100]
        }
