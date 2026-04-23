from collections import deque
import numpy as np
from events.events import SignalEvent


class BreakoutStrategy:
    """
    Breakout Strategy

    Logic:
    - LONG when price breaks highest high of lookback window
    - EXIT when price falls below moving average
    """

    def __init__(self, events, symbol, **params):
        self.events = events
        self.symbol = symbol

        # ---- PARAMETERS (dynamic for optimization) ----
        self.lookback = params.get("lookback", 20)

        # ---- STATE ----
        self.prices = deque(maxlen=self.lookback)
        self.in_market = False

    def calculate_signals(self, event):

        # Ensure correct symbol
        if event.symbol != self.symbol:
            return

        # Store latest price
        self.prices.append(event.close)

        # Wait until enough data
        if len(self.prices) < self.lookback:
            return

        # ---- CALCULATIONS ----
        highest = max(self.prices)
        mean_price = np.mean(self.prices)

        # ---- SIGNAL LOGIC ----
        if event.close >= highest and not self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "LONG"))
            self.in_market = True

        elif event.close < mean_price and self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "EXIT"))
            self.in_market = False

    @staticmethod
    def parameter_grid():
        """
        Parameter grid for optimization
        """
        return {
            "lookback": [10, 20, 50]
        }
