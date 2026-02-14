import pandas as pd
import numpy as np

def compute_metrics(history):


    df = pd.DataFrame(history)

    if len(df) < 2:
        return {}

    returns = df["total"].pct_change().dropna()

    total_return = df["total"].iloc[-1] - df["total"].iloc[0]
    pct_return = (df["total"].iloc[-1] / df["total"].iloc[0] - 1) * 100

    sharpe = 0
    if returns.std() != 0:
        sharpe = np.sqrt(252) * returns.mean() / returns.std()

    drawdown = (df["total"] / df["total"].cummax() - 1).min() * 100

    return {
        "Total Profit": total_return,
        "Return %": pct_return,
        "Sharpe Ratio": sharpe,
        "Max Drawdown %": drawdown
    }

