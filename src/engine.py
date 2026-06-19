import json

FILE_PATH = "data/nifty_option_chain.json"


# -----------------------------
# LOAD DATA (FIXED PATH)
# -----------------------------
def load_data():
    with open(FILE_PATH, "r") as f:
        raw = json.load(f)

    return raw["data"]["records"]["data"]


# -----------------------------
# NORMALIZE DATA
# -----------------------------
def normalize(rows):
    cleaned = []

    for r in rows:
        try:
            cleaned.append({
                "strike": r["strikePrice"],
                "ce_oi": r["CE"]["openInterest"],
                "pe_oi": r["PE"]["openInterest"],
                "ce_vol": r["CE"]["totalTradedVolume"],
                "pe_vol": r["PE"]["totalTradedVolume"],
            })
        except:
            continue

    return cleaned


# -----------------------------
# FIND PEAKS
# -----------------------------
def find_peaks(rows):
    ce_peak = max(rows, key=lambda x: x["ce_oi"])
    pe_peak = max(rows, key=lambda x: x["pe_oi"])

    return ce_peak, pe_peak


# -----------------------------
# SENTIMENT
# -----------------------------
def sentiment(ce_peak, pe_peak):
    if ce_peak["ce_oi"] > pe_peak["pe_oi"] * 1.1:
        return "BULLISH"
    elif pe_peak["pe_oi"] > ce_peak["ce_oi"] * 1.1:
        return "BEARISH"
    return "RISKY"


# -----------------------------
# RISKY STRIKES (YOUR RULE)
# -----------------------------
def risky_trades(ce_peak, pe_peak):
    return {
        "CE_BUY": {
            "entry": ce_peak["strike"] - 10,
            "sl": ce_peak["strike"] + 10
        },
        "PE_BUY": {
            "entry": pe_peak["strike"] + 10,
            "sl": pe_peak["strike"] - 10
        }
    }


# -----------------------------
# MAIN ENGINE
# -----------------------------
def run_engine():
    raw_rows = load_data()
    rows = normalize(raw_rows)

    ce_peak, pe_peak = find_peaks(rows)

    sent = sentiment(ce_peak, pe_peak)

    result = {
        "ce_peak": ce_peak,
        "pe_peak": pe_peak,
        "sentiment": sent
    }

    # -----------------------------
    # TRADE LOGIC
    # -----------------------------
    if sent == "RISKY":
        result["trades"] = risky_trades(ce_peak, pe_peak)

    elif sent == "BULLISH":
        result["trades"] = {
            "BUY": {
                "entry": pe_peak["strike"] + 10,
                "sl": pe_peak["strike"] - 10,
                "target": ce_peak["strike"]
            }
        }

    elif sent == "BEARISH":
        result["trades"] = {
            "SELL": {
                "entry": ce_peak["strike"] - 10,
                "sl": ce_peak["strike"] + 10,
                "target": pe_peak["strike"]
            }
        }

    return result


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    output = run_engine()
    print(json.dumps(output, indent=2))
