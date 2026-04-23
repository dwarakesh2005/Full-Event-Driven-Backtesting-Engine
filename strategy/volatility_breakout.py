from collections import deque
import numpy as np
from events.events import SignalEvent


class VolatilityBreakoutStrategy:
    """
    Volatility Breakout Strategy

    Logic:
    - LONG when price breaks above (mean + k * volatility)
    - EXIT when price falls below mean
    """

    def __init__(self, events, symbol, **params):
        self.events = events
        self.symbol = symbol

        # ---- PARAMETERS (dynamic for optimization) ----
        self.window = params.get("window", 14)
        self.multiplier = params.get("multiplier", 1.0)

        # ---- STATE ----
        self.prices = deque(maxlen=self.window)
        self.in_market = False

    def calculate_signals(self, event):

        # Ensure correct symbol
        if event.symbol != self.symbol:
            return

        # Store price
        self.prices.append(event.close)

        # Wait until enough data
        if len(self.prices) < self.window:
            return

        # ---- CALCULATIONS ----
        prices_list = list(self.prices)

        mean_price = np.mean(prices_list)
        volatility = np.std(prices_list)

        upper_break = mean_price + self.multiplier * volatility

        # ---- SIGNAL LOGIC ----
        if event.close > upper_break and not self.in_market:
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
            "window": [10, 14, 20],
            "multiplier": [0.5, 1.0, 1.5]
        }
