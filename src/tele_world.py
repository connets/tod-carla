from abc import ABC
from queue import PriorityQueue


class TeleWorld:

    def __init__(self, world_name, start_timestamp):
        self._world_name = world_name
        self._queue = PriorityQueue()
        self._current_timestamp = start_timestamp

    def proceed(self, current_timestamp):
        self._current_timestamp = current_timestamp
        if not self._queue.empty() and self._queue.queue[0].timestamp_scheduled <= self._current_timestamp:
            self._queue.get().event.exec(self)

    @property
    def world_name(self):
        return self._world_name

    def schedule_event_from_now(self, e, time_from_now: int):
        self._queue.put(self.TimingEvent(e, self._current_timestamp + time_from_now))

    def has_events(self) -> bool:
        return not self._queue.empty()

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
            return self._timestamp < e.timestamp
