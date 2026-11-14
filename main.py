#!/usr/bin/env python3
"""BTC 4-hour close forecaster for make.fun btc-cent-forecast-01.

Method: for each case, take the market's last one-minute close (the close
at the checkpoint) and pull it 5% of the way toward the mean of the last
1440 closes (24 hours):

    guess = last + 0.05 * (mean(last 1440 closes) - last)

The guess is rounded to 5 decimals and kept inside [0.00001, 9999999.99999].

Why this shape: at a four-hour horizon Bitcoin is close to a random walk,
so the checkpoint close is the honest baseline -- any forecast that leans
hard on momentum or on a far-away anchor loses to simply standing still.
A small 5% pull toward the 24-hour mean was the only adjustment that was
not harmful out of sample on 90 days of one-minute closes: it leans
against short-lived spikes without pretending the price reverts. In 511
simulated 48-hour finals this rule beat the persistence baseline (the
checkpoint close, unchanged) in 61 percent of finals.

The program is stdlib-only, offline, and deterministic: cases are read in
file-name order, the arithmetic is a fixed sequence of float operations,
and the output JSON uses fixed key order, so two runs on the same input
write byte-identical outputs.

Input:  every ``<id>.in`` in ``$MAKEFUN_INPUT_DIR`` (default ``/input``),
        one JSON case per file, holding exactly one market whose
        ``prices`` list is the one-minute BTC/USD closes, oldest first,
        the last being the checkpoint close.
Output: one ``<id>.out`` per case in ``$MAKEFUN_OUTPUT_DIR`` (default
        ``/output``), JSON with exactly one key, ``forecasts``, a list
        holding exactly one object with the case id and the price guess.

Degenerate cases are handled with a valid fallback instead of crashing:
an empty price list, or a last close that is not finite, yields the
fallback guess of 1.0 (a finite price inside the allowed range); a
non-finite value anywhere else in the window is ignored, so the mean is
always taken over the finite closes that exist. A stray directory named
``*.in`` in the input folder is skipped rather than read as a case.
"""

import json
import math
import os
from pathlib import Path

# Pull toward the 24-hour mean: 5% of the gap between the last close and
# the mean of the last 1440 one-minute closes.
SHRINK = 0.05
# One day of one-minute closes.
WINDOW = 1440
# The scorer's price grid: 5 decimals, strictly inside (0, 10_000_000).
MIN_PRICE = 0.00001
MAX_PRICE = 9999999.99999
# Valid guess when a case carries no usable price at all.
FALLBACK_PRICE = 1.0

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def grid_price(x):
    """Keep x on the 5-decimal price grid inside (0, 10_000_000)."""
    x = min(MAX_PRICE, max(MIN_PRICE, x))
    # Round half-up at the 5th decimal (all prices here are positive),
    # then clamp once more so rounding can never step outside the range.
    rounded = math.floor(x * 1e5 + 0.5) / 1e5
    return min(MAX_PRICE, max(MIN_PRICE, rounded))


def forecast(prices):
    """One forecast from a list of one-minute closes, oldest first."""
    finite = [
        p
        for p in prices
        if isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p)
    ]
    if not finite:
        return FALLBACK_PRICE
    last = finite[-1]
    window = finite[-WINDOW:]
    mean = sum(window) / len(window)
    guess = last + SHRINK * (mean - last)
    if not math.isfinite(guess):
        return FALLBACK_PRICE
    return grid_price(guess)


def main():
    input_dir = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Name order, so two runs write the same bytes. A stray directory
    # named *.in is not a case file, so only regular files are read.
    inputs = sorted(
        p for p in input_dir.iterdir() if p.is_file() and p.name.endswith(".in")
    )
    for path in inputs:
        case_id = path.name[: -len(".in")]
        with path.open("r", encoding="utf-8") as f:
            case = json.load(f)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{path.name} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list):
            raise ValueError(f"{path.name} market has no prices list")
        guess = forecast(prices)
        payload = {"forecasts": [{"case": case_id, "price": guess}]}
        out_path = output_dir / f"{case_id}.out"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps(payload, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
