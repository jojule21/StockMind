# services.py
# Middle layer between the server (app.py) and the data/math code.
# On startup it checks whether calculations.py exists: if it does, all
# calls go to the real implementation, otherwise they go to mock_data.
# app.py only ever imports from this file, so swapping between real
# and mock data requires no code changes anywhere else.

import mock_data


class DataUnavailableError(Exception):
    # raised when market data cannot be fetched at all (API down,
    # invalid ticker, no internet). the server converts this into a
    # 503 error response
    pass


class DataStaleError(Exception):
    # raised when data was fetched but is too old to be considered
    # real-time. the server converts this into a Knocked Out result
    pass


# detect whether the real implementation is available
try:
    import calculations as engine
    _REAL = True
    print("services: found calculations.py, using real data")
except ImportError:
    engine = None
    _REAL = False
    print("services: no calculations.py yet, using mock data")


def using_real_data():
    return _REAL


# returns a list of {"symbol", "company", "price"} dicts for the
# requested tickers
def get_quotes(symbols):
    if _REAL:
        return engine.get_quotes(symbols)
    return mock_data.get_quotes(symbols)


# returns chart data for one stock:
# {"symbol", "company", "exchange", "sector", "current_price",
#  "points": [{"timestamp", "close"}, ...]}
def get_history(symbol, days):
    if _REAL:
        return engine.get_history(symbol, days)
    return mock_data.get_history(symbol, days)


# returns the full pricing result:
# {"theoretical_price", "status", "model_used", "simulations",
#  "cpu_cores_used", "computation_time_seconds",
#  "volatility_annualized_percent", "spot_price"}
def price_option(ticker, strike_price, option_type, time_to_expiry_years,
                 risk_free_rate_percent, volatility_percent, model):
    if _REAL:
        return engine.price_option(
            ticker, strike_price, option_type, time_to_expiry_years,
            risk_free_rate_percent, volatility_percent, model)
    return mock_data.price_option(
        ticker, strike_price, option_type, time_to_expiry_years,
        risk_free_rate_percent, volatility_percent, model)
