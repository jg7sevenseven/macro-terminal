import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Macro Liquidity Terminal")

# --------------------------------
# REFRESH BUTTON
# --------------------------------

if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()
    st.rerun()

st.caption(
    f"Last market data refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
)

# --------------------------------
# CONFIG
# --------------------------------

ETF_LIST = ["QQQ","XLU","IWM","KBE","SPY"]

MACRO = ["^TNX","^IRX","^VIX","DX-Y.NYB","HYG","LQD"]

SYMBOLS = ETF_LIST + MACRO

# --------------------------------
# DATA DOWNLOAD
# --------------------------------

@st.cache_data(ttl=600)
def get_data():

    data = yf.download(
        SYMBOLS,
        period="6mo",
        progress=False,
        auto_adjust=True
    )

    return data

data = get_data()

if data.empty:
    st.error("Market data failed to load.")
    st.stop()

prices = data["Close"]

# --------------------------------
# MACRO DATA
# --------------------------------

ten_year = prices["^TNX"].iloc[-1] / 10
three_month = prices["^IRX"].iloc[-1] / 10
yield_curve = ten_year - three_month
vix = prices["^VIX"].iloc[-1]
dxy = prices["DX-Y.NYB"].iloc[-1]

# --------------------------------
# CREDIT MODEL
# --------------------------------

credit_ratio = prices["HYG"] / prices["LQD"]

credit_change = credit_ratio.pct_change(20).iloc[-1]

credit_signal = "Improving" if credit_change > 0 else "Worsening"

# --------------------------------
# LIQUIDITY INDEX
# --------------------------------

liq = None

try:

    with open("liquidity_output.json") as f:

        liquidity_data = json.load(f)

        liq = liquidity_data["liquidity_index"]

        liquidity_regime = liquidity_data["regime"]

except:

    liquidity_regime = "Unavailable"

# --------------------------------
# GLOBAL RISK GAUGE
# --------------------------------

risk_score = 0

if vix < 18:
    risk_score += 1
elif vix > 25:
    risk_score -= 1

if credit_change > 0:
    risk_score += 1
else:
    risk_score -= 1

dxy_change = prices["DX-Y.NYB"].pct_change(20).iloc[-1]

if dxy_change < 0:
    risk_score += 1
else:
    risk_score -= 1

if liq is not None:

    if liq > 0.5:
        risk_score += 1

    elif liq < -0.5:
        risk_score -= 1

if risk_score >= 2:
    risk_regime = "GREEN"
elif risk_score <= -2:
    risk_regime = "RED"
else:
    risk_regime = "YELLOW"

# --------------------------------
# DASHBOARD
# --------------------------------

st.header("Macro Environment")

c1,c2,c3,c4 = st.columns(4)

c1.metric("10Y Yield",f"{ten_year:.2f}%")
c2.metric("Yield Curve",f"{yield_curve:.2f}%")
c3.metric("VIX",f"{vix:.2f}")
c4.metric("Dollar Index",f"{dxy:.2f}")

st.write("Credit Market:",credit_signal)

# --------------------------------
# RISK GAUGE
# --------------------------------

st.subheader("Global Risk Gauge")

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
liq if liq else "N/A"
]

})

st.dataframe(drivers,use_container_width=True)

# --------------------------------
# GLOBAL LIQUIDITY INDEX
# --------------------------------

st.subheader("Global Liquidity Index")

if liq:

    col1,col2 = st.columns(2)

    col1.metric("Liquidity Index",round(liq,2))
    col2.metric("Liquidity Regime",liquidity_regime)

else:

    st.warning("Liquidity model not updated yet")

# --------------------------------
# LIQUIDITY HEATMAP
# --------------------------------

st.subheader("Global Liquidity Heatmap")

try:

    with open("liquidity_heatmap.json") as f:

        heat = json.load(f)

    heat_df = pd.DataFrame(heat)

    fig = px.imshow(
        heat_df[["3M Change %"]],
        labels=dict(color="%"),
        y=heat_df["Indicator"]
    )

    st.plotly_chart(fig,use_container_width=True)

except:

    st.warning("Liquidity heatmap not available yet")

# --------------------------------
# ETF SIGNALS
# --------------------------------

ret20 = prices.pct_change(20)

spy_ret = ret20["SPY"].iloc[-1]

signals = []

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

st.subheader("ETF Trading Signals")

st.dataframe(signal_df)

# --------------------------------
# CREDIT CHART
# --------------------------------

st.subheader("Credit Market Risk")

fig = px.line(credit_ratio,title="HYG / LQD Ratio")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------
# RELATIVE PERFORMANCE
# --------------------------------

st.subheader("Relative Performance")

perf = ret20[ETF_LIST].iloc[-1]*100

fig2 = px.bar(perf,title="20 Day Relative Performance")

st.plotly_chart(fig2,use_container_width=True)

# --------------------------------
# MARKET SCAN
# --------------------------------

st.subheader("Automated Market Scan")

try:

    with open("market_scan.json") as f:

        scan = json.load(f)

    scan_df = pd.DataFrame(scan)

    st.dataframe(scan_df)

except:

    st.warning("Market scan not available yet")
