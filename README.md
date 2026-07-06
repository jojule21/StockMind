# StockMind (StockMind is an educational tool, not financial advice, use at your own risk)

CSCI 49900 capstone Summer 2026
Team: Joel Lee (backend), Will Gadson (data + math), Ishpreet Singh (frontend)

Stock watchlist + options pricing web app. Live prices come from yahoo finance, and the options calculator runs simulations.

## Repo layout

- backend/ - the flask API server (see backend/README.md for how to run it and the full endpoint docs)
- frontend/ - the web UI (Ishpreet)
- docs/ - proposal, slides, UI breakdown, and early prototypes

## Quick start (backend)

```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open backend/index.html in a browser to test the endpoints.
Full API docs are in backend/README.md.

## Who did what

- Joel: flask server, API endpoints, real-time SSE stream, timeout / knocked-out handling, mock data layer, the adapter (calculations.py) that connects Will's code to the server
- Will: yahoo finance data functions (market_data.py) and the parallel monte carlo engine (monte_carlo.py)
- Ishpreet: figma designs (docs/ui_breakdown.pdf) and the frontend
