import requests
import json
from datetime import datetime

url = "https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol=NIFTY&expiry=23-Jun-2026"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/option-chain"
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers)

res = session.get(url, headers=headers)
data = res.json()

# create folder safe
import os
os.makedirs("data", exist_ok=True)

file_path = "data/nifty_option_chain.json"

output = {
    "time": str(datetime.now()),
    "data": data
}

with open(file_path, "w") as f:
    json.dump(output, f)

print("Saved data at:", file_path)
