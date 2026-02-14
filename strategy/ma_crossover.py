# strategy/ma_crossover.py

from collections import deque
import numpy as np
from events.events import SignalEvent


class MovingAverageCrossStrategy:
    """
    Simple Moving Average Crossover Strategy.
    Generates LONG and EXIT signals.
    """

    def __init__(self, events, symbol, short_window=20, long_window=50):
        self.events = events
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window

        self.prices = deque(maxlen=long_window)
        self.in_market = False

    def calculate_signals(self, event):
        """
        Receives MarketEvent and generates SignalEvent.
        """
        if event.symbol != self.symbol:
            return

        self.prices.append(event.close)

        if len(self.prices) < self.long_window:
            return

        short_ma = np.mean(list(self.prices)[-self.short_window:])
        long_ma = np.mean(self.prices)

        if short_ma > long_ma and not self.in_market:
            signal = SignalEvent(
                symbol=self.symbol,
                time=event.time,
                signal_type="LONG"
            )
            self.events.put(signal)
            self.in_market = True

        elif short_ma < long_ma and self.in_market:
            signal = SignalEvent(
                symbol=self.symbol,
                time=event.time,
                signal_type="EXIT"
            )
            self.events.put(signal)
            self.in_market = False
    