from abc import ABC


class TeleEvent(ABC):

    def __init__(self, time):
        self._time = time

    @property
    def time(self) -> float:
        return self._time

    def __lt__(self, e):
        return self._time < e.time
