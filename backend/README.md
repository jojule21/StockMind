# MarketMinds Backend (Joel's part)

CSCI 49900 Summer 2026
Team: Ishpreet Singh (frontend), Will Gadson (data + math), Joel Lee (backend)

This is the python backend server. It handles the API endpoints and the
communication between the web frontend and the server. It does NOT do
the yahoo finance fetching or the options math, thats Will's part.
Until his module is done the server runs on mock data so we can all
keep working in parallel.

## How to run

```
pip install -r requirements.txt
python app.py
```

Server runs at http://localhost:5000. To check its up:

```
curl http://localhost:5000/api/health
```

"using_real_data": false means its on mock data (Will's file isnt
plugged in yet). You can also open index.html in a browser to test
every endpoint with buttons.

## Endpoints (for Ishpreet)

### GET /api/health
Returns { "status": "ok", "using_real_data": true/false, "server_time": ... }

### GET /api/watchlist
Screen 1. One-time fetch, use it for the initial page load.
Optional ?symbols=AAPL,NVDA for specific tickers.

```json
{
  "quotes": [
    { "symbol": "AAPL", "company": "Apple Inc.", "price": 150.45 }
  ],
  "last_updated": "2026-07-06T10:24:15"
}
```

### GET /api/watchlist/stream  (real-time)
Screen 1, the real-time version. Server sent events - the server keeps
the connection open and pushes new prices the moment they change, no
polling needed. This is what makes the update flash instant. Frontend:

```js
const es = new EventSource("http://localhost:5000/api/watchlist/stream");
es.onmessage = (e) => {
  const data = JSON.parse(e.data); // same shape as GET /api/watchlist
};
```

### GET /api/stock/AAPL/history?days=7
Screen 2, chart data. days defaults to 7, max 365.

```json
{
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "current_price": 150.45,
  "points": [
    { "timestamp": "2026-06-29T10:00:00", "close": 142.10 }
  ]
}
```

### POST /api/options/price
Screen 3. Send JSON:

```json
{
  "ticker": "AAPL",
  "strike_price": 150.00,
  "option_type": "call",
  "expiration_date": "2026-12-18",
  "risk_free_rate": 4.25,
  "volatility": 22.45,
  "model": "monte_carlo"
}
```

model is optional (default monte_carlo, also takes black_scholes and
binomial). Response has everything the results panel shows:

```json
{
  "theoretical_price": 4.25,
  "status": "In the Money (ITM)",
  "model_used": "Monte Carlo",
  "simulations": 100000,
  "cpu_cores_used": 4,
  "computation_time_seconds": 0.842,
  "volatility_annualized_percent": 22.45,
  "spot_price": 150.45
}
```

### "Knocked Out" (our team definition)
In our system knocked out means the real-time guarantee failed (not the
finance textbook barrier option meaning). 3 cases:

1. calculation took longer than 10 seconds -> "Knocked Out (Calculation Timeout)"
2. the market data wasnt fresh -> "Knocked Out (Stale Data)"
3. the expiration date already passed -> "Knocked Out (Expired)"

For 1 and 2 the response is still a 200 with the normal shape but
theoretical_price is null and status says knocked out. Show the badge
and dashes instead of a price.

### Errors (screen 4)
Every error is JSON, never an html page:

```json
{ "error": true, "message": "Unable to retrieve market data from AAPL. Please check your connection and try again." }
```

- 400 = bad input (show the message under the form)
- 503 = market data unavailable (show the red error panel + recalculate button)

## How Will plugs in

Make a file called calculations.py in this folder. The server finds it
automatically on startup, no changes to my code needed. It needs these
3 functions:

```python
def get_quotes(symbols):
    # symbols: list of tickers like ["AAPL", "NVDA"]
    # return: list of { "symbol": str, "company": str, "price": float }
    # raise services.DataUnavailableError if yahoo fails

def get_history(symbol, days):
    # return: { "symbol", "company", "exchange", "sector",
    #           "current_price", "points": [ {"timestamp", "close"} ] }
    # raise services.DataUnavailableError if yahoo fails

def price_option(ticker, strike_price, option_type, time_to_expiry_years,
                 risk_free_rate_percent, volatility_percent, model):
    # option_type: "call" or "put"
    # model: "monte_carlo", "black_scholes", or "binomial"
    # note rates/volatility come in as percents (4.25 means 4.25%)
    # return: { "theoretical_price", "status", "model_used", "simulations",
    #           "cpu_cores_used", "computation_time_seconds",
    #           "volatility_annualized_percent", "spot_price" }
    # raise services.DataUnavailableError if the ticker lookup fails
    # raise services.DataStaleError if the data isnt real-time/fresh
```

All input validation already happens in app.py before these get called.
The 10 second timeout is handled on my side too, Will doesnt need to do
anything for that.
