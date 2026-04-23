from collections import deque
from events.events import SignalEvent


class MomentumStrategy:
    """
    Momentum Strategy (Rate of Change)

    Logic:
    - LONG when return over lookback period > threshold
    - EXIT when momentum weakens (return < 0)
    """

    def __init__(self, events, symbol, **params):
        self.events = events
        self.symbol = symbol

        # ---- PARAMETERS (dynamic for optimization) ----
        self.lookback = params.get("lookback", 10)
        self.threshold = params.get("threshold", 0.02)

        # ---- STATE ----
        self.prices = deque(maxlen=self.lookback + 1)
        self.in_market = False

    def calculate_signals(self, event):

        # Ensure correct symbol
        if event.symbol != self.symbol:
            return

        # Store price
        self.prices.append(event.close)

        # Wait until enough data
        if len(self.prices) < self.lookback + 1:
            return

        # ---- CALCULATE MOMENTUM ----
        past_price = self.prices[0]
        current_price = self.prices[-1]

        return_pct = (current_price - past_price) / past_price

        # ---- SIGNAL LOGIC ----
        if return_pct > self.threshold and not self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "LONG"))
            self.in_market = True

        elif return_pct < 0 and self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "EXIT"))
            self.in_market = False

    @staticmethod
    def parameter_grid():
        """
        Parameter grid for optimization
        """
        return {
            "lookback": [5, 10, 20],
            "threshold": [0.01, 0.02, 0.05]
        }
