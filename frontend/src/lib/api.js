// Thin wrapper around the backtest API so App.jsx doesn't deal with raw
// fetch/CORS/network-error branching directly.

const API_BASE_URL = "http://localhost:8050";

async function postJson(path, body) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (networkErr) {
    // TypeError: Failed to fetch -- covers both "server is down" and CORS
    // preflight rejection, which the browser deliberately reports identically.
    throw new Error(
      "Could not reach the backtest API. Is the backend running at " +
      `${API_BASE_URL}, and does its CORS config allow this origin?`
    );
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const errBody = await response.json();
      if (errBody?.detail) {
        detail = typeof errBody.detail === "string" ? errBody.detail : JSON.stringify(errBody.detail);
      }
    } catch {
      // response wasn't JSON -- fall back to the generic status message
    }
    throw new Error(detail);
  }

  return response.json();
}

export function runBacktest({ initialCapital, numStocks, holdingPeriodWeeks }) {
  return postJson("/api/v1/backtest", {
    initial_capital: initialCapital,
    num_stocks: numStocks,
    holding_period_weeks: holdingPeriodWeeks,
  });
}

/** Average Net PnL / Total Return % / Win Rate % over the last `numRuns` recorded backtests. */
export function getAverageStats(numRuns) {
  return postJson("/api/v1/backtest/average", { num_runs: numRuns });
}
