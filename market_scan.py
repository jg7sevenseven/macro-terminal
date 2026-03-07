import yfinance as yf
import pandas as pd
import json

ETF_LIST = [
"QQQ",
"XLU",
"IWM",
"KBE",
"SPY"
]

data = yf.download(
    ETF_LIST,
    period="6mo",
    progress=False,
    auto_adjust=True
)

prices = data["Close"]

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
        "ticker": t,
        "price": round(float(price),2),
        "relative_strength": round(float(rs*100),2),
        "signal": signal
    })

with open("market_scan.json","w") as f:
    json.dump(signals,f,indent=2)
