from abc import ABC
from queue import PriorityQueue

from tele_event import TeleEvent


class TeleWorld(ABC):

    def __init__(self):
        self._queue = PriorityQueue()
        self._current_time_step = None

    @staticmethod
    def proceed(self, ms: int):
        ...

    def init(self, start_time_step):
        self._current_time_step = start_time_step

    def schedule_event(self, e: TeleEvent):
        self._queue.put(e)

    def has_events(self) -> bool:
        return not self._queue.empty()
