"""
FastAPI application entry point.

Run with:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as backtest_router

app = FastAPI(
    title="Micro-Cap Backtest API",
    description="REST API wrapper around a random-selection, fixed-holding-period "
                 "backtesting engine for US micro-cap stocks.",
    version="1.0.0",
)

# Allow the local frontend dev server to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backtest_router)


@app.get("/")
def health_check():
    """Simple liveness check."""
    return {"status": "ok", "service": "microcap-backtest-api"}
