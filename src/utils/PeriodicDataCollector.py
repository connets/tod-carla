import csv


class PeriodicDataCollector:
    def __init__(self, file_path, items: dict):
        self._writer = csv.writer(open(file_path, 'w', newline=''))
        self._items = items
        self._timestamp_func = None
        self._interval = None
        self._last_timestamp = None
        self._writer.writerow(self._items.keys())

    def add_interval_logging(self, timestamp_func, interval):
        self._timestamp_func = timestamp_func
        self._interval = interval
        self._last_timestamp = timestamp_func() - interval

    def tick(self):
        current_timestamp = None if self._timestamp_func() is None else self._timestamp_func()
        if current_timestamp is None or current_timestamp >= self._last_timestamp + self._interval:
            self._writer.writerow(func() for func in self._items.values())
            self._last_timestamp = current_timestamp
