import sched
import time
from abc import ABC, abstractmethod

from src.TeleEvent import TeleEvent


class TeleEventsScheduler(ABC):
    def schedule(self, event: TeleEvent, ms):
        self._schedule(event, ms)

    @abstractmethod
    def _schedule(self, event: TeleEvent, ns: int):
        pass


class TeleEventsSchedulerTime(TeleEventsScheduler):
    def __init__(self, timefunc=time.time, blocking=False):
        self._sched_model = sched.scheduler(timefunc)
        self._blocking = blocking

    def _schedule(self, event: TeleEvent, ms: int):
        self._sched_model.enter(ms / 100, 1, event)
        self._sched_model.run(blocking=self._blocking)
