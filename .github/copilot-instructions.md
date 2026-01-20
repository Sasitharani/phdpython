# Copilot Instructions for phdpython

## Architecture Overview
This is a Python-based financial data pipeline for PhD research on Indian stock markets (NSE). It collects real-time tick data via Dhan API WebSocket, aggregates into OHLC candles, and enables analysis through Jupyter notebooks.

**Key Components:**
- `api/dhan_ws_client.py`: WebSocket client for live ticker subscription
- `aggregation/candle_builder.py`: CandleAggregator class for building candles from ticks
- `config /settings.yaml`: Configuration for symbols, timeframe, data paths
- `analysis/notebooks/`: Jupyter notebooks for data analysis and modeling

**Data Flow:**
1. WebSocket receives binary tick packets → parse LTP/LTT
2. Aggregator builds candles per timeframe (e.g., "1min", "5m")
3. Completed candles printed/logged (extend to save to `data/raw/` CSVs)

## Key Patterns
- **Time Handling:** Use pandas with UTC → Asia/Kolkata timezone conversion. Floor timestamps to bucket (e.g., `ts.floor("5m")`)
- **Binary Parsing:** Use `struct.unpack` for Dhan's binary protocol (little-endian: `<f` for float, `<i` for int)
- **Configuration:** Load YAML from `config /settings.yaml` for symbols list, timeframe, lookback days
- **Environment Variables:** `DHAN_ACCESS_TOKEN`, `DHAN_CLIENT_ID` for API auth
- **Reconnection:** Exponential backoff (1s to 60s) for WebSocket failures

**Example Candle Building:**
```python
aggregator = CandleAggregator("5m")
aggregator.add_tick(price, epoch_timestamp)
for candle in aggregator.get_completed_candles():
    # candle: {"timestamp": pd.Timestamp, "open": float, "high": float, "low": float, "close": float}
```

## Developer Workflows
- **Run Live Feed:** `python api/dhan_ws_client.py` (requires env vars set)
- **Data Collection:** Extend `Collector/monthly_fetch.py` for historical data via Dhan REST API
- **Analysis:** Use notebooks in `analysis/`; import aggregated data from `data/raw/*.csv`
- **Dependencies:** Install `websocket-client`, `pandas` (no requirements.txt yet)

## Conventions
- **Imports:** Relative imports for modules (e.g., `from aggregation.candle_builder import CandleAggregator`)
- **Error Handling:** Print emojis for logs (✅ ❌ 🔄); raise RuntimeError for missing env vars
- **Data Storage:** Raw CSVs in `data/raw/`; use pandas for reading/writing
- **Security:** Never commit API tokens; use env vars

Focus on extending data persistence, adding historical fetch, and building analysis models in notebooks.