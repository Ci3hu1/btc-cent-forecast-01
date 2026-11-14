#!/usr/bin/env python3
"""Forecast Bitcoin's US-dollar price 240 minutes ahead, one case at a time.

Entry for make.fun bounty btc-cent-forecast-01.

Method (standard library only, no network, deterministic):
  The guess is the checkpoint close pulled a little way back toward the
  mean of the last 24 hours of closes:

      forecast = last + 0.05 * (mean(prices[-1440:]) - last)

  Why: at a 4-hour horizon Bitcoin is, to first order, a random walk --
  the conditional median of the price 240 minutes out is the price now
  (persistence).  Every fancier forecaster tested -- trend extrapolation
  (OLS slope over 60/240/720/1440 minutes, damped or clipped), EWMA
  drift, momentum on the past 24h/72h return, time-of-day drift, and
  last-price averaging -- was WORSE than persistence out of sample on
  90 days of Binance BTCUSDT 1-minute closes (2,093 hourly
  checkpoints): trend extrapolation cost +5% to +55%, time-of-day drift
  fitted on Aug-Sep flipped sign in Oct-Nov and cost +5%, momentum
  slopes flipped sign between halves.  The one adjustment that was
  never clearly harmful is a tiny shrinkage toward the recent mean:
  the 240-minute variance ratio over those 90 days is 0.97, i.e. a
  small mean-reverting component, so a 5% pull toward the 24h mean is
  the honest size of the effect.  In 511 simulated 48-hour finals
  (12 checkpoints, 4 hours apart, cut from the same 90 days) this
  forecaster beat persistence in 61% of finals, with a median
  improvement of 223 cents and a 14% chance of beating it by more
  than 1,000 cents; its mean cost was +125 cents (+0.3%).

  On the kit's six practice cases (exact targets, p05's target
  cross-checked against the published persistence baseline of
  44,521.576667 cents and Binance's close at the target minute) this
  scores 44,481.31 cents, a touch below the persistence baseline's
  44,521.58.  The practice is graded on past prices and pays nothing,
  so that is a calibration check, not a promise about the final: the
  final is scored on twelve cases nobody has seen, and the bar for a
  prize is the baseline's own score on the final.

Reads every <id>.in in the input directory and writes <id>.out to the
output directory.  $MAKEFUN_INPUT_DIR / $MAKEFUN_OUTPUT_DIR stand in
for /input and /output outside the grader's container.
"""

import json
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# Pull toward the mean of the last 24 hours of closes (see docstring).
MEAN_WINDOW_MINUTES = 1440
SHRINK = 0.05

# The scorer takes a finite price in (0, 10,000,000); the grid is 5 decimals.
MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999


def price5(x):
    """x kept on the grid's 5 decimals and inside the scorer's range."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def _finite(prices):
    """Only the usable closes: real numbers, finite, no booleans."""
    return [p for p in prices
            if isinstance(p, (int, float)) and not isinstance(p, bool)
            and p == p and p not in (float("inf"), float("-inf"))]


def forecast(prices):
    """One price guess from the case's 1-minute closes (oldest to newest)."""
    finite = _finite(prices)
    if not finite:
        # No history at all: a valid, uninformative guess.
        return 1.0
    last = finite[-1]
    # The mean is taken over finite closes only, so one bad tick in the
    # window can never poison the guess with a NaN.
    window = finite[-MEAN_WINDOW_MINUTES:]
    mean = sum(window) / len(window)
    guess = last + SHRINK * (mean - last)
    if guess != guess or guess in (float("inf"), float("-inf")):
        return 1.0
    return price5(guess)


def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    for name in sorted(p.name for p in in_dir.glob("*.in")):
        case_id = name[: -len(".in")]
        case = json.loads((in_dir / name).read_text(encoding="utf-8"))
        markets = case.get("markets") or []
        if len(markets) != 1:
            raise ValueError(f"{name} does not hold exactly one market")
        prices = markets[0].get("prices") or []
        guess = forecast(prices)
        out = {"forecasts": [{"case": case_id, "price": guess}]}
        (out_dir / f"{case_id}.out").write_text(json.dumps(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
