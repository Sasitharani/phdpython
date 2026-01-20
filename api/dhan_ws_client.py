import websocket
import struct
import json
import time
import os

from aggregation.candle_builder import CandleAggregator

# ---------------- CONFIG ---------------- #

DHAN_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")

if not DHAN_TOKEN or not CLIENT_ID:
    raise RuntimeError("❌ DHAN_ACCESS_TOKEN or DHAN_CLIENT_ID not set")

WS_URL = (
    f"wss://api-feed.dhan.co?"
    f"version=2&token={DHAN_TOKEN}&clientId={CLIENT_ID}&authType=2"
)

SUBSCRIBE_PAYLOAD = {
    "RequestCode": 15,
    "InstrumentCount": 1,
    "InstrumentList": [
        {
            "ExchangeSegment": "NSE_EQ",   # use MCX_COMM for Gold
            "SecurityId": "1333"
        }
    ]
}

# ---------------- AGGREGATOR ---------------- #

aggregator = CandleAggregator("1min")

# ---------------- PARSING ---------------- #

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


# ---------------- WS CALLBACKS ---------------- #

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

        for candle in aggregator.get_completed_candles():
            print("🕯️ CANDLE:", candle)


def on_error(ws, error):
    print("❌ WebSocket error:", error)


def on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed")
    if close_status_code:
        print(f"Close code: {close_status_code}, message: {close_msg}")


# ---------------- RUNNER ---------------- #

def start_ws():
    reconnect_delay = 1  # Start with 1 second
    max_reconnect_delay = 60  # Max 1 minute
    while True:
        try:
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
        except Exception as e:
            print(f"❌ WebSocket exception: {e}")

        print(f"🔄 Reconnecting in {reconnect_delay} seconds...")
        time.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)  # Exponential backoff


if __name__ == "__main__":
    start_ws()