# app.py
# Flask server for MarketMinds. Defines the API endpoints, validates
# incoming requests, and returns JSON responses to the frontend.

import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as CalcTimeout
from datetime import datetime

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

import services
from services import DataUnavailableError, DataStaleError

app = Flask(__name__)
CORS(app)  # allows the frontend to call this server from a different port

# max seconds an option calculation is allowed to take before the
# request returns a Knocked Out result instead of a price
CALC_TIMEOUT_SECONDS = 10

# how many seconds the live stream waits between price checks
STREAM_INTERVAL_SECONDS = 1.0

# tickers returned when the request doesn't specify any
DEFAULT_WATCHLIST = ["AAPL", "NVDA", "AMZN", "GOOGL", "TSLA", "META", "NFLX"]


# builds the standard error JSON: {"error": true, "message": "..."}
def error_response(message, status_code):
    return jsonify({"error": True, "message": message}), status_code


# GET /api/health
# reports whether the server is up and whether it is running on real
# yahoo finance data (calculations.py present) or mock data
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "using_real_data": services.using_real_data(),
        "server_time": datetime.now().isoformat()
    })


# GET /api/watchlist
# returns current prices for a list of tickers. accepts an optional
# ?symbols=AAPL,NVDA query param, otherwise uses the default list.
# response only contains symbol, company, and price to keep it small
@app.route("/api/watchlist")
def watchlist():
    symbols_param = request.args.get("symbols")
    if symbols_param:
        symbols = [s.strip().upper() for s in symbols_param.split(",") if s.strip()]
    else:
        symbols = DEFAULT_WATCHLIST

    try:
        quotes = services.get_quotes(symbols)
    except DataUnavailableError as e:
        return error_response(str(e), 503)

    return jsonify({
        "quotes": quotes,
        "last_updated": datetime.now().isoformat()
    })


# GET /api/watchlist/stream
# server-sent events version of the watchlist. the connection stays
# open and the server pushes a new JSON payload whenever any price
# changes, so the frontend updates without polling. the frontend
# consumes it with the built-in EventSource API
@app.route("/api/watchlist/stream")
def watchlist_stream():
    symbols_param = request.args.get("symbols")
    if symbols_param:
        symbols = [s.strip().upper() for s in symbols_param.split(",") if s.strip()]
    else:
        symbols = DEFAULT_WATCHLIST

    def event_stream():
        last_prices = None
        while True:
            try:
                quotes = services.get_quotes(symbols)
                # compare against the last push so events are only sent
                # when a price actually changed
                prices = [q["price"] for q in quotes]
                if prices != last_prices:
                    last_prices = prices
                    payload = {
                        "quotes": quotes,
                        "last_updated": datetime.now().isoformat()
                    }
                    yield "data: " + json.dumps(payload) + "\n\n"
            except DataUnavailableError as e:
                yield "data: " + json.dumps({"error": True, "message": str(e)}) + "\n\n"
            time.sleep(STREAM_INTERVAL_SECONDS)

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache"})


# GET /api/stock/<symbol>/history?days=7
# returns the time series used to draw the price chart: a list of
# {timestamp, close} points plus basic info about the company.
# days defaults to 7 and is capped at 365
@app.route("/api/stock/<symbol>/history")
def stock_history(symbol):
    symbol = symbol.strip().upper()

    try:
        days = int(request.args.get("days", 7))
    except ValueError:
        return error_response("days must be a whole number", 400)

    if days < 1 or days > 365:
        return error_response("days must be between 1 and 365", 400)

    try:
        history = services.get_history(symbol, days)
    except DataUnavailableError:
        return error_response(
            "Unable to retrieve market data from " + symbol +
            ". Please check your connection and try again.", 503)

    return jsonify(history)


# POST /api/options/price
# takes the option parameters as JSON, validates every field, converts
# the expiration date to years, then runs the pricing engine and
# returns the result. body format:
# {
#   "ticker": "AAPL", "strike_price": 150.00, "option_type": "call",
#   "expiration_date": "2026-12-18", "risk_free_rate": 4.25,
#   "volatility": 22.45, "model": "monte_carlo" (optional)
# }
@app.route("/api/options/price", methods=["POST"])
def options_price():
    body = request.get_json(silent=True)
    if body is None:
        return error_response("Request body must be JSON", 400)

    # validation: each field is checked and returns a 400 with a
    # specific message if it is missing or has the wrong type/range
    ticker = str(body.get("ticker", "")).strip().upper()
    if not ticker:
        return error_response("Ticker symbol is required", 400)

    try:
        strike = float(body.get("strike_price"))
    except (TypeError, ValueError):
        return error_response("Strike price must be a number", 400)
    if strike <= 0:
        return error_response("Strike price must be greater than 0", 400)

    option_type = str(body.get("option_type", "")).strip().lower()
    if option_type not in ("call", "put"):
        return error_response("Option type must be 'call' or 'put'", 400)

    exp_string = str(body.get("expiration_date", "")).strip()
    try:
        expiration = datetime.strptime(exp_string, "%Y-%m-%d").date()
    except ValueError:
        return error_response("Expiration date must be in YYYY-MM-DD format", 400)

    try:
        risk_free_rate = float(body.get("risk_free_rate"))
    except (TypeError, ValueError):
        return error_response("Risk-free rate must be a number", 400)
    if risk_free_rate < 0 or risk_free_rate > 100:
        return error_response("Risk-free rate must be between 0 and 100 percent", 400)

    try:
        volatility = float(body.get("volatility"))
    except (TypeError, ValueError):
        return error_response("Volatility must be a number", 400)
    if volatility <= 0 or volatility > 500:
        return error_response("Volatility must be between 0 and 500 percent", 400)

    model = str(body.get("model", "monte_carlo")).strip().lower()
    if model not in ("monte_carlo", "black_scholes", "binomial"):
        return error_response(
            "Model must be one of: monte_carlo, black_scholes, binomial", 400)

    # pricing models take time to expiration in years, so convert the
    # date into a fraction of a year from today
    days_left = (expiration - datetime.now().date()).days
    time_to_expiry_years = days_left / 365.0

    # the calculation runs in a separate thread so the request can
    # stop waiting after CALC_TIMEOUT_SECONDS. a timeout or stale data
    # returns a Knocked Out result, a failed data fetch returns a 503
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        services.price_option,
        ticker=ticker,
        strike_price=strike,
        option_type=option_type,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate_percent=risk_free_rate,
        volatility_percent=volatility,
        model=model,
    )
    try:
        result = future.result(timeout=CALC_TIMEOUT_SECONDS)
    except CalcTimeout:
        return jsonify(knocked_out_result("Calculation Timeout", model, volatility)), 200
    except DataStaleError:
        return jsonify(knocked_out_result("Stale Data", model, volatility)), 200
    except DataUnavailableError:
        return error_response(
            "Unable to retrieve market data from " + ticker +
            ". Please check your connection and try again.", 503)
    finally:
        executor.shutdown(wait=False)

    return jsonify(result)


MODEL_LABELS = {
    "monte_carlo": "Monte Carlo",
    "black_scholes": "Black-Scholes",
    "binomial": "Binomial",
}


# builds a result with the same shape as a normal pricing response but
# with null values and a Knocked Out status, so the frontend can fill
# the results panel with dashes instead of a price
def knocked_out_result(reason, model, volatility):
    return {
        "theoretical_price": None,
        "status": "Knocked Out (" + reason + ")",
        "model_used": MODEL_LABELS[model],
        "simulations": None,
        "cpu_cores_used": None,
        "computation_time_seconds": None,
        "volatility_annualized_percent": volatility,
        "spot_price": None,
    }


# catch-all handlers so failed requests always come back as JSON
# instead of flask's default HTML error pages
@app.errorhandler(404)
def not_found(e):
    return error_response("That endpoint does not exist", 404)


@app.errorhandler(405)
def wrong_method(e):
    return error_response("Wrong HTTP method for this endpoint", 405)


@app.errorhandler(500)
def server_error(e):
    return error_response("Internal server error", 500)


if __name__ == "__main__":
    print("MarketMinds backend starting...")
    print("Using real data:", services.using_real_data())
    app.run(host="0.0.0.0", port=5050, debug=True)
