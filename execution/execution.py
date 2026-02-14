from events.events import FillEvent
from events.events import FillEvent, OrderEvent, MarketEvent

class SimulatedExecutionHandler:

#  Converts OrderEvents into FillEvents at market price.



    def __init__(self, events):
        self.events = events
        self.current_price = None
        self.current_time = None

    def update_market(self, market_event):
        self.current_price = market_event.close
        self.current_time = market_event.time

    def execute_order(self, order_event):
        if self.current_price is None:
            return

        fill = FillEvent(
            time=self.current_time,
            symbol=order_event.symbol,
            quantity=order_event.quantity,
            direction=order_event.direction,
            fill_price=self.current_price,
            commission=0.0
        )

        self.events.put(fill)



