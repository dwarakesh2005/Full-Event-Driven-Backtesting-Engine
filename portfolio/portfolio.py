# portfolio/portfolio.py

from events.events import OrderEvent


class Portfolio:
    """
    Handles positions, cash, and order generation.
    """

    def __init__(self, events, symbol, initial_capital=100000):
        self.events = events
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.trades = []

        self.cash = initial_capital
        self.position = 0
        self.current_price = None

        self.holdings_history = []

    def update_market(self, event):
        """
        Updates latest market price.
        """
        if event.symbol == self.symbol:
            self.current_price = event.close

    def update_signal(self, signal):
        """
        Converts SignalEvent into OrderEvent.
        """
        if signal.signal_type == "LONG" and self.position == 0:
            quantity = self._calculate_quantity()
            order = OrderEvent(
                symbol=self.symbol,
                order_type="MKT",
                quantity=quantity,
                direction="BUY"
            )
            self.events.put(order)

        elif signal.signal_type == "EXIT" and self.position > 0:
            order = OrderEvent(
                symbol=self.symbol,
                order_type="MKT",
                quantity=self.position,
                direction="SELL"
            )
            self.events.put(order)

    def update_fill(self, fill):
        """
        Updates cash and position from FillEvent.
        """
        if fill.direction == "BUY":
            cost = fill.quantity * fill.fill_price
            self.cash -= cost
            self.position += fill.quantity

        elif fill.direction == "SELL":
            proceeds = fill.quantity * fill.fill_price
            self.cash += proceeds
            self.position -= fill.quantity
        self.trades.append({
"time": fill.time,
"symbol": fill.symbol,
"direction": fill.direction,
"price": fill.fill_price,
"quantity": fill.quantity,
"cash_after": self.cash,
"position_after": self.position
})
        self._record_holdings(fill.time)

    def _calculate_quantity(self):
        """
        Simple position sizing: invest all cash.
        """
        if self.current_price is None:
            return 0
        return int(self.cash / self.current_price)

    def _record_holdings(self, time):
        """
        Records portfolio value over time.
        """
        holdings_value = self.position * self.current_price if self.current_price else 0
        total_value = self.cash + holdings_value

        self.holdings_history.append({
            "time": time,
            "cash": self.cash,
            "position": self.position,
            "holdings": holdings_value,
            "total": total_value
        })





































































































































































































































































































































































































































































                                                                    