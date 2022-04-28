from queue import PriorityQueue

from src.utils.MySingleton import Singleton


@Singleton
class TeleScheduler:
    def __init__(self, timestmap_func):
        self._queue = PriorityQueue()
        self._timestamp_func = timestmap_func

    def schedule(self, event, ms):
        self._queue.put(self.TimingEvent(event, self._timestamp_func() + ms))

    def tick(self):
        if not self._queue.empty() and self._queue.queue[0].timestamp_scheduled <= self._timestamp_func():
            self._queue.get().event()

    class TimingEvent:
        def __init__(self, event, timestamp):
            self._event = event
            self._timestamp = timestamp

        @property
        def event(self):
            return self._event

        @property
        def timestamp_scheduled(self) -> int:
            return self._timestamp

        def __lt__(self, e):
            return self._timestamp < e._timestamp
