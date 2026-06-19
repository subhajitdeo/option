import json

FILE_PATH = "data/nifty_option_chain.json"


# -----------------------------
# SAFE DATA LOADER (FIX YOUR ERROR)
# -----------------------------
def load_data():
    with open(FILE_PATH, "r") as f:
        raw = json.load(f)

    # Case 1: wrapped inside "data"
    if "data" in raw:
        raw = raw["data"]

    # Case 2: wrapped inside "records"
    if isinstance(raw, dict) and "records" in raw:
        raw = raw["records"]

    # Case 3: final extraction
    if isinstance(raw, dict) and "data" in raw:
        return raw["data"]

    # Case 4: already list
    if isinstance(raw, list):
        return raw

    raise Exception("Unknown JSON structure")


# -----------------------------
# SENTIMENT DETECTION (SIMPLE)
# -----------------------------
def detect_sentiment(ce_peak, pe_peak):
    ce = ce_peak["oi"]
    pe = pe_peak["oi"]

    if ce > pe * 1.1:
        return "BULLISH"
    elif pe > ce * 1.1:
        return "BEARISH"
    else:
        return "RISKY"


# -----------------------------
# FIND PEAKS
# -----------------------------
def find_peaks(rows):
    ce_peak = max(rows, key=lambda x: x["ce_oi"])
    pe_peak = max(rows, key=lambda x: x["pe_oi"])

    return {
        "ce": {"strike": ce_peak["strike"], "oi": ce_peak["ce_oi"]},
        "pe": {"strike": pe_peak["strike"], "oi": pe_peak["pe_oi"]},
    }


# -----------------------------
# EXTREME STRIKE LOGIC (YOUR RULE)
# -----------------------------
def risky_trades(pe_peak, ce_peak):
    return {
        "PE_BUY": {
            "entry": pe_peak["strike"] + 10,
            "sl": pe_peak["strike"] - 10,
        },
        "CE_BUY": {
            "entry": ce_peak["strike"] - 10,
            "sl": ce_peak["strike"] + 10,
        },
    }


# -----------------------------
# MAIN ENGINE
# -----------------------------
def run_engine():
    rows = load_data()

    peaks = find_peaks(rows)
    ce_peak = peaks["ce"]
    pe_peak = peaks["pe"]

    sentiment = detect_sentiment(ce_peak, pe_peak)

    result = {
        "ce_peak": ce_peak,
        "pe_peak": pe_peak,
        "sentiment": sentiment,
    }

    # -----------------------------
    # TRADE LOGIC
    # -----------------------------
    if sentiment == "RISKY":
        result["trades"] = risky_trades(pe_peak, ce_peak)

    else:
        # simple directional structure (you can extend later)
        if sentiment == "BULLISH":
            result["trades"] = {
                "BUY": {
                    "entry": pe_peak["strike"] + 10,
                    "sl": pe_peak["strike"] - 10,
                    "target": ce_peak["strike"],
                }
            }

        elif sentiment == "BEARISH":
            result["trades"] = {
                "SELL": {
                    "entry": ce_peak["strike"] - 10,
                    "sl": ce_peak["strike"] + 10,
                    "target": pe_peak["strike"],
                }
            }

    return result


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    output = run_engine()
    print(json.dumps(output, indent=2))
