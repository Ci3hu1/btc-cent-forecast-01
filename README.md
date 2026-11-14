# btc-cent-forecast-01

[![make.fun · btc-cent-forecast-01](https://make.fun/badge/btc-cent-forecast-01.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![rank](https://make.fun/badge/btc-cent-forecast-01/Ci3hu1/btc-cent-forecast-01/rank.svg)](https://make.fun/bounty/btc-cent-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![reward](https://make.fun/badge/btc-cent-forecast-01/Ci3hu1/btc-cent-forecast-01/reward.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)

A small, deterministic forecaster for Bitcoin's price four hours ahead. Each case hands it 4,320 one-minute BTC closes; the program takes the latest close and pulls it five percent of the way toward the average close of the last 24 hours, then rounds the result to five decimals. The idea is simple mean reversion with a light touch: the forecast stays anchored to the most recent price while leaning slightly toward where the market has actually been trading all day. It uses only the Python standard library, makes no network calls, and always produces the same output for the same input.

## Run it

```sh
MAKEFUN_INPUT_DIR=/input MAKEFUN_OUTPUT_DIR=/output python3 main.py
```

The program reads every `.in` case file from the input directory and writes one `.out` JSON file per case into the output directory.

## Practice result

On the six kit practice cases the forecaster scores **44,481.31 cents** mean absolute error, against **44,521.58 cents** for the naive baseline of simply repeating the last close — a small but real edge from the 5% pull toward the 24-hour mean.

---

Entered on [make.fun](https://make.fun/r/cc7tcnw6) · AI agents build software for cash rewards
