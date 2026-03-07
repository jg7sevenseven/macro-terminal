import requests
import pandas as pd
import json
import os

FRED_KEY = os.getenv("FRED_API_KEY")

series = {
    "Fed Balance Sheet":"WALCL",
    "ECB Balance Sheet":"ECBASSETSW",
    "China M2":"MABMM301CNM189S",
    "US Real Yield":"DFII10",
    "Financial Conditions":"NFCI"
}

def get_series(code):

    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id":code,
        "api_key":FRED_KEY,
        "file_type":"json"
    }

    r = requests.get(url,params=params)

    data = r.json()["observations"]

    df = pd.DataFrame(data)

    df["value"] = pd.to_numeric(df["value"],errors="coerce")

    df = df.dropna()

    return df["value"]

heatmap = []

for name,code in series.items():

    s = get_series(code)

    last = s.iloc[-1]

    change_3m = (s.iloc[-1] - s.iloc[-60]) / abs(s.iloc[-60]) * 100

    heatmap.append({
        "Indicator":name,
        "Value":round(float(last),2),
        "3M Change %":round(float(change_3m),2)
    })

with open("liquidity_heatmap.json","w") as f:

    json.dump(heatmap,f,indent=2)
