"""
Core backtesting engine: random-selection, fixed-holding-period baseline
strategy for US micro-cap stocks.

This mirrors the logic validated in the standalone microcap_backtest.py CLI
script, refactored so it can be driven with per-request parameters (initial
capital, basket size, holding period) instead of module-level constants, and
so its outputs come back as JSON-safe dicts rather than pandas DataFrames.
"""

import json
import os
import re
import time
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Fixed engine configuration (not part of the per-request API surface).
# ---------------------------------------------------------------------------

# Anchor all relative paths to this file's own directory, not the process's
# current working directory -- otherwise the cache/results location silently
# depends on where uvicorn happens to be launched from.
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CORE_DIR)

LOOKBACK_DAYS = 365  # rolling 1-year lookback window

USE_CACHE = True
CACHE_MAX_AGE_HOURS = 24
CACHE_DIR = os.path.join(PROJECT_ROOT, "price_cache")
CACHE_DATA_FILE = os.path.join(CACHE_DIR, "daily_prices.csv")
CACHE_META_FILE = os.path.join(CACHE_DIR, "cache_meta.json")

# Rolling history of past backtest runs, used for the "average of last N
# runs" feature. Persisted to disk (not just in-memory) so history survives
# server restarts. Only the MAX_HISTORY most recent runs are kept -- that's
# also the hard ceiling on how many runs a client can request an average
# over, so nothing more ever needs to be retained.
HISTORY_FILE = os.path.join(PROJECT_ROOT, "backtest_history.json")
MAX_HISTORY = 100

# Representative sample of ~500 US micro-cap tickers spanning biotech/pharma,
# tech/semis, industrials, energy/materials, financials, consumer/retail,
# REITs, transportation, and media/telecom. Best-effort illustrative universe
# compiled from general market knowledge, NOT a scraped live snapshot of
# official Russell Microcap / IWC constituents -- some names may have since
# merged, uplisted past micro-cap, or delisted. That's fine: fetch_price_data()
# below automatically drops anything that fails to download or has
# insufficient trading history.
MICROCAP_UNIVERSE = [
    # --- Biotech / Pharma ---
    "VHC", "EVOL", "NYMX", "CDXC", "ADMA", "AEHR", "AEYE", "AGEN", "ALDX",
    "ANIK", "ARQT", "ATEC", "AVXL", "BCRX", "BIOL", "CARA", "CEMI", "ETON",
    "IRWD", "MNKD", "OCUL", "AKBA", "AMRN", "APLT", "AQST", "ARDX", "ATOS",
    "AVIR", "CDTX", "CERS", "CLDX", "CLRB", "CLSD", "CORT", "CRIS", "CTMX",
    "CYCC", "DVAX", "EIGR", "ENTA", "ESPR", "FGEN", "GOSS", "HRTX", "IMGN",
    "INFI", "IOVA", "KPTI", "LJPC", "MCRB", "MGNX", "NKTR", "OCGN", "ONCT",
    "PBYI", "PGEN", "PHIO", "PRQR", "PTGX", "RCUS", "RIGL", "SGMO", "SNDX",
    "SPPI", "STOK", "SUPN", "SYRS", "TGTX", "TNXP", "VBLT", "VCEL", "VNDA",
    "VRCA", "VSTM", "VYGR", "XENE", "ZYNE", "ANAB", "AXSM",

    # --- Technology / Software / Semis ---
    "EVLV", "IMMR", "MITK", "SITM", "AXTI", "CEVA", "CREX", "DSP",
    "DGII", "DLTH", "EGHT", "EVOP", "EXTR", "GSIT", "IDN", "INVE", "IPWR",
    "ISSC", "KOPN", "LGL", "LTRX", "MGIC", "MOBQ", "MVIS", "NTGR", "NVEC",
    "OBLG", "ODC", "OPTT", "PCTI", "PIXY", "QUIK", "RMBL", "SCWX", "SGH",
    "SIFY", "SILC", "SPWH", "SSYS", "TAYD", "TESS", "UCTT", "VIAV", "VUZI",
    "WISA", "WKHS", "XPEL", "ZIXI",

    # --- Industrials / Manufacturing ---
    "AIRT", "APOG", "ASTE", "CLFD", "CPSH", "CRAI", "CUTR", "DAKT", "DXPE",
    "EPAC", "FLXS", "GNCA", "HAYN", "HURC", "IEC", "AMSC", "ASYS", "BLBD",
    "CIR", "CMCO", "CVU", "DLX", "DXLG", "ELSE", "ENZ", "FSS",
    "GBX", "GENC", "HLIO", "HURN", "IIIN", "KAMN", "KVHI", "LAKE", "LMB",
    "MLKN", "MOD", "MYRG", "NPK", "NX", "OFLX", "OSIS", "PATK", "PLPC",
    "PRLB", "RCKY", "SXI", "TGI", "TRS", "UFPT", "UNF", "UFI",

    # --- Energy / Materials / Mining ---
    "GEVO", "AMPY", "AR", "BATL", "BORR", "BRY", "CEIX", "CLB",
    "CPE", "CRK", "DK", "EGY", "ESTE", "FANG", "GPOR", "GTE", "HUSA",
    "ICD", "KOS", "MGY", "NBR", "NOG", "NRP", "PARR", "PDS", "REI",
    "RES", "SBOW", "SD", "SM", "TALO", "TELL", "VET", "VTLE",
    "WTI", "AXU", "CDE", "EGO", "GATO", "HL", "MUX", "NAK", "PAAS",
    "SILV", "SVM", "THM", "USAS",

    # --- Financials / Banks / Insurance ---
    "BHE", "BOOT", "CENT", "CODA", "CVGW", "ANDE", "BFST", "BHRB",
    "BUSE", "BWFG", "CAC", "CASH", "CATC", "CBFV", "CFFI", "CFFN", "CHMG",
    "CIVB", "CTBI", "CZFS", "CZWI", "EBTC", "ESQ", "FBIZ", "FCAP", "FMBH",
    "FMNB", "FNLC", "FRBA", "FSBW", "GCBC", "HFWA", "HMNF", "HONE",
    "IROQ", "ISBA", "KFFB", "LARK", "MBWM", "MPB", "NFBK", "NKSH", "OVLY",
    "PFIS", "PGC", "PKBK", "PVBC", "RBB", "RRBI", "SFST", "SMBC", "TBNK",
    "TFSL", "TMP", "UBFO", "UVSP",

    # --- Consumer / Retail ---
    "BGFV", "DXLG", "EYE", "FIZZ", "HAIN", "JJSF", "KIRK", "LOVE",
    "MOV", "NATH", "NWY", "PLAY", "SCVL", "SHOO", "SPTN", "TITN",
    "TUES", "VRA", "WINA", "YETI", "ZUMZ", "CATO", "CONN", "CTRN",
    "DBI", "EXPR", "FRAN", "GCO", "HIBB", "JOUT",

    # --- REITs / Real Estate ---
    "AHH", "BRT", "CDOR", "CIO", "CLPR", "CTO", "GOOD", "GYRO", "HIW",
    "ILPT", "IRT", "MDV", "NXRT", "OPI", "PDM", "PLYM", "RLJ", "SVC",
    "UMH", "UNIT", "WHLR", "WSR",

    # --- Transportation / Shipping / Logistics ---
    "ATSG", "CVLG", "DSKE", "ECHO", "EGLE", "GNK", "GSL", "HTLD", "MATX",
    "PANL", "PATI", "SBLK", "SNDR", "TGH", "USAK", "USDP", "WERN", "YRCW",

    # --- Media / Telecom / Other ---
    "AMCX", "ATEX", "BBGI", "CCUR", "CMBM", "GNSS", "GOGO", "GSAT", "IDT",
    "ORBC", "SALM", "SGA", "SSP", "TDS", "USM", "VNET", "VSAT",

    # --- Additional Biotech / Pharma ---
    "ACRS", "ADAP", "ADIL", "AGLE", "AKRO", "ALT", "AMPH", "AMTX", "ANIP",
    "APRE", "AQB", "ARCT", "ARQL", "ASND", "ASRT", "AUTL", "AVTX", "AXGN",
    "BDTX", "BIOC", "BMEA", "BNTC", "BPTH", "BTAI", "CABA", "CARM", "CDMO",
    "CGEM", "CLGN", "CMPS", "COGT", "CPRX", "CRBP", "CRVS", "CTXR", "CVM",
    "CYTK", "DMTK", "DRIO", "EBS", "ELDN", "EOLS", "EVLO", "EVOK", "EXAI",
    "FBIO", "FDMT", "GERN", "GLSI", "HALO", "HCTI", "HRMY", "IBRX", "ICCC",
    "IMRA", "IMTX", "INMB", "INO", "INVA", "ITOS", "JAGX", "KALA", "KALV",
    "KOD", "KRON", "KURA", "LIAN", "LPCN", "LXRX", "MASI", "MDNA", "MEIP",

    # --- Additional Technology / Industrials ---
    "ACLS", "ADTN", "ALOT", "AMSWA", "APPS", "ARLO", "ASUR", "AVNW", "BAND",
    "BCOV", "BOOM", "CALX", "CASA", "CGNX", "CMTL", "CSPI", "DAIO",
    "DGLY", "DIOD", "DSGN", "EMKR", "FARO", "FORM", "HEAR",
    "IMOS", "INTZ", "IPGP", "ITRI", "JBSS", "KLIC", "LASR", "LPTH", "LYTS",
    "MTSC", "NCTY", "NVTS", "OSS", "PLAB", "PRSO", "RSSS", "SGMA",
    "SMTC", "SPNS", "SYNA", "TACT", "TTEC", "UEIC", "VICR", "VOXX",

    # --- Additional Energy / Materials / Industrials ---
    "AMRC", "APAM", "BRN", "CENX", "CMP", "CRS", "CSTM", "ENS",
    "ESE", "FUL", "GRC", "HAYW", "HWKN", "INSW", "IOSP", "KALU",
    "KOP", "MATW", "MTRN", "MTX", "NEU", "NL", "OI", "OLN", "PKE",
    "PLOW", "POWL", "RPM", "SCHN", "SHYF", "SXC", "TG", "TROX", "WLK",
    "WOR",

    # --- Additional Financials / Consumer / Other ---
    "ALRS", "AMAL", "AROW", "AUBN", "BFIN", "BHB", "BOTJ", "BSRR", "BWB",
    "CCNE", "CFB", "CHCO", "CNOB", "CPF", "CWBC", "ECBK", "EFSC",
    "ESXB", "FCBC", "FCCO", "FFIN", "FRME", "FUNC", "GABC", "GSBC", "HBCP",
    "HMST", "HTBI", "HTLF", "HWBK", "IBCP", "MBIN", "MCBC", "MFNC", "MSBI",
    "NBTB", "NWFL", "OPOF", "OSBC", "PFC", "PPBI", "PWOD", "QCRH", "RBCAA",
    "RVSB", "SFNC", "SMBK", "SSBI", "SYBT", "THFF", "TRMK", "UBSI", "UCBI",
    "WASH", "WNEB", "WSBC", "WTBA",
]
MICROCAP_UNIVERSE = list(dict.fromkeys(MICROCAP_UNIVERSE))[:500]


class BacktestEngineError(Exception):
    """Raised for data-availability problems (empty download, no eligible
    tickers, etc.) so the API layer can distinguish them from genuine bugs
    and return a clean 4xx/5xx instead of a raw traceback."""


# ---------------------------------------------------------------------------
# Data sourcing (with local cache)
# ---------------------------------------------------------------------------

def _load_from_cache(tickers, start, end):
    if not (os.path.exists(CACHE_DATA_FILE) and os.path.exists(CACHE_META_FILE)):
        return None

    with open(CACHE_META_FILE, "r") as f:
        meta = json.load(f)

    age_hours = (time.time() - meta["fetched_at"]) / 3600.0
    if age_hours > CACHE_MAX_AGE_HOURS:
        return None

    cached_tickers = set(meta["tickers"])
    if not set(tickers).issubset(cached_tickers):
        return None

    cached_start = datetime.fromisoformat(meta["start"])
    cached_end = datetime.fromisoformat(meta["end"])
    if start < cached_start or end > cached_end:
        return None

    price_df = pd.read_csv(CACHE_DATA_FILE, index_col=0, parse_dates=True)
    price_df = price_df[[t for t in tickers if t in price_df.columns]]
    return price_df


def _save_to_cache(price_df, requested_tickers, start, end):
    os.makedirs(CACHE_DIR, exist_ok=True)
    price_df.to_csv(CACHE_DATA_FILE)
    meta = {
        "tickers": list(requested_tickers),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "fetched_at": time.time(),
    }
    with open(CACHE_META_FILE, "w") as f:
        json.dump(meta, f)


def fetch_price_data(tickers, start, end):
    """
    Download daily (auto-adjusted) Close prices for the given tickers,
    transparently using a local cache to avoid re-hitting yfinance on every
    request. Raises BacktestEngineError if no usable data comes back at all.
    """
    if USE_CACHE:
        cached = _load_from_cache(tickers, start, end)
        if cached is not None:
            return cached

    try:
        raw = yf.download(
            tickers,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
    except Exception as exc:  # noqa: BLE001 -- yfinance can raise many transient error types
        raise BacktestEngineError(f"yfinance download failed: {exc}") from exc

    if raw is None or raw.empty:
        raise BacktestEngineError(
            "yfinance returned no data at all -- possible rate limiting or network issue."
        )

    prices = {}
    for ticker in tickers:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                if ticker not in raw.columns.get_level_values(0):
                    continue
                series = raw[ticker]["Close"]
            else:
                series = raw["Close"]
            if series.dropna().empty:
                continue
            prices[ticker] = series
        except (KeyError, TypeError):
            continue

    price_df = pd.DataFrame(prices)
    if price_df.empty:
        raise BacktestEngineError(
            "None of the requested tickers returned usable price data."
        )

    min_obs = int(len(price_df) * 0.5)
    valid_cols = price_df.columns[price_df.notna().sum() >= min_obs]
    price_df = price_df[valid_cols]
    price_df = price_df.ffill()

    if price_df.empty:
        raise BacktestEngineError(
            "All requested tickers had insufficient trading history in the lookback window."
        )

    if USE_CACHE:
        _save_to_cache(price_df, tickers, start, end)

    return price_df


def resample_weekly(daily_prices):
    """Resample to weekly, anchored on Friday, forward-filled for holidays."""
    return daily_prices.resample("W-FRI").last().ffill()


# ---------------------------------------------------------------------------
# Backtest simulation
# ---------------------------------------------------------------------------

def select_basket(candidates_pool, entry_prices, exit_prices, n_requested, rng):
    """Randomly draw up to n_requested tickers with valid entry AND exit prices."""
    eligible = [
        t for t in candidates_pool
        if pd.notna(entry_prices.get(t)) and entry_prices.get(t) > 0
        and pd.notna(exit_prices.get(t)) and exit_prices.get(t) > 0
    ]

    if len(eligible) < n_requested:
        warnings.warn(
            f"Only {len(eligible)} eligible tickers available (requested "
            f"{n_requested}); proceeding with a smaller basket."
        )

    n_pick = min(n_requested, len(eligible))
    if n_pick == 0:
        return []

    return list(rng.choice(eligible, size=n_pick, replace=False))


def run_backtest(weekly_prices, universe, initial_capital, min_invest_capital,
                  n_stocks, holding_weeks, rng):
    """
    Core simulation loop -- see microcap_backtest.py for full docstring.
    Applies a capital floor: portfolio value is topped back up to
    min_invest_capital before investing whenever it has dropped below that,
    and the full portfolio value is invested (uncapped) otherwise.

    Returns (trade_ledger_df, rebalance_summary_df, total_capital_contributed).
    """
    dates = weekly_prices.index
    trade_rows = []
    rebalance_rows = []

    current_cash = initial_capital
    total_contributed = initial_capital
    period_idx = 0

    for start_i in range(0, len(dates) - holding_weeks, holding_weeks):
        end_i = start_i + holding_weeks
        start_date = dates[start_i]
        end_date = dates[end_i]

        entry_prices = weekly_prices.loc[start_date]
        exit_prices = weekly_prices.loc[end_date]

        capital_injected = 0.0
        if current_cash < min_invest_capital:
            capital_injected = min_invest_capital - current_cash
            current_cash += capital_injected
            total_contributed += capital_injected

        basket = select_basket(universe, entry_prices, exit_prices, n_stocks, rng)

        if not basket:
            rebalance_rows.append({
                "Period": period_idx,
                "Start Date": str(start_date.date()),
                "End Date": str(end_date.date()),
                "Starting Value": current_cash,
                "Capital Injected ($)": capital_injected,
                "Ending Value": current_cash,
                "Net PnL ($)": 0.0,
                "Return (%)": 0.0,
            })
            period_idx += 1
            continue

        starting_value = current_cash
        capital_per_stock = current_cash / len(basket)
        ending_value = 0.0

        for ticker in basket:
            entry_price = entry_prices[ticker]
            exit_price = exit_prices[ticker]
            shares = capital_per_stock / entry_price
            position_end_value = shares * exit_price
            net_pnl = position_end_value - capital_per_stock
            ret_pct = (exit_price / entry_price - 1.0) * 100.0

            ending_value += position_end_value

            trade_rows.append({
                "Period": period_idx,
                "Period Start": str(start_date.date()),
                "Period End": str(end_date.date()),
                "Ticker": ticker,
                "Entry Price": entry_price,
                "Exit Price": exit_price,
                "Invested Capital ($)": capital_per_stock,
                "Net PnL ($)": net_pnl,
                "Return (%)": ret_pct,
            })

        current_cash = ending_value
        period_pnl = ending_value - starting_value
        period_ret = (ending_value / starting_value - 1.0) * 100.0 if starting_value > 0 else 0.0

        rebalance_rows.append({
            "Period": period_idx,
            "Start Date": str(start_date.date()),
            "End Date": str(end_date.date()),
            "Starting Value": starting_value,
            "Capital Injected ($)": capital_injected,
            "Ending Value": ending_value,
            "Net PnL ($)": period_pnl,
            "Return (%)": period_ret,
        })

        period_idx += 1

    trade_ledger = pd.DataFrame(trade_rows)
    rebalance_summary = pd.DataFrame(rebalance_rows)
    return trade_ledger, rebalance_summary, total_contributed


def compute_max_drawdown(equity_curve):
    """Max drawdown (%) of an equity curve (array-like), returned as a negative number."""
    equity = np.asarray(equity_curve, dtype=float)
    running_max = np.maximum.accumulate(equity)
    drawdowns = (equity - running_max) / running_max
    return float(drawdowns.min() * 100.0)


def build_global_metrics(trade_ledger, rebalance_summary, initial_capital, total_contributed):
    """Level 3 summary dict. Returns None-safe values even on empty inputs."""
    if rebalance_summary.empty:
        return {
            "Total Initial Capital": initial_capital,
            "Final Portfolio Value": initial_capital,
            "Overall Net PnL": 0.0,
            "Total Strategy Return (%)": 0.0,
            "Win Rate (%)": None,
            "Max Drawdown (%)": 0.0,
            "Additional Capital Injected": 0.0,
            "Total Capital Contributed": initial_capital,
        }

    final_value = float(rebalance_summary["Ending Value"].iloc[-1])
    total_injected = total_contributed - initial_capital

    total_pnl = final_value - total_contributed
    total_return_pct = (final_value / total_contributed - 1.0) * 100.0 if total_contributed > 0 else None

    win_rate = float((trade_ledger["Net PnL ($)"] > 0).mean() * 100.0) if not trade_ledger.empty else None

    equity_curve = [initial_capital] + rebalance_summary["Ending Value"].tolist()
    max_dd = compute_max_drawdown(equity_curve)

    return {
        "Total Initial Capital": initial_capital,
        "Final Portfolio Value": final_value,
        "Overall Net PnL": total_pnl,
        "Total Strategy Return (%)": total_return_pct,
        "Win Rate (%)": win_rate,
        "Max Drawdown (%)": max_dd,
        "Additional Capital Injected": total_injected,
        "Total Capital Contributed": total_contributed,
    }


def _sanitize_records(df):
    """
    Convert a DataFrame to a JSON-safe list of dicts: NaN/NaT/Inf -> None.
    FastAPI's jsonable_encoder chokes on raw NaN (invalid JSON), so this
    must happen before the response model is built, not after.
    """
    if df.empty:
        return []
    clean = df.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notna(df), None)
    return clean.to_dict(orient="records")


def _sanitize_metrics(metrics: dict):
    """Same NaN/Inf -> None handling, but for a flat dict rather than a DataFrame."""
    clean = {}
    for k, v in metrics.items():
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            clean[k] = None
        else:
            clean[k] = v
    return clean


# ---------------------------------------------------------------------------
# Backtest run history (for the "average of last N runs" feature)
# ---------------------------------------------------------------------------

def _load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt/unreadable history file shouldn't take down the whole API --
        # treat it as empty and let future runs rebuild it.
        return []


def _save_history(history: list) -> None:
    os.makedirs(PROJECT_ROOT, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def _append_history(global_metrics: dict, initial_capital: float, num_stocks: int, holding_period_weeks: int) -> None:
    """Record one run's headline metrics, trimmed to the MAX_HISTORY most recent."""
    history = _load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "initial_capital": initial_capital,
        "num_stocks": num_stocks,
        "holding_period_weeks": holding_period_weeks,
        "net_pnl": global_metrics.get("Overall Net PnL"),
        "total_return_pct": global_metrics.get("Total Strategy Return (%)"),
        "win_rate_pct": global_metrics.get("Win Rate (%)"),
    })
    history = history[-MAX_HISTORY:]
    _save_history(history)


def _mean_ignoring_none(values: list):
    clean = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not clean:
        return None
    return float(np.mean(clean))


def compute_average_stats(num_runs: int) -> dict:
    """
    Average net PnL, total return %, and win rate % over the `num_runs` most
    recent recorded backtest runs. Raises BacktestEngineError if fewer than
    `num_runs` runs have ever been recorded.
    """
    history = _load_history()

    if len(history) < num_runs:
        raise BacktestEngineError(
            f"Not enough backtest runs: requested an average of the last {num_runs}, "
            f"but only {len(history)} run(s) have been recorded so far. Run more "
            f"backtests first, or request a smaller number."
        )

    recent = history[-num_runs:]

    return {
        "num_runs_requested": num_runs,
        "num_runs_used": len(recent),
        "avg_net_pnl": _mean_ignoring_none([r["net_pnl"] for r in recent]),
        "avg_total_return_pct": _mean_ignoring_none([r["total_return_pct"] for r in recent]),
        "avg_win_rate_pct": _mean_ignoring_none([r["win_rate_pct"] for r in recent]),
        "oldest_run_timestamp": recent[0]["timestamp"],
        "newest_run_timestamp": recent[-1]["timestamp"],
    }


def get_history_count() -> int:
    return len(_load_history())


# ---------------------------------------------------------------------------
# Public entry point used by the API layer
# ---------------------------------------------------------------------------

def run_backtest_pipeline(initial_capital: float, num_stocks: int, holding_period_weeks: int) -> dict:
    """
    Runs one full backtest end-to-end and returns a plain, JSON-safe dict
    with keys 'global_metrics', 'rebalance_summary', 'trade_ledger' -- ready
    to hand straight to a Pydantic response model.

    Raises BacktestEngineError on data problems (empty download, no eligible
    tickers, etc.) so the route layer can turn that into a clean HTTP error.
    """
    end_date = datetime.combine(datetime.today().date(), datetime.min.time())
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)

    daily_prices = fetch_price_data(MICROCAP_UNIVERSE, start_date, end_date)
    weekly_prices = resample_weekly(daily_prices)

    if len(weekly_prices.index) <= holding_period_weeks:
        raise BacktestEngineError(
            "Not enough weekly data points for the requested holding period "
            f"({holding_period_weeks} weeks) -- try a shorter holding period."
        )

    universe = list(weekly_prices.columns)
    rng = np.random.default_rng(None)  # fully random basket each request

    trade_ledger, rebalance_summary, total_contributed = run_backtest(
        weekly_prices=weekly_prices,
        universe=universe,
        initial_capital=initial_capital,
        min_invest_capital=initial_capital,
        n_stocks=num_stocks,
        holding_weeks=holding_period_weeks,
        rng=rng,
    )

    global_metrics = build_global_metrics(
        trade_ledger, rebalance_summary, initial_capital, total_contributed
    )

    _append_history(global_metrics, initial_capital, num_stocks, holding_period_weeks)

    return {
        "global_metrics": _sanitize_metrics(global_metrics),
        "rebalance_summary": _sanitize_records(rebalance_summary),
        "trade_ledger": _sanitize_records(trade_ledger),
    }
