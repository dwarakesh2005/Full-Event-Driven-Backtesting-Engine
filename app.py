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
    st.header(" Strategy Control")

    ticker = st.text_input("Ticker Symbol", "AAPL").upper()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start", date(2020, 1, 1))
    with col2:
        end_date = st.date_input("End", date(2022, 1, 1))

    capital = st.number_input("Initial Capital ($)", value=100000)

    selected_strategy_name = st.selectbox(
        "Select Strategy",
        list(STRATEGIES.keys())
    )

    st.divider()
    run = st.button(" EXECUTE BACKTEST", use_container_width=True, type="primary")


# ---------------- MAIN TITLE ----------------
st.title(f" Event-Driven Backtesting Engine: {ticker}")
st.caption("Data: Yahoo Finance | Next-bar execution at close | No transaction costs")


# ---------------- RUN BACKTEST ----------------
if run:

    strategy_class = STRATEGIES[selected_strategy_name]

    with st.status("Running Backtest...", expanded=True) as status:

        st.write("📥 Downloading data")
        data = yf.download(ticker, start=start_date, end=end_date)

        if data.empty:
            st.error("No data found — check ticker or dates")
            st.stop()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data[["Open", "High", "Low", "Close", "Volume"]]
        data.dropna(inplace=True)
        data.reset_index(inplace=True)

        os.makedirs("data", exist_ok=True)
        csv_path = f"data/{ticker}.csv"
        data.to_csv(csv_path, index=False)

        st.write("⚙️ Running event-driven simulation")
        history, trades, metrics = run_backtest(
            strategy_class=strategy_class,
            symbol=ticker,
            csv_path=csv_path,
            initial_capital=capital
        )

        status.update(label="Backtest Complete", state="complete", expanded=False)

    # ---------------- DATAFRAMES ----------------
    history_df = pd.DataFrame(history)
    trades_df = pd.DataFrame(trades)

    if history_df.empty:
        st.warning("Strategy produced no results.")
        st.stop()

    history_df["time"] = pd.to_datetime(history_df["time"]).dt.tz_localize(None)
    if not trades_df.empty:
        trades_df["time"] = pd.to_datetime(trades_df["time"]).dt.tz_localize(None)
    data["Date"] = pd.to_datetime(data["Date"]).dt.tz_localize(None)

    # ---------------- KPI BAR ----------------
    final_val = history_df["total"].iloc[-1]
    start_val = history_df["total"].iloc[0]
    profit = final_val - start_val
    roi = (profit / start_val) * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Final Balance", f"${final_val:,.2f}", f"{roi:.2f}%")
    k2.metric("Trades", len(trades_df))
    k3.metric("Sharpe", f"{metrics.get('Sharpe Ratio', 0):.2f}")
    k4.metric("Drawdown", f"{metrics.get('Max Drawdown %', 0):.2f}%", delta_color="inverse")

    # ---------------- TABS ----------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Price & Equity",
        "📜 Trade Log",
        "🧪 Metrics",
        "🧠 Summary",
        "🕒 Trade Timeline"
    ])

    # ----- TAB 1 PRICE + EQUITY -----
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data['Date'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ))
        fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Portfolio Equity")
        st.area_chart(history_df.set_index("time")["total"])

    # ----- TAB 2 TRADES -----
    with tab2:
        if trades_df.empty:
            st.info("No trades executed.")
        else:
            st.dataframe(trades_df, use_container_width=True)

    # ----- TAB 3 METRICS -----
    with tab3:
        st.table(pd.Series(metrics, name="Value"))

    # ----- TAB 4 SUMMARY -----
    with tab4:
        st.write(f"Start: ${start_val:,.2f}")
        st.write(f"End: ${final_val:,.2f}")

        if profit > 0:
            st.success(f"Profit: ${profit:,.2f}")
        else:
            st.error(f"Loss: ${abs(profit):,.2f}")

        st.write(f"Total trades: {len(trades_df)}")

    # ----- TAB 5 TIMELINE -----
    with tab5:
        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=data['Date'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
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
                marker=dict(symbol="triangle-up", size=14, color="lime"),
                name="BUY"
            ))

            fig.add_trace(go.Scatter(
                x=sells["Date"],
                y=sells["Close"],
                mode="markers",
                marker=dict(symbol="triangle-down", size=14, color="red"),
                name="SELL"
            ))

        fig.add_trace(go.Scatter(
            x=history_df["time"],
            y=history_df["total"],
            name="Equity",
            yaxis="y2",
            line=dict(color="cyan")
        ))

        fig.update_layout(
            template="plotly_dark",
            height=650,
            yaxis2=dict(overlaying="y", side="right", title="Portfolio Value"),
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)
