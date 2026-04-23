import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import date

from strategy.register import load_strategies
from engine import run_backtest


# ---------------- PAGE CONFIG ----------------

st.set_page_config(page_title="Backtesting Terminal", layout="wide")

STRATEGIES = load_strategies()


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("Strategy Control")

    ticker = st.text_input("Ticker Symbol", "AAPL").upper()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start", date(2020, 1, 1))
    with col2:
        end_date = st.date_input("End", date(2022, 1, 1))

    capital = st.number_input("Initial Capital ($)", value=100000)

    slippage = st.number_input("Slippage (%)", 0.0, value=0.0, step=0.01) / 100
    commission = st.number_input("Transaction Cost (%)", 0.0, value=0.0, step=0.01) / 100

    selected_strategy_name = st.selectbox(
        "Select Strategy",
        list(STRATEGIES.keys())
    )

    st.subheader("Validation & Optimization")

    split_ratio = st.slider("Train/Test Split (%)", 50, 90, 70)
    optimize = st.checkbox("Enable Hyperparameter Optimization", value=False)

    metric = st.selectbox(
        "Optimization Metric",
        ["Sharpe Ratio", "Return", "Drawdown"]
    )

    param_inputs = {}

    if optimize and hasattr(STRATEGIES[selected_strategy_name], "parameter_grid"):
        st.subheader("Strategy Parameters")

        param_grid = STRATEGIES[selected_strategy_name].parameter_grid()

        for param, values in param_grid.items():
            param_inputs[param] = st.multiselect(
                f"{param}",
                options=values,
                default=values
            )

    st.divider()
    run = st.button("EXECUTE BACKTEST", use_container_width=True, type="primary")


# ---------------- MAIN ----------------

st.title(f"Event-Driven Backtesting Engine: {ticker}")
st.caption("Yahoo Finance | Event-driven execution | Transaction costs included")

if not run:
    st.info("Configure parameters and click EXECUTE BACKTEST")
    st.stop()


# ---------------- RUN BACKTEST ----------------

strategy_class = STRATEGIES[selected_strategy_name]

with st.status("Running backtest...", expanded=True):

    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error("No data found")
        st.stop()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Open", "High", "Low", "Close", "Volume"]]
    data.dropna(inplace=True)
    data.reset_index(inplace=True)

    os.makedirs("data", exist_ok=True)
    csv_path = f"data/{ticker}.csv"
    data.to_csv(csv_path, index=False)

    history, trades, metrics, best_params = run_backtest(
        strategy_class=strategy_class,
        symbol=ticker,
        csv_path=csv_path,
        initial_capital=capital,
        slippage=slippage,
        commission=commission,
        optimize=optimize,
        param_grid=param_inputs,
        metric=metric,
        split_ratio=split_ratio
    )


# ---------------- DATA PREPARATION ----------------

history_df = pd.DataFrame(history)
trades_df = pd.DataFrame(trades)

if history_df.empty:
    st.warning("No results")
    st.stop()

history_df["time"] = pd.to_datetime(history_df["time"]).astype("datetime64[ns]")
data["Date"] = pd.to_datetime(data["Date"]).astype("datetime64[ns]")

if not trades_df.empty:
    trades_df["time"] = pd.to_datetime(trades_df["time"]).astype("datetime64[ns]")

    for col in trades_df.columns:
        if trades_df[col].apply(lambda x: isinstance(x, dict)).any():
            trades_df[col] = trades_df[col].astype(str)


# ---------------- METRICS ----------------

final_val = history_df["total"].iloc[-1]
start_val = history_df["total"].iloc[0]
roi = (final_val - start_val) / start_val * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Balance", f"${final_val:,.2f}", f"{roi:.2f}%")
c2.metric("Trades", len(trades_df))
c3.metric("Sharpe Ratio", f"{metrics.get('Sharpe Ratio', 0):.2f}")
c4.metric("Max Drawdown", f"{metrics.get('Max Drawdown %', 0):.2f}%")


# ---------------- TABS ----------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Price & Equity",
    "Trades",
    "Metrics",
    "Summary",
    "Timeline"
])


# ---------------- TAB 1 ----------------

with tab1:
    data["MA20"] = data["Close"].rolling(20).mean()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350"
    ))

    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        name="MA20",
        line=dict(color="#ffd54f")
    ))

    if not trades_df.empty:
        merged = pd.merge_asof(
            trades_df.sort_values("time"),
            data.sort_values("Date"),
            left_on="time",
            right_on="Date",
            direction="nearest"
        )

        buys = merged[merged["direction"] == "BUY"]
        sells = merged[merged["direction"] == "SELL"]

        fig.add_trace(go.Scatter(
            x=buys["Date"],
            y=buys["Close"],
            mode="markers",
            marker=dict(symbol="triangle-up", color="lime", size=12)
        ))

        fig.add_trace(go.Scatter(
            x=sells["Date"],
            y=sells["Close"],
            mode="markers",
            marker=dict(symbol="triangle-down", color="red", size=12)
        ))

    fig.add_trace(go.Bar(
        x=data["Date"],
        y=data["Volume"],
        yaxis="y2",
        opacity=0.3
    ))

    fig.update_layout(
        template="plotly_dark",
        height=700,
        yaxis2=dict(overlaying="y", side="right"),
        xaxis_rangeslider_visible=True
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Equity Curve")
    st.line_chart(history_df.set_index("time")["total"])


# ---------------- TAB 2 ----------------

with tab2:
    st.dataframe(trades_df, use_container_width=True)


# ---------------- TAB 3 ----------------

with tab3:
    clean_metrics = {
        k: round(v, 4) if isinstance(v, float) else v
        for k, v in metrics.items()
        if not isinstance(v, dict)
    }

    st.table(pd.Series(clean_metrics))

    if best_params:
        st.subheader("Best Parameters")
        st.json(best_params)


# ---------------- TAB 4 ----------------

with tab4:
    st.write(f"Start: ${start_val:,.2f}")
    st.write(f"End: ${final_val:,.2f}")


# ---------------- TAB 5 ----------------

# ---------------- TAB 5 (TRADE TIMELINE) ----------------

with tab5:

    st.subheader("Trade Timeline")

    fig = go.Figure()

    # ---- PRICE CANDLES ----
    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Price",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350"
    ))

    # ---- TRADES OVERLAY ----
    if not trades_df.empty:

        trades_sorted = trades_df.sort_values("time")
        data_sorted = data.sort_values("Date")

        merged = pd.merge_asof(
            trades_sorted,
            data_sorted,
            left_on="time",
            right_on="Date",
            direction="nearest"
        )

        merged = merged.dropna(subset=["Close"])

        buys = merged[merged["direction"] == "BUY"]
        sells = merged[merged["direction"] == "SELL"]

        fig.add_trace(go.Scatter(
            x=buys["Date"],
            y=buys["Close"],
            mode="markers+text",
            text=["BUY"] * len(buys),
            textposition="top center",
            marker=dict(
                symbol="triangle-up",
                size=14,
                color="#00ff9f",
                line=dict(width=1, color="white")
            ),
            name="BUY"
        ))

        fig.add_trace(go.Scatter(
            x=sells["Date"],
            y=sells["Close"],
            mode="markers+text",
            text=["SELL"] * len(sells),
            textposition="bottom center",
            marker=dict(
                symbol="triangle-down",
                size=14,
                color="#ff4d4d",
                line=dict(width=1, color="white")
            ),
            name="SELL"
        ))

    # ---- CHART LAYOUT ----
    fig.update_layout(
        template="plotly_dark",
        height=700,
        margin=dict(l=10, r=10, t=30, b=10),

        hovermode="x unified",

        xaxis=dict(
            showgrid=False,
            rangeslider=dict(visible=True),
            showspikes=True,
            spikemode="across",
            spikesnap="cursor"
        ),

        yaxis=dict(
            title="Price",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
