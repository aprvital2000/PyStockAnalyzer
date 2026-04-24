# PyStockAnalyzer

A Python-based stock technical analysis tool that fetches daily market data, computes 10 technical indicators, visualises them in an interactive Dash dashboard, and sends a daily BUY/SELL alert at 6 PM via macOS notification.

---

## Features

- **10 technical indicators** — MACD, ROC, Aroon, RSI, ADX, Bollinger Bands, CCI, Williams %R, Stochastic, VWAP, OBV, SuperTrend
- **Buy / Sell signals** — generated per indicator and combined into a daily recommendation
- **Interactive dashboard** — dark-themed Dash app with candlestick chart, colour-coded signal zones, sticky price panel, and cross-chart hover crosshair
- **Daily notification** — macOS alert popup at 6 PM via launchd scheduler
- **CSV caching** — raw and enriched data cached daily under `data/` to avoid redundant API calls

---

## Project Structure

```
PyStockAnalyzer/
├── analyse.py          # Core analysis engine
├── analyse_batch.py    # Batch runner — analyses all symbols in securities.json
├── dash_app.py         # Interactive Dash/Plotly dashboard
├── notify.py           # Daily notifier — runs analysis and fires macOS alert
├── securities.json     # Watchlist of ticker symbols and company names
├── assets/
│   └── styles.css      # Dark-theme CSS overrides for the Dash dropdown
├── data/               # Auto-generated CSV cache (raw + enriched per symbol)
└── logs/
    ├── notify.log      # stdout from scheduled notify.py runs
    └── notify.err      # stderr from scheduled notify.py runs
```

---

## Prerequisites

- Python 3.13+
- macOS (for the notification scheduler)
- [Homebrew](https://brew.sh) (for `terminal-notifier`, optional)

---

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install pandas pandas-ta yfinance plotly dash
```

### 3. Configure your watchlist

Edit `securities.json` to add or remove symbols:

```json
[
  { "ticker": "AAPL", "name": "Apple Inc." },
  { "ticker": "NVDA", "name": "NVIDIA Corporation" }
]
```

---

## Usage

### Run a batch analysis

Analyses all symbols in `securities.json`, prints BUY/SELL signals to the console, and writes enriched CSVs to `data/`.

```bash
python analyse_batch.py
```

**Output example:**
```
[BUY ] --> DOCU (DocuSign, Inc.)
[BUY ] --> NET (Cloudflare, Inc.)
[SELL] --> BAC (Bank Of America Corporation)
[SELL] --> WFC (Wells Fargo & Company)
```

### Analyse a single symbol

```python
from analyse import analyze_symbol
df = analyze_symbol("AAPL", "Apple Inc.")
```

Returns a pandas DataFrame with all indicator columns and recommendation columns (`macd_reco`, `rsi_reco`, `bb_reco`, etc.).

### Launch the dashboard

```bash
python dash_app.py
```

Open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser.

### Send a manual notification

```bash
python notify.py
```

Runs the full analysis and shows a macOS popup alert with today's signals.

---

## Dashboard

The Dash app displays 10 stacked panels for the selected symbol:

| Panel | Indicator | Signal Logic |
|---|---|---|
| 1 | **Price** | Candlestick + MACD-based buy (🟢) / sell (🔴) markers |
| 2 | **MACD** | Histogram (green/red) + MACD & Signal lines |
| 3 | **Rate of Change** | Buy when ROC crosses above 0, Sell below |
| 4 | **Aroon Oscillator** | Buy when ≥ 0, Sell when < 0 |
| 5 | **RSI** | Overbought ≥ 70 (red zone), Oversold ≤ 30 (green zone) |
| 6 | **ADX** | Trend strength ≥ 25 with +DMI / −DMI direction lines |
| 7 | **Bollinger Bands** | Buy at lower band, Sell at upper band |
| 8 | **CCI** | Overbought ≥ 100, Oversold ≤ −100 |
| 9 | **Williams %R** | Overbought ≥ −20, Oversold ≤ −80 |
| 10 | **Stochastic** | %K overbought ≥ 80, oversold ≤ 20 |

**Interactions:**
- Hover on any panel → crosshair syncs across all 10 panels
- Pan / zoom → both price and indicator charts stay in sync
- Price chart stays pinned to the top while scrolling through indicators
- Scroll zoom is disabled to avoid accidental zooming

---

## Technical Indicators

| Indicator | Buy Signal | Sell Signal |
|---|---|---|
| **MACD** | Histogram crosses above 0 while MACD < 0 | Histogram crosses below 0 while MACD > 0 |
| **ROC** | Crosses above 0 | Crosses below 0 |
| **Aroon** | Oscillator ≥ 0 | Oscillator < 0 |
| **RSI** | ≥ 70 (momentum) | ≤ 30 (oversold) |
| **ADX** | ADX > 25 and +DMI > −DMI | ADX > 25 and −DMI > +DMI |
| **Bollinger Bands** | Close ≤ Lower Band | Close ≥ Upper Band |
| **CCI** | ≤ −100 | ≥ 100 |
| **Williams %R** | ≤ −80 | ≥ −20 |
| **Stochastic** | %K ≤ 20 and %K ≥ %D | %K ≥ 80 and %K ≤ %D |
| **VWAP** | Close ≥ VWAP | Close < VWAP |

---

## Daily Scheduler

A macOS launchd agent runs `notify.py` every day at **6:00 PM** local time.

**Agent plist:** `~/Library/LaunchAgents/com.pystock.daily.plist`

```bash
# Check it is loaded
launchctl list | grep pystock

# Unload (disable)
launchctl unload ~/Library/LaunchAgents/com.pystock.daily.plist

# Reload (re-enable)
launchctl load ~/Library/LaunchAgents/com.pystock.daily.plist
```

**Notification format:**
```
Stocks Apr 24, 2026: 2 BUY / 7 SELL
🟢 BUY: DOCU, NET
🔴 SELL: BAC, DE, ETH-USD, NIO, SMFG, SPCE, WFC
```

---

## Data & Caching

- Raw OHLCV data is fetched from Yahoo Finance via `yfinance` and cached as `data/{TICKER}-{DDMMYY}.csv`
- Enriched data (with all indicator columns) is saved as `data/{TICKER}-enriched-{DDMMYY}.csv`
- Files older than 1 day are automatically purged on each run

---

## Configuration

Key settings at the top of `analyse.py`:

| Variable | Default | Description |
|---|---|---|
| `print_reco` | `True` | Print BUY/SELL signals to console |
| `print_result` | `False` | Print full indicator table to console |
| `write_to_file` | `True` | Save enriched CSV to `data/` |
| `print_debug` | `False` | Enable verbose debug logging |
| `purge_files_after_days` | `1` | Days before cached CSVs are deleted |
| `decision_truncate_days` | `5` | Look-back window for BUY/SELL decision |
