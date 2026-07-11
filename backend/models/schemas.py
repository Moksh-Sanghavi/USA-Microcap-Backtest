"""
Pydantic request/response schemas for the backtest API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """Parameters controlling a single backtest run."""

    initial_capital: float = Field(
        default=100.0,
        gt=0,
        description="Starting cash ($). Also used as the capital floor: if the "
                    "portfolio dips below this between rebalances, fresh capital "
                    "is injected back up to this amount before the next period.",
    )
    num_stocks: int = Field(
        default=10,
        ge=1,
        description="Number of random tickers to select in each rebalance period.",
    )
    holding_period_weeks: int = Field(
        default=2,
        ge=1,
        description="Number of weeks each basket is held before liquidating and rebalancing.",
    )


class BacktestResponse(BaseModel):
    """Full result of a backtest run, split into the three reporting levels."""

    global_metrics: Dict[str, Any] = Field(
        description="Level 3: headline summary stats (final value, PnL, return %, "
                    "win rate, max drawdown, etc.)."
    )
    rebalance_summary: List[Dict[str, Any]] = Field(
        description="Level 2: one row per holding period (start/end value, PnL, return %)."
    )
    trade_ledger: List[Dict[str, Any]] = Field(
        description="Level 1: one row per individual stock position held during the backtest."
    )


class AverageStatsRequest(BaseModel):
    """Request to average metrics across the last N recorded backtest runs."""

    num_runs: int = Field(
        ge=1,
        le=100,
        description="How many of the most recent backtest runs to average over (1-100).",
    )


class AverageStatsResponse(BaseModel):
    """Averaged metrics across the requested number of most recent runs."""

    num_runs_requested: int
    num_runs_used: int
    avg_net_pnl: Optional[float] = Field(description="Average 'Overall Net PnL' across the runs.")
    avg_total_return_pct: Optional[float] = Field(description="Average 'Total Strategy Return (%)' across the runs.")
    avg_win_rate_pct: Optional[float] = Field(description="Average 'Win Rate (%)' across the runs.")
    oldest_run_timestamp: Optional[str] = None
    newest_run_timestamp: Optional[str] = None


class HistoryCountResponse(BaseModel):
    """How many backtest runs are currently recorded in history."""

    count: int
    max_history: int
