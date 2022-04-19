import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from queue import PriorityQueue

from src.utils.distribution_utils import _constant_family


class NetworkDelayManager(ABC):
    def __init__(self, timestamp_func, distr_func, interval):
        self._timestamp_func = timestamp_func
        self._distr_func = distr_func
        self._interval = interval
        self._last_timestamp = None

    def start(self):
        self.tick()

    def tick(self):
        ...

    def schedule(self, event):  # seconds
        ...


class PhysicNetworkDelayManager(NetworkDelayManager):
    def __init__(self, timestamp_func, distr_func, interval):
        super().__init__(timestamp_func, distr_func, interval)

    @abstractmethod
    def _apply_delay(self):
        ...

    def tick(self):
        current_timestamp = self._timestamp_func()
        if self._last_timestamp is None or current_timestamp >= self._last_timestamp + self._interval:
            self._apply_delay()
            self._last_timestamp = current_timestamp

    @abstractmethod
    def finish(self):
        ...


class TcNetworkDelayManager(PhysicNetworkDelayManager):

    def __init__(self, distr_funct, timestamp_func, interval, user_pw):
        super().__init__(distr_funct, timestamp_func, interval)
        self._user_pw = user_pw

    def _apply_delay(self):
        self.finish()
        os.system(
            f'echo {self._user_pw} | sudo -S sudo tc qdisc add dev wlp2s0 root netem delay {self._distr_func()}ms 2> /dev/null')

    def finish(self):
        os.system(f'echo {self._user_pw} | sudo -S tc qdisc del dev wlp2s0 root 2> /dev/null')




class DiscreteNetworkDelayManager(NetworkDelayManager):
    def __init__(self, timestamp_func):
        super().__init__(timestamp_func)
        self._queue = PriorityQueue()

    def schedule(self, event, delay: float):  # seconds
        self._queue.put(self.TimingEvent(event, self._timestamp_func() + delay))

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

    def tick(self):
        if not self._queue.empty() and self._queue.queue[0].timestamp_scheduled <= self._timestamp_func():
            self._queue.get().event()




if __name__ == '__main__':
    network_delay = TcNetworkDelayManager(_constant_family(20), lambda: round(3), 0, 'valecislavale')
    network_delay.start()
    network_delay.finish()