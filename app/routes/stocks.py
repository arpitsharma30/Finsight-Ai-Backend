from fastapi import APIRouter, Query
import yfinance as yf
import httpx

router = APIRouter()

def fetch_stock(sym, display_symbol, exchange):
    try:
        ticker = yf.Ticker(sym)
        info = ticker.fast_info
        price = info.last_price
        prev = info.previous_close
        if not price or not prev or price <= 0:
            return None
        change = round(((price - prev) / prev) * 100, 2)
        try:
            name = ticker.info.get("longName") or ticker.info.get("shortName") or display_symbol
        except:
            name = display_symbol
        return {
            "symbol": display_symbol,
            "name": name,
            "price": round(price, 2),
            "change": change,
            "exchange": exchange
        }
    except:
        return None


async def search_yahoo(query: str):
    """Use Yahoo Finance search API to find matching ticker symbols"""
    url = "https://query1.finance.yahoo.com/v1/finance/search"
    params = {
        "q": query,
        "quotesCount": 6,
        "newsCount": 0,
        "listsCount": 0,
    }
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(url, params=params, headers=headers)
        data = resp.json()
        quotes = data.get("quotes", [])
        results = []
        for q in quotes:
            sym = q.get("symbol", "")
            name = q.get("longname") or q.get("shortname") or sym
            exchange = q.get("exchange", "")
            results.append((sym, name, exchange))
        return results


@router.get("/stocks")
async def get_stocks(symbol: str = Query(None)):
    if symbol:
        # Step 1: Use Yahoo search API to find matching symbols
        try:
            matches = await search_yahoo(symbol)
        except Exception:
            matches = []

        # Step 2: Fetch price for each match, return first valid one
        for sym, name, exchange in matches:
            try:
                ticker = yf.Ticker(sym)
                info = ticker.fast_info
                price = info.last_price
                prev = info.previous_close
                if not price or not prev or price <= 0:
                    continue
                change = round(((price - prev) / prev) * 100, 2)
                return {
                    "stocks": [{
                        "symbol": sym,
                        "name": name,
                        "price": round(price, 2),
                        "change": change,
                        "exchange": exchange
                    }]
                }
            except:
                continue

        return {
            "stocks": [],
            "error": f"No results found for '{symbol}'."
        }

    # Default top Indian stocks
    default_symbols = [
        ("RELIANCE.NS", "RELIANCE", "NSE"),
        ("TCS.NS", "TCS", "NSE"),
        ("INFY.NS", "INFY", "NSE"),
        ("HDFCBANK.NS", "HDFCBANK", "NSE"),
        ("WIPRO.NS", "WIPRO", "NSE"),
        ("BAJFINANCE.NS", "BAJFINANCE", "NSE"),
        ("ICICIBANK.NS", "ICICIBANK", "NSE"),
    ]
    result = []
    for sym, display, exchange in default_symbols:
        stock = fetch_stock(sym, display, exchange)
        if stock:
            result.append(stock)
    return {"stocks": result if result else []}