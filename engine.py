from queue import Queue
from data_handler.csv_data_handler import CSVDataHandler
from portfolio.portfolio import Portfolio
from execution.execution import SimulatedExecutionHandler
from performance.metrics import compute_metrics

def run_backtest(strategy_class, symbol, csv_path, initial_capital):


    events = Queue()

    data = CSVDataHandler(events, csv_path, symbol)
    strategy = strategy_class(events, symbol)
    portfolio = Portfolio(events, symbol, initial_capital)
    execution = SimulatedExecutionHandler(events)

    while data.continue_backtest:

        data.update_bars()

        while not events.empty():

            event = events.get()

            if event.__class__.__name__ == "MarketEvent":
                strategy.calculate_signals(event)
                portfolio.update_market(event)
                execution.update_market(event)

            elif event.__class__.__name__ == "SignalEvent":
                portfolio.update_signal(event)

            elif event.__class__.__name__ == "OrderEvent":
                execution.execute_order(event)

            elif event.__class__.__name__ == "FillEvent":
                portfolio.update_fill(event)

    metrics = compute_metrics(portfolio.holdings_history)

    return portfolio.holdings_history, portfolio.trades, metrics


