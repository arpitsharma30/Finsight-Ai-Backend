from fastapi import APIRouter
import os
from groq import Groq
import yfinance as yf

router = APIRouter()

PORTFOLIOS = {
    "Low": {
        "holdings": [
            {"symbol": "HDFCBANK", "name": "HDFC Bank", "qty": 2, "buy_price": 1500, "exchange": "NSE"},
            {"symbol": "TCS",      "name": "TCS",       "qty": 1, "buy_price": 3200, "exchange": "NSE"},
        ],
        "allocation_types": [
            {"type": "Fixed Deposits",   "percent": 40},
            {"type": "Government Bonds", "percent": 30},
            {"type": "Mutual Funds",     "percent": 20},
            {"type": "Stocks",           "percent": 10},
        ],
        "tip": "Safe and steady. Perfect for beginners!"
    },
    "Medium": {
        "holdings": [
            {"symbol": "RELIANCE", "name": "Reliance Industries", "qty": 2, "buy_price": 2600, "exchange": "NSE"},
            {"symbol": "TCS",      "name": "TCS",                 "qty": 1, "buy_price": 3500, "exchange": "NSE"},
            {"symbol": "INFY",     "name": "Infosys",             "qty": 1, "buy_price": 1600, "exchange": "NSE"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank",           "qty": 1, "buy_price": 1500, "exchange": "NSE"},
        ],
        "allocation_types": [
            {"type": "Mutual Funds", "percent": 35},
            {"type": "Stocks",       "percent": 30},
            {"type": "SIP",          "percent": 20},
            {"type": "Bonds",        "percent": 15},
        ],
        "tip": "Good balance of risk and reward!"
    },
    "High": {
        "holdings": [
            {"symbol": "RELIANCE",   "name": "Reliance Industries", "qty": 3, "buy_price": 2400, "exchange": "NSE"},
            {"symbol": "ADANIENT",   "name": "Adani Enterprises",   "qty": 2, "buy_price": 1800, "exchange": "NSE"},
            {"symbol": "BAJFINANCE", "name": "Bajaj Finance",       "qty": 1, "buy_price": 6000, "exchange": "NSE"},
            {"symbol": "ICICIBANK",  "name": "ICICI Bank",          "qty": 2, "buy_price": 1100, "exchange": "NSE"},
            {"symbol": "WIPRO",      "name": "Wipro",               "qty": 3, "buy_price": 400,  "exchange": "NSE"},
        ],
        "allocation_types": [
            {"type": "Stocks",       "percent": 50},
            {"type": "Mutual Funds", "percent": 25},
            {"type": "Crypto",       "percent": 15},
            {"type": "SIP",          "percent": 10},
        ],
        "tip": "High risk high reward. Diversify always!"
    }
}

@router.get("/portfolio")
async def get_portfolio(risk_level: str = "Medium"):
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key) if api_key else None
    data = PORTFOLIOS.get(risk_level, PORTFOLIOS["Medium"])
    holdings = []
    total_value = 0
    total_cost = 0

    for h in data["holdings"]:
        try:
            ticker = yf.Ticker(f"{h['symbol']}.NS")
            current_price = round(ticker.fast_info.last_price, 2)
        except:
            current_price = h["buy_price"]

        value    = round(current_price * h["qty"], 2)
        cost     = round(h["buy_price"] * h["qty"], 2)
        gain_pct = round(((current_price - h["buy_price"]) / h["buy_price"]) * 100, 2)

        total_value += value
        total_cost  += cost

        holdings.append({
            "symbol":        h["symbol"],
            "name":          h["name"],
            "qty":           h["qty"],
            "buy_price":     h["buy_price"],
            "current_price": current_price,
            "value":         value,
            "gain_pct":      gain_pct,
            "exchange":      h["exchange"],
        })

    for h in holdings:
        h["allocation"] = round((h["value"] / total_value) * 100, 2)

    total_gain = round(total_value - total_cost, 2)
    gain_pct   = round(((total_value - total_cost) / total_cost) * 100, 2)

    try:
        ai_prompt = f"A student has a {risk_level} risk portfolio worth ₹{round(total_value)}. Give one short investment tip in 1 sentence."
        if not client:
            raise RuntimeError("Missing GROQ_API_KEY")
        ai_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": ai_prompt}],
            temperature=0.7,
        )
        ai_tip = ai_response.choices[0].message.content.strip()
    except:
        ai_tip = data["tip"]

    return {
        "risk_level":       risk_level,
        "total_value":      round(total_value, 2),
        "total_gain":       total_gain,
        "gain_pct":         gain_pct,
        "holdings":         holdings,
        "allocation_types": data["allocation_types"],
        "tip":              data["tip"],
        "ai_tip":           ai_tip,
    }