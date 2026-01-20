from flask import Flask, render_template, jsonify
from api.dhan_ws_client import LIVE_CANDLES
import threading
from api.dhan_ws_client import start_ws

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/candles")
def candles():
    return jsonify(LIVE_CANDLES[-50:])  # last 50 candles

def start_ws_thread():
    t = threading.Thread(target=start_ws, daemon=True)
    t.start()

# Start the WebSocket thread when the module is loaded
start_ws_thread()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)