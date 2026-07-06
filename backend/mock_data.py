# mock_data.py
# Placeholder implementations of the three data functions. Used
# automatically by services.py whenever calculations.py is not present,
# so the server and frontend can run without a live data source.
# Prices and companies match the figma mockups.

import random
import time
from datetime import datetime, timedelta

# symbol -> (company name, base price, exchange, sector)
COMPANIES = {
    "AAPL":  ("Apple Inc.",          150.45, "NASDAQ", "Technology"),
    "NVDA":  ("NVIDIA Corp.",        127.82, "NASDAQ", "Technology"),
    "AMZN":  ("Amazon.com Inc.",     186.22, "NASDAQ", "Consumer Cyclical"),
    "GOOGL": ("Alphabet Inc.",      2811.34, "NASDAQ", "Technology"),
    "TSLA":  ("Tesla, Inc.",         172.36, "NASDAQ", "Consumer Cyclical"),
    "META":  ("Meta Platforms Inc.", 499.13, "NASDAQ", "Technology"),
    "NFLX":  ("Netflix, Inc.",       615.27, "NASDAQ", "Communication Services"),
}


# returns the base price moved randomly by up to +/-0.5% so repeated
# calls produce slightly different values, which lets the live stream
# and the frontend update flash behave like they would with real data
def _fake_price(base):
    return round(base * random.uniform(0.995, 1.005), 2)


def get_quotes(symbols):
    quotes = []
    for sym in symbols:
        if sym in COMPANIES:
            name, base, _, _ = COMPANIES[sym]
            quotes.append({
                "symbol": sym,
                "company": name,
                "price": _fake_price(base)
            })
        # symbols not in the table are left out of the response
    return quotes


def get_history(symbol, days):
    # imported inside the function because services imports this file,
    # importing at the top would be a circular import
    from services import DataUnavailableError

    if symbol not in COMPANIES:
        raise DataUnavailableError("unknown ticker in mock mode: " + symbol)

    name, base, exchange, sector = COMPANIES[symbol]

    # generates a random walk with a slight upward drift that ends
    # near the base price, 8 points per day
    points = []
    price = base * 0.94
    total_points = days * 8
    start = datetime.now() - timedelta(days=days)
    for i in range(total_points):
        ts = start + timedelta(days=days * i / total_points)
        price = price * random.uniform(0.997, 1.004)
        points.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "close": round(price, 2)
        })

    return {
        "symbol": symbol,
        "company": name,
        "exchange": exchange,
        "sector": sector,
        "current_price": points[-1]["close"],
        "points": points
    }


def price_option(ticker, strike_price, option_type, time_to_expiry_years,
                 risk_free_rate_percent, volatility_percent, model):
    from services import DataUnavailableError

    if ticker not in COMPANIES:
        raise DataUnavailableError("unknown ticker in mock mode: " + ticker)

    spot = COMPANIES[ticker][1]

    # determine the status badge by comparing spot price to strike.
    # an already-expired option is Knocked Out
    if time_to_expiry_years <= 0:
        status = "Knocked Out (Expired)"
    elif option_type == "call":
        if spot > strike_price:
            status = "In the Money (ITM)"
        elif spot < strike_price:
            status = "Out of the Money (OTM)"
        else:
            status = "At the Money (ATM)"
    else:
        if spot < strike_price:
            status = "In the Money (ITM)"
        elif spot > strike_price:
            status = "Out of the Money (OTM)"
        else:
            status = "At the Money (ATM)"

    model_labels = {
        "monte_carlo": "Monte Carlo",
        "black_scholes": "Black-Scholes",
        "binomial": "Binomial",
    }

    # returns a plausible placeholder number, not a real model output.
    # the short sleep keeps the frontend's processing animation visible
    time.sleep(0.4)
    fake_price = round(abs(spot - strike_price) * 0.35 + spot * 0.012, 2)

    return {
        "theoretical_price": fake_price,
        "status": status,
        "model_used": model_labels[model],
        "simulations": 100000 if model == "monte_carlo" else None,
        "cpu_cores_used": 4 if model == "monte_carlo" else 1,
        "computation_time_seconds": 0.842,
        "volatility_annualized_percent": volatility_percent,
        "spot_price": spot
    }
