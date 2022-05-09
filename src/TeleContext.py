from queue import PriorityQueue

from src.TeleLogger import TeleLogger
from src.utils.decorators import Singleton


class TeleContext:
    def __init__(self, initial_timestamp):
        self._queue = PriorityQueue()
        self._timestamp = initial_timestamp

    @property
    def timestamp(self):
        return self._timestamp

    def next_timestamp_event(self):
        return self._queue.queue[0].timestamp if not self._queue.empty() else None

    def run_next_event(self):
        timing_event = self._queue.get()
        TeleLogger.event_logger.write(timing_event.timestamp, timing_event.event)
        self._timestamp = timing_event.timestamp
        timing_event.event()

    def schedule(self, event, s):
        print(event.__name__, self._timestamp, self._timestamp + s)
        # print("-"*5, self._timestamp_func(), ms, self._timestamp_func() + ms)
        self._queue.put(self.TimingEvent(event, self._timestamp + s))

    class TimingEvent:
        def __init__(self, event, timestamp):
            self.event = event
            self.timestamp = timestamp

        def __lt__(self, e):
            return self.timestamp < e.timestamp

        @property
        def timestamp_scheduled(self):
            return self.timestamp
