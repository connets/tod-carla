from queue import PriorityQueue

from src import TeleOutputWriter


class TeleContext:
    def __init__(self, initial_timestamp):
        self._queue = PriorityQueue()
        self._initial_timestamp = initial_timestamp
        self._timestamp = initial_timestamp

        self._finished = False

    @property
    def timestamp(self):
        return self._timestamp

    def current_duration(self):
        return self._timestamp - self._initial_timestamp


    def next_timestamp_event(self):
        return self._queue.queue[0].timestamp if not self._queue.empty() else None

    def run_next_event(self):
        timing_event = self._queue.get()
        TeleOutputWriter.event_logger.write(timing_event.timestamp, timing_event.event)
        self._timestamp = timing_event.timestamp
        timing_event.event()

    def has_scheduled_events(self):
        return not self._queue.empty()

    def schedule(self, event, s):
        # print("-"*5, self._timestamp_func(), ms, self._timestamp_func() + ms)
        if not self._finished:
            self._queue.put(self.TimingEvent(event, self._timestamp + s))

    def finish(self):
        self._finished = True

    class TimingEvent:
        def __init__(self, event, timestamp):
            self.event = event
            self.timestamp = timestamp

        def __lt__(self, e):
            return self.timestamp < e.timestamp

        @property
        def timestamp_scheduled(self):
            return self.timestamp
