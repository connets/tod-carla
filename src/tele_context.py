from multiprocessing import Event
from typing import List

from my_singleton import Singleton
from queue import PriorityQueue

from tele_event import TeleEvent
from tele_world import TeleWorld


class TeleContext:
    def __init__(self, start_timestamp: int, end_timestamp: int, time_step: int):
        self._last_event = None
        self._current_timestamp = 0
        self._start_timestamp = start_timestamp
        self._end_timestamp = end_timestamp
        self._time_step = time_step
        self._worlds = []

    def add_world(self, world: TeleWorld):
        world.init(self._time_step)
        self._worlds.append(world)

    def start(self):
        for current_timestamp in range(self._start_timestamp, self._end_timestamp, self._time_step):
            self._current_timestamp = current_timestamp
            for world in self._worlds:
                world.proceed(current_timestamp)

    @property
    def current_timestamp(self):
        return self._current_timestamp

    @property
    def start_timestamp(self):
        return self._start_timestamp

    @property
    def end_timestamp(self):
        return self._end_timestamp

    @property
    def time_step(self):
        return self._time_step
