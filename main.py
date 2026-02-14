from queue import Queue
from data_handler.csv_data_handler import CSVDataHandler
from strategy.ma_crossover import MovingAverageCrossStrategy

events = Queue()

data = CSVDataHandler(events, "data/sample_data.csv", "TEST")
strategy = MovingAverageCrossStrategy(events, "TEST", 3, 5)

while data.continue_backtest:
    data.update_bars()
    event = events.get()
    strategy.calculate_signals(event)
