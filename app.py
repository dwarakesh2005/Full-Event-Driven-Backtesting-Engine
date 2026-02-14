import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date
from strategy.register import load_strategies
from engine import run_backtest

#Load strategies

STRATEGIES = load_strategies()

st.title("Event Driven Backtesting Engine")

#-------- USER INPUT --------

ticker = st.text_input("Ticker Symbol", "AAPL")
start_date = st.date_input("Start Date", date(2020,1,1))
end_date = st.date_input("End Date", date(2022,1,1))
capital = st.number_input("Initial Capital", value=100000)

selected_strategy_name = st.selectbox(
"Choose Strategy",
list(STRATEGIES.keys())
)

run = st.button("Run Backtest")

#-------- RUN PIPELINE --------

if run:

    strategy_class = STRATEGIES[selected_strategy_name]

    st.write("Downloading data...")

    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error("No data found")
        st.stop()

    # Clean dataset
    data = data[["Open","High","Low","Close","Volume"]]
    data.dropna(inplace=True)
    data.reset_index(inplace=True)

    csv_path = f"data/{ticker}.csv"
    data.to_csv(csv_path, index=False)

    st.success("Data prepared")

    # Run backtest
    st.write("Running backtest...")
    history, trades,metrics  = run_backtest(
        strategy_class=strategy_class,
        symbol=ticker,
        csv_path=csv_path,
        initial_capital=capital
    )

    # Convert to DataFrame
    history_df = pd.DataFrame(history)
    trades_df = pd.DataFrame(trades)

    # Tabs
    # Tabs

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Equity Curve",
        "Trades",
        "Quant Metrics",
        "Summary"
    ])

    # ---------- TAB 1: Equity ----------
    with tab1:
        if not history_df.empty:
            st.subheader("Portfolio Value Over Time")
            st.line_chart(history_df.set_index("time")["total"])
        else:
            st.info("No equity data available")

    # ---------- TAB 2: Trades ----------
    with tab2:
        st.subheader("Trade Log")
        if trades_df.empty:
            st.info("No trades executed")
        else:
            st.dataframe(trades_df)

    # ---------- TAB 3: Quant Metrics ----------
    with tab3:
        st.subheader("Performance Metrics")

        if metrics:
            for k, v in metrics.items():
                st.metric(k, f"{v:,.2f}")
        else:
            st.warning("Not enough data to compute metrics")

    # ---------- TAB 4: Human Summary ----------
    with tab4:
        st.subheader("What Happened?")

        if not history_df.empty:

            start_val = history_df["total"].iloc[0]
            end_val = history_df["total"].iloc[-1]
            profit = end_val - start_val

            st.write(f"Initial capital: **${start_val:,.0f}**")
            st.write(f"Final value: **${end_val:,.0f}**")

            if profit > 0:
                st.success(f"You made **${profit:,.0f} profit**")
            elif profit < 0:
                st.error(f"You lost **${abs(profit):,.0f}**")
            else:
                st.info("No profit, no loss")

            st.write(f"Total trades executed: **{len(trades_df)}**")

            if metrics and "Sharpe Ratio" in metrics:
                if metrics["Sharpe Ratio"] > 1:
                    st.write("Returns were relatively stable.")
                else:
                    st.write("Returns were volatile and inconsistent.")
        else:
            st.info("No history data available")
