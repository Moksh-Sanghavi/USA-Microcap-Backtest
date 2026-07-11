"""
API route definitions for the backtest service.
"""

from fastapi import APIRouter, HTTPException

from core.engine import (
    MAX_HISTORY,
    BacktestEngineError,
    compute_average_stats,
    get_history_count,
    run_backtest_pipeline,
)
from models.schemas import (
    AverageStatsRequest,
    AverageStatsResponse,
    BacktestRequest,
    BacktestResponse,
    HistoryCountResponse,
)

router = APIRouter(prefix="/api/v1", tags=["backtest"])


@router.post("/backtest", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """
    Run one random-selection, fixed-holding-period micro-cap backtest and
    return the three reporting levels: global metrics, rebalance summary,
    and the detailed trade ledger.
    """
    try:
        result = run_backtest_pipeline(
            initial_capital=request.initial_capital,
            num_stocks=request.num_stocks,
            holding_period_weeks=request.holding_period_weeks,
        )
    except BacktestEngineError as exc:
        # Data-availability problems: empty yfinance response, rate limiting,
        # no eligible tickers for the requested basket size, etc. These are
        # the caller's fault or an upstream data issue, not a server bug.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 -- last-resort guard for unexpected engine errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while running the backtest: {exc}",
        ) from exc

    return BacktestResponse(**result)


@router.post("/backtest/average", response_model=AverageStatsResponse)
def get_average_stats(request: AverageStatsRequest) -> AverageStatsResponse:
    """
    Average Net PnL, Total Return (%), and Win Rate (%) across the last
    `num_runs` recorded backtest runs (each POST /backtest call is recorded
    to history). 400s if fewer than `num_runs` runs have been recorded yet.
    """
    try:
        result = compute_average_stats(request.num_runs)
    except BacktestEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while computing average stats: {exc}",
        ) from exc

    return AverageStatsResponse(**result)


@router.get("/backtest/history-count", response_model=HistoryCountResponse)
def history_count() -> HistoryCountResponse:
    """How many backtest runs are currently recorded (out of the 100-run cap)."""
    return HistoryCountResponse(count=get_history_count(), max_history=MAX_HISTORY)
