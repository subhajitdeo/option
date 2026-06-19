import json

# -----------------------------
# 1. LOAD DATA
# -----------------------------
def load_data(path="nifty_option_chain.json"):
    with open(path, "r") as f:
        raw = json.load(f)

    # your structure fix safety
    if "data" in raw:
        raw = raw["data"]

    if "records" in raw:
        raw = raw["records"]

    if "records" in raw and "data" in raw["records"]:
        raw = raw["records"]["data"]

    return raw


# -----------------------------
# 2. FIND ATM
# -----------------------------
def find_atm(data, spot):
    return min(data, key=lambda x: abs(x["strikePrice"] - spot))["strikePrice"]


# -----------------------------
# 3. FILTER ZONE ±5
# -----------------------------
def filter_zone(data, atm):
    zone = []
    for d in data:
        sp = d["strikePrice"]
        if atm - 250 <= sp <= atm + 250:  # approx ±5 strikes (50pt each)
            zone.append(d)
    return zone


# -----------------------------
# 4. FIND PEAKS
# -----------------------------
def find_peaks(zone):
    ce_peak = max(zone, key=lambda x: x["CE"]["openInterest"])
    pe_peak = max(zone, key=lambda x: x["PE"]["openInterest"])

    return {
        "ce_peak": {
            "strike": ce_peak["strikePrice"],
            "oi": ce_peak["CE"]["openInterest"]
        },
        "pe_peak": {
            "strike": pe_peak["strikePrice"],
            "oi": pe_peak["PE"]["openInterest"]
        }
    }


# -----------------------------
# 5. SENTIMENT (BASIC VERSION)
# -----------------------------
def get_sentiment(ce_peak, pe_peak):
    ce = ce_peak["strike"]
    pe = pe_peak["strike"]

    if ce == pe:
        return "RISKY"
    elif ce < pe:
        return "BULLISH"
    else:
        return "BEARISH"


# -----------------------------
# 6. RISKY MODE ENGINE
# -----------------------------
def risky_engine(ce_peak, pe_peak):
    ce = ce_peak["strike"]
    pe = pe_peak["strike"]

    return {
        "sentiment": "RISKY",

        "pe_trade": {
            "type": "BUY_PE",
            "entry": pe + 10,
            "sl": pe - 10,
            "target_1": pe - 5,
            "target_2": "exit on reversal"
        },

        "ce_trade": {
            "type": "SELL_CE",
            "entry": ce - 10,
            "sl": ce + 10,
            "target_1": ce + 5,
            "target_2": "exit on reversal"
        }
    }


# -----------------------------
# 7. BULLISH ENGINE
# -----------------------------
def bullish_engine(ce_peak, pe_peak):
    support = pe_peak["strike"] + 15
    resistance = ce_peak["strike"] - 10

    return {
        "sentiment": "BULLISH",

        "support": {
            "level": support,
            "sl": support - 10
        },

        "resistance": {
            "level": resistance,
            "sl": resistance + 10
        },

        "buy_ce": {
            "entry": resistance,
            "target_1": resistance + 5,
            "target_2": ce_peak["strike"]
        }
    }


# -----------------------------
# 8. BEARISH ENGINE
# -----------------------------
def bearish_engine(ce_peak, pe_peak):
    resistance = ce_peak["strike"] - 15
    support = pe_peak["strike"] + 10

    return {
        "sentiment": "BEARISH",

        "resistance": {
            "level": resistance,
            "sl": resistance + 10
        },

        "support": {
            "level": support,
            "sl": support - 10
        },

        "sell_ce": {
            "entry": resistance,
            "target_1": resistance - 5,
            "target_2": pe_peak["strike"]
        }
    }


# -----------------------------
# 9. MAIN ENGINE
# -----------------------------
def run_engine(data, spot):
    atm = find_atm(data, spot)
    zone = filter_zone(data, atm)
    peaks = find_peaks(zone)

    ce_peak = peaks["ce_peak"]
    pe_peak = peaks["pe_peak"]

    sentiment = get_sentiment(ce_peak, pe_peak)

    if sentiment == "RISKY":
        trade = risky_engine(ce_peak, pe_peak)

    elif sentiment == "BULLISH":
        trade = bullish_engine(ce_peak, pe_peak)

    else:
        trade = bearish_engine(ce_peak, pe_peak)

    return {
        "spot": spot,
        "atm": atm,
        "ce_peak": ce_peak,
        "pe_peak": pe_peak,
        "sentiment": sentiment,
        "trade_plan": trade
    }


# -----------------------------
# 10. RUN
# -----------------------------
if __name__ == "__main__":
    data = load_data("data/nifty_option_chain.json")
    spot = data[0]["CE"]["underlyingValue"]  # auto spot

    result = run_engine(data, spot)

    print(json.dumps(result, indent=2))
