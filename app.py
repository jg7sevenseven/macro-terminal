import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import json

st.set_page_config(layout="wide")

st.title("Macro Liquidity Terminal")

from datetime import datetime


# -----------------------------
# MANUAL REFRESH
# -----------------------------

if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()
    st.rerun()

# Last update timestamp
st.caption(f"Last market data refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

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
if data.empty:
    st.error("Market data failed to load.")
    st.stop()

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
# GLOBAL RISK GAUGE MODEL
# -----------------------------

risk_score = 0

# VIX signal
if vix < 18:
    risk_score += 1
elif vix > 25:
    risk_score -= 1

# Credit spreads signal
if credit_change > 0:
    risk_score += 1
else:
    risk_score -= 1

# Dollar trend
dxy_change = prices["DX-Y.NYB"].pct_change(20).iloc[-1]

if dxy_change < 0:
    risk_score += 1
else:
    risk_score -= 1

# Liquidity index signal
liq = None

try:
    with open("liquidity_output.json") as f:
        liquidity_data = json.load(f)
        liq = liquidity_data["liquidity_index"]

        if liq > 0.5:
            risk_score += 1
        elif liq < -0.5:
            risk_score -= 1

except:
    pass


# -----------------------------
# RISK REGIME CLASSIFICATION
# -----------------------------

if risk_score >= 2:
    risk_regime = "GREEN"

elif risk_score <= -2:
    risk_regime = "RED"

else:
    risk_regime = "YELLOW"


# -----------------------------
# GLOBAL RISK GAUGE DISPLAY
# -----------------------------

st.subheader("Global Risk Gauge")

st.caption(
"Composite indicator summarizing market risk conditions using volatility, "
"credit spreads, liquidity, and dollar strength."
)

if risk_regime == "GREEN":
    st.success("🟢 GREEN — Risk On")

elif risk_regime == "RED":
    st.error("🔴 RED — Risk Off")

else:
    st.warning("🟡 YELLOW — Neutral")


drivers = pd.DataFrame({
"Indicator":[
"VIX",
"Credit Trend",
"Dollar Trend",
"Liquidity Index"
],
"Status":[
round(vix,2),
credit_signal,
"Falling" if dxy_change < 0 else "Rising",
liq if liq is not None else "N/A"
]
})

st.dataframe(drivers, use_container_width=True)

# -----------------------------
# LIQUIDITY MODEL (Internal)
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

# -----------------------------
# GLOBAL LIQUIDITY INDEX
# -----------------------------

st.subheader("Global Liquidity Index")

try:

    with open("liquidity_output.json") as f:

        liquidity_data = json.load(f)

    col1, col2 = st.columns(2)

    col1.metric(
        "Global Liquidity Index",
        round(liquidity_data["liquidity_index"],2)
    )

    col2.metric(
        "Liquidity Regime",
        liquidity_data["regime"]
    )

except:

    st.warning("Liquidity model not updated yet")
st.subheader("Global Liquidity Heatmap")

try:

    with open("liquidity_heatmap.json") as f:

        heat = json.load(f)

    heat_df = pd.DataFrame(heat)

    fig_heat = px.imshow(
        heat_df[["3M Change %"]],
        labels=dict(x="Liquidity Change",y="Indicator",color="%"),
        y=heat_df["Indicator"],
        title="3 Month Liquidity Change"
    )

    st.plotly_chart(fig_heat,use_container_width=True)

    st.dataframe(heat_df)

except:

    st.write("Liquidity heatmap not available yet")

# -----------------------------
# MARKET REGIME
# -----------------------------

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

st.subheader("Automated Market Scan")

try:

    import json

    with open("market_scan.json") as f:

        scan = json.load(f)

    scan_df = pd.DataFrame(scan)

    st.dataframe(scan_df)

except:

    st.write("Market scan not available yet")




