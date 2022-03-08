from multiprocessing import Event
from typing import List

from my_singleton import Singleton
from queue import PriorityQueue

from tele_event import TeleEvent
from tele_world import TeleWorld


@Singleton
class TeleContext:
    def __init__(self, time_step: int):
        self._last_event = None
        self._current_time_step = 0
        self._time_step = time_step
        self._worlds = []

    def add_world(self, world: TeleWorld):
        world.init(self._time_step)
        self._worlds.append(world)

    def start(self):
        for world in self._worlds:
            world.proceed(self._current_time_step)
        self._current_time_step += self._time_step

    @property
    def simulation_time(self):
        return self._last_event.time
