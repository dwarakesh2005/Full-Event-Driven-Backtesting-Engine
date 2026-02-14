from collections import deque
import numpy as np
from events.events import SignalEvent

class RSIReversionStrategy:



    def __init__(self, events, symbol, period=14):
        self.events = events
        self.symbol = symbol
        self.period = period

        self.prices = deque(maxlen=period+1)
        self.in_market = False

    def calculate_signals(self, event):

        if event.symbol != self.symbol:
            return

        self.prices.append(event.close)

        if len(self.prices) < self.period + 1:
            return

        deltas = np.diff(self.prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # ---- SIGNAL LOGIC ----
        if rsi < 30 and not self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "LONG"))
            self.in_market = True

        elif rsi > 50 and self.in_market:
            self.events.put(SignalEvent(self.symbol, event.time, "EXIT"))
            self.in_market = False

