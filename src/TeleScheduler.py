from queue import PriorityQueue

from src.TeleLogger import TeleLogger
from src.utils.MySingleton import Singleton


@Singleton
class TeleScheduler:
    def __init__(self, timestmap_func):
        self._queue = PriorityQueue()
        self._timestamp_func = timestmap_func

    def schedule(self, event, ms):
        # print("-"*5, self._timestamp_func(), ms, self._timestamp_func() + ms)
        self._queue.put(self.TimingEvent(event, self._timestamp_func() + ms))

    def tick(self):
        while not self._queue.empty() and self._queue.queue[0].timestamp_scheduled <= self._timestamp_func():
            timing_event = self._queue.get()
            TeleLogger.event_logger.write(timing_event.timestamp, self._timestamp_func(),
                                            timing_event)
            timing_event.event()

    class TimingEvent:
        def __init__(self, event, timestamp):
            self.event = event
            self.timestamp = timestamp

        def __lt__(self, e):
            return self.timestamp < e.timestamp

        @property
        def timestamp_scheduled(self):
            return self.timestamp
