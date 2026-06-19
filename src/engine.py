import json

# -----------------------------
# 1. LOAD DATA (OLD FORMAT)
# -----------------------------
def load_data(path="data/nifty_option_chain.json"):
    with open(path, "r") as f:
        raw = json.load(f)

    # OLD EXPECTED STRUCTURE
    return raw["records"]["data"]


# -----------------------------
# 2. FIND ATM
# -----------------------------
def find_atm(data, spot):
    return min(data, key=lambda x: abs(x["strikePrice"] - spot))["strikePrice"]


# -----------------------------
# 3. FILTER ZONE ±5 STRIKES (50 POINT STEP)
# -----------------------------
def filter_zone(data, atm):
    return [
        d for d in data
        if atm - 250 <= d["strikePrice"] <= atm + 250
    ]


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
# 5. SENTIMENT (BASIC)
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
# 6. RISKY MODE (YOUR RULE)
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
            "target_2": "exit_manual"
        },

        "ce_trade": {
            "type": "SELL_CE",
            "entry": ce - 10,
            "sl": ce + 10,
            "target_1": ce + 5,
            "target_2": "exit_manual"
        }
    }


# -----------------------------
# 7. BULLISH MODE
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
# 8. BEARISH MODE
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
def run_engine():
    data = load_data()

    spot = data[0]["CE"]["underlyingValue"]

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
    result = run_engine()
    print(json.dumps(result, indent=2))
