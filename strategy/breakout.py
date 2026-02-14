from collections import deque
import numpy as np
from events.events import SignalEvent

class BreakoutStrategy:

#Buy when price breaks highest high of N days
#Exit when price drops below moving average


    def __init__(self, events, symbol, lookback=20):
        self.events = events
        self.symbol = symbol
        self.lookback = lookback

        self.prices = deque(maxlen=lookback)
        self.in_market = False

    def calculate_signals(self, event):

        if event.symbol != self.symbol:
            return

        self.prices.append(event.close)

        if len(self.prices) < self.lookback:
            return

        highest = max(self.prices)
        mean_price = np.mean(self.prices)

        # ---- SIGNAL LOGIC ----
        if event.close >= highest and not self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "LONG"))
            self.in_market = True

        elif event.close < mean_price and self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "EXIT"))
            self.in_market = False
