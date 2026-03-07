import requests
import pandas as pd
import numpy as np
import os
import json

FRED_KEY = os.getenv("FRED_API_KEY")

series = {
"fed_balance":"WALCL",
"ecb_balance":"ECBASSETSW",
"china_m2":"MABMM301CNM189S",
"real_yield":"DFII10",
"financial_conditions":"NFCI"
}

def fetch_series(series_id):

    url = f"https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id":series_id,
        "api_key":FRED_KEY,
        "file_type":"json"
    }

    r = requests.get(url,params=params)

    data = r.json()["observations"]

    df = pd.DataFrame(data)

    df["value"] = pd.to_numeric(df["value"],errors="coerce")

    return df["value"].dropna()

data = {}

for name,code in series.items():

    data[name] = fetch_series(code).iloc[-100:]

df = pd.DataFrame(data)

# normalize series
z_scores = (df - df.mean()) / df.std()

liquidity_index = z_scores.mean(axis=1)

current_value = liquidity_index.iloc[-1]

if current_value > 0.5:

    regime = "LIQUIDITY EXPANSION"

elif current_value < -0.5:

    regime = "LIQUIDITY TIGHTENING"

else:

    regime = "NEUTRAL"

output = {
"liquidity_index":float(current_value),
"regime":regime
}

with open("liquidity_output.json","w") as f:

    json.dump(output,f)
