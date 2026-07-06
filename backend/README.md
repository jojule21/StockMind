# MarketMinds Backend (Joel's part)

CSCI 49900 Summer 2026
Team: Ishpreet Singh (frontend), Will Gadson (data + math), Joel Lee (backend)

This is the python backend server. 

## How to run

```
pip install -r requirements.txt
python app.py
```

Server runs at http://localhost:5000. To check its up:

```
curl http://localhost:5000/api/health
```

"using_real_data": false means its on mock data. 

## Endpoints (for Ishpreet)

### GET /api/health
Returns { "status": "ok", "using_real_data": true/false, "server_time": ... }

### Reliability Check
In our system knocked out means the real-time guarantee failed (not the
finance textbook barrier option meaning). 3 cases:

1. calculation took longer than 10 seconds -> "Knocked Out (Calculation Timeout)"
2. the market data wasnt fresh -> "Knocked Out (Stale Data)"
3. the expiration date already passed -> "Knocked Out (Expired)"

For 1 and 2 the response is still a 200 with the normal shape but
theoretical_price is null and status says knocked out. Show the badge
and dashes instead of a price.
