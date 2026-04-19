from events.events import FillEvent
from events.events import FillEvent, OrderEvent, MarketEvent

class SimulatedExecutionHandler:

#  Converts OrderEvents into FillEvents at market price.



    def __init__(self, events, slippage, commission):
        self.events = events
        self.current_price = None
        self.current_time = None
        self.slippage = slippage # 0.05% 
        self.commission = commission # 0.1%

    def update_market(self, market_event):
        self.current_price = market_event.close
        self.current_time = market_event.time

    def execute_order(self, order_event: OrderEvent):

        if self.current_price is None:
            return

        price = self.current_price

        # ---- APPLY SLIPPAGE ----
        if order_event.direction == "BUY":
            fill_price = price * (1 + self.slippage)
        else:
            fill_price = price * (1 - self.slippage)

        # ---- CALCULATE COMMISSION (FOR BOTH) ----
        trade_value = fill_price * order_event.quantity
        commission = trade_value * self.commission

        fill = FillEvent(
            time=self.current_time,
            symbol=order_event.symbol,
            quantity=order_event.quantity,
            direction=order_event.direction,
            fill_price=fill_price,
            commission=commission
        )

        self.events.put(fill)


