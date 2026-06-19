import json
import os

INPUT_FILE = "data/nifty_option_chain.json"
OUTPUT_FILE = "output/result.json"


def load_data():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)


def find_atm(strikes, spot):
    return min(strikes, key=lambda x: abs(x - spot))


def main():
    data = load_data()
    records = data["records"]

    chain = records["data"]
    spot = records["PE"]["totOI"]  # fallback (we override below)

    # FIX SPOT (correct source)
    spot = chain[0]["CE"]["underlyingValue"]

    strikes = [item["strikePrice"] for item in chain]

    atm = find_atm(strikes, spot)

    # ATM ± 5 range
    zone = [s for s in strikes if atm - 250 <= s <= atm + 250]  # approx step safe

    filtered = [x for x in chain if x["strikePrice"] in zone]

    # BASE MAX VALUES
    x_oi = max(x["CE"]["openInterest"] for x in filtered)
    x_vol = max(x["CE"]["totalTradedVolume"] for x in filtered)

    y_oi = max(x["PE"]["openInterest"] for x in filtered)
    y_vol = max(x["PE"]["totalTradedVolume"] for x in filtered)

    result = {
        "spot": spot,
        "atm": atm,
        "zone_count": len(filtered),
        "strikes": []
    }

    ce_peak = {"strike": 0, "oi": 0}
    pe_peak = {"strike": 0, "oi": 0}

    for item in filtered:
        ce = item["CE"]
        pe = item["PE"]
        strike = item["strikePrice"]

        ce_oi = ce["openInterest"]
        ce_vol = ce["totalTradedVolume"]

        pe_oi = pe["openInterest"]
        pe_vol = pe["totalTradedVolume"]

        ce_oi_pct = (ce_oi / x_oi * 100) if x_oi else 0
        ce_vol_pct = (ce_vol / x_vol * 100) if x_vol else 0

        pe_oi_pct = (pe_oi / y_oi * 100) if y_oi else 0
        pe_vol_pct = (pe_vol / y_vol * 100) if y_vol else 0

        oi_diff = ce_oi - pe_oi

        # peaks
        if ce_oi > ce_peak["oi"]:
            ce_peak = {"strike": strike, "oi": ce_oi}

        if pe_oi > pe_peak["oi"]:
            pe_peak = {"strike": strike, "oi": pe_oi}

        result["strikes"].append({
            "strike": strike,

            "ce_oi": ce_oi,
            "ce_oi_pct": round(ce_oi_pct, 2),
            "ce_vol": ce_vol,
            "ce_vol_pct": round(ce_vol_pct, 2),

            "pe_oi": pe_oi,
            "pe_oi_pct": round(pe_oi_pct, 2),
            "pe_vol": pe_vol,
            "pe_vol_pct": round(pe_vol_pct, 2),

            "oi_diff": oi_diff,

            "strong_ce": ce_oi_pct >= 75,
            "strong_pe": pe_oi_pct >= 75
        })

    result["ce_peak"] = ce_peak
    result["pe_peak"] = pe_peak

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print("DONE ✔ RESULT GENERATED")


if __name__ == "__main__":
    main()
