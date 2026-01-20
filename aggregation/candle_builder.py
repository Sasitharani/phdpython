import pandas as pd

class CandleAggregator:
    def __init__(self, timeframe="1min"):
        self.timeframe = timeframe
        self.current_bucket = None
        self.candle = None
        self.completed_candles = []

    def _bucket_time(self, epoch):
        ts = pd.to_datetime(epoch, unit="s", utc=True).tz_convert("Asia/Kolkata")
        return ts.floor(self.timeframe)

    def add_tick(self, price, epoch):
        bucket = self._bucket_time(epoch)

        if self.current_bucket != bucket:
            if self.candle is not None:
                self.completed_candles.append(self.candle)

            self.current_bucket = bucket
            self.candle = {
                "timestamp": bucket,
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }
        else:
            self.candle["high"] = max(self.candle["high"], price)
            self.candle["low"] = min(self.candle["low"], price)
            self.candle["close"] = price

    def get_completed_candles(self):
        candles = self.completed_candles
        self.completed_candles = []
        return candles