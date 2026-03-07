import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Macro Liquidity Terminal")

# -----------------------------
# CONFIG
# -----------------------------

ETF_LIST = [
"QQQ",
"XLU",
"IWM",
"KBE",
"SPY"
]

MACRO = [
"^TNX",
"^IRX",
"^VIX",
"DX-Y.NYB",
"HYG",
"LQD"
]

SYMBOLS = ETF_LIST + MACRO

# -----------------------------
# DATA DOWNLOAD
# -----------------------------

@st.cache_data(ttl=3600)
def get_data():

    data = yf.download(
        SYMBOLS,
        period="6mo",
        progress=False,
        auto_adjust=True
    )

    return data

data = get_data()

prices = data["Close"]
volume = data["Volume"]

# -----------------------------
# MACRO DATA
# -----------------------------

ten_year = prices["^TNX"].iloc[-1] / 10
three_month = prices["^IRX"].iloc[-1] / 10
yield_curve = ten_year - three_month
vix = prices["^VIX"].iloc[-1]
dxy = prices["DX-Y.NYB"].iloc[-1]

# -----------------------------
# CREDIT MODEL
# -----------------------------

credit_ratio = prices["HYG"] / prices["LQD"]

credit_change = credit_ratio.pct_change(20).iloc[-1]

if credit_change > 0:
    credit_signal = "Improving"
else:
    credit_signal = "Worsening"

# -----------------------------
# LIQUIDITY MODEL
# -----------------------------

score = 0

if vix < 20:
    score += 1

if yield_curve > 0:
    score += 1

if credit_change > 0:
    score += 1

if ten_year < 4.25:
    score += 1

if score >= 3:
    regime = "RISK ON"
elif score == 2:
    regime = "NEUTRAL"
else:
    regime = "RISK OFF"

# -----------------------------
# ETF SIGNALS
# -----------------------------

signals = []

ret20 = prices.pct_change(20)

spy_ret = ret20["SPY"].iloc[-1]

for t in ETF_LIST:

    price = prices[t].iloc[-1]

    ma50 = prices[t].rolling(50).mean().iloc[-1]

    rs = ret20[t].iloc[-1] - spy_ret

    if price > ma50 and rs > 0:

        signal = "BUY"

    elif price > ma50:

        signal = "HOLD"

    else:

        signal = "AVOID"

    signals.append({
        "Ticker":t,
        "Price":round(price,2),
        "Relative Strength %":round(rs*100,2),
        "Signal":signal
    })

signal_df = pd.DataFrame(signals)

# -----------------------------
# DASHBOARD
# -----------------------------

st.header("Macro Environment")

c1,c2,c3,c4 = st.columns(4)

c1.metric("10Y Yield",f"{ten_year:.2f}%")
c2.metric("Yield Curve",f"{yield_curve:.2f}%")
c3.metric("VIX",f"{vix:.2f}")
c4.metric("Dollar Index",f"{dxy:.2f}")

st.write("Credit Market:",credit_signal)

st.subheader("Market Regime")

st.write(regime)

# -----------------------------
# ETF SIGNAL TABLE
# -----------------------------

st.subheader("ETF Trading Signals")

st.dataframe(signal_df)

# -----------------------------
# CREDIT CHART
# -----------------------------

st.subheader("Credit Market Risk")

fig = px.line(credit_ratio,title="HYG / LQD Ratio")

st.plotly_chart(fig,use_container_width=True)

# -----------------------------
# RELATIVE PERFORMANCE
# -----------------------------

st.subheader("Relative Performance")

perf = ret20[ETF_LIST].iloc[-1]*100

fig2 = px.bar(perf,title="20 Day Relative Performance")

st.plotly_chart(fig2,use_container_width=True)

# -----------------------------
# TRADE ALERTS
# -----------------------------

st.subheader("Alerts")

alerts = signal_df[signal_df["Signal"]=="BUY"]

if alerts.shape[0] == 0:

    st.write("No buy signals")

else:

    for i in alerts["Ticker"]:

        st.success(f"BUY SIGNAL: {i}")