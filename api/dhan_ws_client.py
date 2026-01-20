import websocket
import struct
import json
import time
import os
from threading import Lock

from aggregation.candle_builder import CandleAggregator

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

DHAN_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")

if not DHAN_TOKEN or not CLIENT_ID:
    raise RuntimeError("❌ Set DHAN_ACCESS_TOKEN and DHAN_CLIENT_ID")

# Global list to store live candles for web app
LIVE_CANDLES = []
DATA_LOCK = Lock()

WS_URL = (
    f"wss://api-feed.dhan.co?"
    f"version=2&token={DHAN_TOKEN}&clientId={CLIENT_ID}&authType=2"
)

SUBSCRIBE_PAYLOAD = {
    "RequestCode": 15,
    "InstrumentCount": 1,
    "InstrumentList": [
        {
            "ExchangeSegment": "NSE_EQ",   # change to MCX_COMM for Gold
            "SecurityId": "1333"          # change to correct instrument ID
        }
    ]
}

# -------------------------------------------------
# GLOBAL STORAGE (used by browser / Flask)
# -------------------------------------------------

LIVE_CANDLES = []
DATA_LOCK = Lock()

# -------------------------------------------------
# AGGREGATOR
# -------------------------------------------------

aggregator = CandleAggregator("1min")

# -------------------------------------------------
# BINARY PARSING
# -------------------------------------------------

def parse_header(data):
    feed_code = data[0]
    msg_len = struct.unpack("<h", data[1:3])[0]
    exchange = data[3]
    security_id = struct.unpack("<i", data[4:8])[0]
    return feed_code, msg_len, exchange, security_id


def parse_ticker_packet(data):
    ltp = struct.unpack("<f", data[8:12])[0]
    ltt = struct.unpack("<i", data[12:16])[0]
    return ltp, ltt

# -------------------------------------------------
# WEBSOCKET CALLBACKS
# -------------------------------------------------

def on_open(ws):
    print("✅ WebSocket connected")
    ws.send(json.dumps(SUBSCRIBE_PAYLOAD))
    print("📡 Subscription sent")


def on_message(ws, message):
    if not isinstance(message, bytes) or len(message) < 16:
        return

    feed_code, _, _, _ = parse_header(message)

    # Ticker packet
    if feed_code == 2:
        ltp, ltt = parse_ticker_packet(message)
        aggregator.add_tick(ltp, ltt)

        candles = aggregator.get_completed_candles()
        if candles:
            with DATA_LOCK:
                LIVE_CANDLES.extend(candles)

            for c in candles:
                print("🕯️ CANDLE:", c)


def on_error(ws, error):
    print("❌ WebSocket error:", error)


def on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed")
    print("ℹ️ Restart manually after cooldown if required")

# -------------------------------------------------
# RUNNER
# -------------------------------------------------

def start_ws():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever(
        ping_interval=10,
        ping_timeout=5
    )

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":
    start_ws()