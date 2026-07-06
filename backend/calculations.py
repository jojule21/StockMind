# calculations.py
# Real data implementation of the three functions services.py expects.
# Wraps the yahoo finance functions in market_data.py and the parallel
# monte carlo in monte_carlo.py, and converts their outputs into the
# response format the API returns. When this file is present,
# services.py uses it instead of mock_data automatically.

import time as time_module

import market_data
import monte_carlo

import services

# simulation settings for the monte carlo model
SIMULATIONS = 100000
CORES = 4


# fetches current prices for a list of tickers. tickers that fail or
# return a non-numeric price are skipped; if none succeed the whole
# call raises DataUnavailableError
def get_quotes(symbols):
    quotes = []
    for sym in symbols:
        try:
            info = market_data.get_stock_info(sym)
            price = info["current_price"]
            if not isinstance(price, (int, float)):
                continue
            quotes.append({
                "symbol": sym,
                "company": info["name"],
                "price": round(float(price), 2)
            })
        except Exception:
            continue
    if not quotes:
        raise services.DataUnavailableError("could not fetch any quotes")
    return quotes


# fetches daily price history for one ticker and converts the pandas
# dataframe rows into the {"timestamp", "close"} point list the chart
# endpoint returns
def get_history(symbol, days):
    try:
        df = market_data.get_price_history(symbol, period=str(days) + "d")
    except Exception:
        raise services.DataUnavailableError("history fetch failed for " + symbol)

    if df is None or len(df) == 0:
        raise services.DataUnavailableError("no history data for " + symbol)

    points = []
    for _, row in df.iterrows():
        points.append({
            "timestamp": row["Date"].strftime("%Y-%m-%dT%H:%M:%S"),
            "close": round(float(row["Close"]), 2)
        })

    try:
        info = market_data.get_stock_info(symbol)
        company = info["name"]
    except Exception:
        company = symbol

    return {
        "symbol": symbol,
        "company": company,
        # exchange and sector are not returned by get_stock_info yet,
        # the yfinance info dict has them under "exchange" and "sector"
        "exchange": "N/A",
        "sector": "N/A",
        "current_price": points[-1]["close"],
        "points": points
    }


# fetches the live spot price, converts the percent inputs to decimals,
# runs the monte carlo simulation, and packages the result with the
# status badge and timing info
def price_option(ticker, strike_price, option_type, time_to_expiry_years,
                 risk_free_rate_percent, volatility_percent, model):
    # an option whose expiration date already passed returns a Knocked
    # Out result without running any calculation
    if time_to_expiry_years <= 0:
        return {
            "theoretical_price": None,
            "status": "Knocked Out (Expired)",
            "model_used": "Monte Carlo",
            "simulations": None,
            "cpu_cores_used": None,
            "computation_time_seconds": None,
            "volatility_annualized_percent": volatility_percent,
            "spot_price": None,
        }

    # current stock price is needed as the simulation starting point
    try:
        info = market_data.get_stock_info(ticker)
        spot = info["current_price"]
    except Exception:
        raise services.DataUnavailableError("spot price fetch failed for " + ticker)
    if not isinstance(spot, (int, float)):
        raise services.DataUnavailableError("no valid spot price for " + ticker)
    spot = float(spot)

    # inputs arrive as percents (4.25 means 4.25%), the model expects
    # decimals (0.0425)
    r = risk_free_rate_percent / 100.0
    sigma = volatility_percent / 100.0

    # black_scholes and binomial are not implemented yet, so every
    # request currently runs monte carlo and is labeled as monte carlo
    start = time_module.perf_counter()
    price = monte_carlo.monte_carlo_option_price_parallel(
        spot, strike_price, r, sigma, time_to_expiry_years,
        option_type, SIMULATIONS, CORES)
    elapsed = time_module.perf_counter() - start

    # status badge from comparing spot price to strike
    if option_type == "call":
        in_money = spot > strike_price
        out_money = spot < strike_price
    else:
        in_money = spot < strike_price
        out_money = spot > strike_price
    if in_money:
        status = "In the Money (ITM)"
    elif out_money:
        status = "Out of the Money (OTM)"
    else:
        status = "At the Money (ATM)"

    return {
        "theoretical_price": round(float(price), 2),
        "status": status,
        "model_used": "Monte Carlo",
        "simulations": SIMULATIONS,
        "cpu_cores_used": CORES,
        "computation_time_seconds": round(elapsed, 3),
        "volatility_annualized_percent": volatility_percent,
        "spot_price": round(spot, 2),
    }
