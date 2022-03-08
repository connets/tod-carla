from multiprocessing import Event
from my_singleton import Singleton
from queue import PriorityQueue

from tele_event import TeleEvent


@Singleton
class TeleContext:

    
    def __init__(self):
        self._queue = PriorityQueue()
        self._last_event = None

    def schedule_event(self, e: TeleEvent):
        self._queue.put(e) #TODO sovrascrivi la comparazione __le__ di event

    def has_events(self) -> bool:
        return not self._queue.empty()

    def exec_next_event(self) -> bool:
        self._last_event = self._queue.get()
        ...

    @property
    def simulation_time(self):
        return self._last_event.time