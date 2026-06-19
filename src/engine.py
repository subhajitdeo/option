import json

INPUT_FILE = "data/nifty_option_chain.json"


# ----------------------------
# LOAD DATA
# ----------------------------
def load_data():
    with open(INPUT_FILE, "r") as f:
        raw = json.load(f)

    return raw["data"]["records"]["data"]


# ----------------------------
# ATM FINDER
# ----------------------------
def find_atm(chain):
    spot = chain[0]["CE"]["underlyingValue"]
    return min(chain, key=lambda x: abs(x["strikePrice"] - spot))["strikePrice"], spot


# ----------------------------
# FILTER ZONE (ATM ± 5)
# ----------------------------
def filter_zone(chain, atm):
    strikes = sorted([x["strikePrice"] for x in chain])
    atm_index = strikes.index(atm)

    zone = strikes[max(0, atm_index - 5): atm_index + 6]
    return [x for x in chain if x["strikePrice"] in zone]


# ----------------------------
# ENGINE
# ----------------------------
def run_engine():

    chain = load_data()

    atm, spot = find_atm(chain)
    zone = filter_zone(chain, atm)

    # ----------------------------
    # STEP 4: MAX BASE VALUES
    # ----------------------------
    x_oi = max(x["CE"]["openInterest"] for x in zone)
    x_vol = max(x["CE"]["totalTradedVolume"] for x in zone)

    y_oi = max(x["PE"]["openInterest"] for x in zone)
    y_vol = max(x["PE"]["totalTradedVolume"] for x in zone)

    # ----------------------------
    # STEP 8: PEAKS
    # ----------------------------
    ce_peak = max(zone, key=lambda x: x["CE"]["openInterest"])
    pe_peak = max(zone, key=lambda x: x["PE"]["openInterest"])

    ce_peak_strike = ce_peak["strikePrice"]
    pe_peak_strike = pe_peak["strikePrice"]

    # ----------------------------
    # STEP 9: SHRINK LOGIC (SINGLE RUN = NO HISTORY)
    # ----------------------------
    # Since no history yet → mark STABLE
    ce_dir = "STABLE"
    pe_dir = "STABLE"

    # ----------------------------
    # STEP 10: SENTIMENT
    # ----------------------------
    if ce_dir == "UP" and pe_dir == "UP":
        sentiment = "BULLISH"
    elif ce_dir == "DOWN" and pe_dir == "DOWN":
        sentiment = "BEARISH"
    else:
        sentiment = "RISKY"

    # ----------------------------
    # STEP 12: TRADE ENGINE
    # ----------------------------
    trades = {}

    ce = ce_peak_strike
    pe = pe_peak_strike

    if sentiment == "BULLISH":

        support = pe + 15
        support_sl = support - 10

        resistance = ce - 10
        resistance_sl = resistance + 10

        trades = {
            "BUY": {
                "entry": support,
                "sl": support_sl,
                "target_1": min([x["strikePrice"] for x in zone if x["strikePrice"] > support], default=ce),
                "target_2": ce
            },
            "SELL": {
                "entry": resistance,
                "sl": resistance_sl,
                "target_1": resistance - 15
            }
        }

    elif sentiment == "BEARISH":

        resistance = ce - 15
        resistance_sl = resistance + 10

        support = pe + 10
        support_sl = support - 10

        trades = {
            "SELL": {
                "entry": resistance,
                "sl": resistance_sl,
                "target_1": min([x["strikePrice"] for x in zone if x["strikePrice"] < resistance], default=pe),
                "target_2": pe
            },
            "BUY": {
                "entry": support,
                "sl": support_sl,
                "target_1": support - 15
            }
        }

    else:

        trades = {
            "BUY_PE_EXTREME": {
                "entry": pe + 10,
                "sl": pe - 10
            },
            "BUY_CE_EXTREME": {
                "entry": ce - 10,
                "sl": ce + 10
            }
        }

    # ----------------------------
    # OUTPUT
    # ----------------------------
    result = {
        "spot": spot,
        "atm": atm,
        "ce_peak": {"strike": ce, "oi": ce_peak["CE"]["openInterest"]},
        "pe_peak": {"strike": pe, "oi": pe_peak["PE"]["openInterest"]},
        "sentiment": sentiment,
        "trades": trades
    }

    return result


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    output = run_engine()

    with open("output/result.json", "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))
