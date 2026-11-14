#!/usr/bin/env python3
"""BTC cent forecaster for make.fun btc-cent-forecast-01.

Idea: Bitcoin's one-minute closes drift, but over a few hours they tend to
wander back toward where they have been trading over the past day. So this
program takes the most recent close and nudges it a small, fixed fraction
of the way toward the average close of the last 24 hours (the last 1,440
one-minute bars). The nudge is deliberately small -- five percent of the
gap -- so the forecast stays close to the latest price while still leaning
in the direction the day's trading suggests.

Usage: python3 main.py
Reads *.in files from $MAKEFUN_INPUT_DIR (default /input) and writes one
*.out JSON file per case into $MAKEFUN_OUTPUT_DIR (default /output).

Standard library only. No network, no clock, no randomness: the same input
always produces byte-identical output.
"""

import json
import math
import os
from pathlib import Path

# How far the last close is pulled toward the 24-hour mean.
SHRINK = 0.05

# One-minute bars covering a full day.
WINDOW = 1440

# Forecasts must stay strictly inside this band.
LOW = 0.00001
HIGH = 9999999.99999

# Fallback forecast when a case carries no usable price at all.
FALLBACK = 1.0


def usable_prices(raw):
    """Keep only real, finite numbers from a raw price list."""
    good = []
    for value in raw or []:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and math.isfinite(value):
            good.append(float(value))
    return good


def forecast(prices):
    """Shrink the last close 5% toward the mean of the last 24 hours."""
    clean = usable_prices(prices)
    if not clean:
        return FALLBACK
    last = clean[-1]
    recent = clean[-WINDOW:]
    mean = sum(recent) / len(recent)
    guess = last + SHRINK * (mean - last)
    guess = round(guess, 5)
    if guess <= LOW:
        guess = LOW + 0.00001
    if guess >= HIGH:
        guess = HIGH - 0.00001
    # Clamping can reintroduce extra decimals; round once more so the
    # written value is always exactly five decimals and inside the band.
    return round(guess, 5)


def read_case(path):
    """Return the price list of the (single) market in a case file."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    markets = payload.get("markets") or []
    if not isinstance(markets, list) or not markets:
        return []
    first = markets[0]
    if not isinstance(first, dict):
        return []
    return first.get("prices") or []


def main():
    in_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR") or "/input")
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    for in_path in sorted(in_dir.glob("*.in")):
        case_id = in_path.stem
        try:
            prices = read_case(in_path)
        except Exception:
            prices = []
        price = forecast(prices)
        document = {"forecasts": [{"case_id": case_id, "price": price}]}
        text = json.dumps(document, sort_keys=True) + "\n"
        with open(out_dir / (case_id + ".out"), "w", encoding="utf-8") as handle:
            handle.write(text)


if __name__ == "__main__":
    main()
