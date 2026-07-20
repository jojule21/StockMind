# MarketMind

> MarketMind is an educational tool, not financial advice. Use at your own risk.

Stock watchlist + options pricing web app that gives everyday retail investors access to financial tools on their phones. Live prices come from Yahoo Finance, and the options calculator runs Monte Carlo simulations.

**CSCI 49900 Capstone — Summer 2026**
Team: Joel Lee (backend), Will Gadson (data + math), Ishpreet Singh (frontend)

<!-- TODO: add a screenshot or demo GIF once the frontend is wired up -->

## Architecture

```
┌──────────────┐   HTTP / SSE    ┌─────────────────────────────┐
│   Frontend    │ ◀────────────▶ │        Flask API (app.py)    │
│  (Ishpreet)   │                │  REST endpoints + real-time  │
└──────────────┘                │  SSE price stream, timeout & │
                                │  knocked-out handling        │
                                └──────────┬──────────────────┘
                                           │ adapter (calculations.py)
                              ┌────────────┴────────────┐
                              ▼                         ▼
                   ┌──────────────────┐      ┌────────────────────┐
                   │  market_data.py   │      │   monte_carlo.py    │
                   │  Yahoo Finance    │      │  parallel Monte     │
                   │  live data (Will) │      │  Carlo engine (Will)│
                   └──────────────────┘      └────────────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │   mock_data.py    │  ← fallback so the frontend
                   │  (development)    │    works without live data
                   └──────────────────┘
```

**Reliability model:** "knocked out" here means the real-time guarantee failed (not the barrier-option meaning) — a calculation exceeded its 10-second budget, market data went stale, or the option expired. The API still returns 200 with `theoretical_price: null` and a status the UI renders as a badge.

## Repo layout

- `backend/` — the Flask API server (see [backend/README.md](backend/README.md) for how to run it and the full endpoint docs)
- `frontend/` — the web UI (Ishpreet)
- `docs/` — proposal, slides, UI breakdown, and early prototypes

## Quick start (backend)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `backend/index.html` in a browser to test the endpoints, or:

```bash
curl http://localhost:5000/api/health
```

`"using_real_data": false` means it's running on mock data.

## Who did what

- **Joel:** Flask server, API endpoints, real-time SSE stream, timeout/knocked-out handling, mock data layer, and the adapter (`calculations.py`) connecting Will's engine to the server
- **Will:** Yahoo Finance data functions (`market_data.py`) and the parallel Monte Carlo engine (`monte_carlo.py`)
- **Ishpreet:** Figma designs (`docs/ui_breakdown.pdf`) and the frontend
