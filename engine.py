from queue import Queue
from data_handler.csv_data_handler import CSVDataHandler
from portfolio.portfolio import Portfolio
from execution.execution import SimulatedExecutionHandler
from performance.metrics import compute_metrics


def _run_single(strategy_class, symbol, csv_path,
                initial_capital, slippage, commission, params=None):
    """
    Run one backtest with a fixed set of params.
    Returns: (history, trades, metrics)
    """
    events = Queue()

    data       = CSVDataHandler(events, csv_path, symbol)
    strategy   = strategy_class(events, symbol, **(params or {}))
    portfolio  = Portfolio(events, symbol, initial_capital)
    execution  = SimulatedExecutionHandler(events, slippage=slippage,
                                           commission=commission)

    while data.continue_backtest:
        data.update_bars()

        while not events.empty():
            event = events.get()
            name  = event.__class__.__name__

            if name == "MarketEvent":
                strategy.calculate_signals(event)
                portfolio.update_market(event)
                execution.update_market(event)

            elif name == "SignalEvent":
                portfolio.update_signal(event)

            elif name == "OrderEvent":
                execution.execute_order(event)

            elif name == "FillEvent":
                portfolio.update_fill(event)

    metrics = compute_metrics(portfolio.holdings_history)
    return portfolio.holdings_history, portfolio.trades, metrics


def run_backtest(strategy_class, symbol, csv_path, initial_capital,
                 slippage=0.0, commission=0.0,
                 optimize=False, param_grid=None,
                 metric="Sharpe Ratio", split_ratio=70):

    # ── 1. SPLIT DATA ──────────────────────────────────────────
    import pandas as pd
    df = pd.read_csv(csv_path)
    split_idx  = int(len(df) * split_ratio / 100)

    import os
    base = os.path.splitext(csv_path)[0]

    train_path = base + "_train.csv"
    test_path  = base + "_test.csv"

    df.iloc[:split_idx].to_csv(train_path, index=False)
    df.iloc[split_idx:].to_csv(test_path,  index=False)

    # ── 2. OPTIMIZE ON TRAIN (if enabled) ──────────────────────
    best_params = {}

    if optimize and param_grid:
        import itertools

        keys   = list(param_grid.keys())
        values = list(param_grid.values())

        best_score  = float("-inf") if metric != "Drawdown" else float("inf")
        best_params = {}

        for combo in itertools.product(*values):
            params = dict(zip(keys, combo))

            try:
                _, _, m = _run_single(strategy_class, symbol, train_path,
                                      initial_capital, slippage, commission,
                                      params=params)
            except Exception:
                continue

            # Pick score based on chosen metric
            score_map = {
                "Sharpe Ratio": m.get("Sharpe Ratio", float("-inf")),
                "Return":       m.get("Total Return %", float("-inf")),
                "Drawdown":     m.get("Max Drawdown %", float("inf")),
            }
            score = score_map.get(metric, float("-inf"))

            if metric == "Drawdown":
                if score < best_score:       # lower drawdown = better
                    best_score  = score
                    best_params = params
            else:
                if score > best_score:
                    best_score  = score
                    best_params = params

    # ── 3. EVALUATE ON TEST ────────────────────────────────────
    history, trades, metrics = _run_single(
        strategy_class, symbol, test_path,
        initial_capital, slippage, commission,
        params=best_params or None
    )

    # Surface best params in metrics for UI display
    if best_params:
        metrics["best_params"] = best_params   # keep as dict(i guess so man......)

    return history, trades, metrics, best_params
