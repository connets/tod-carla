import os
from abc import ABC, abstractmethod

from src.utils.distribution_utils import _constant_family


class PhysycNetworkDelayManager(ABC):
    def __init__(self, distr_funct, timestamp_func, interval):
        self._distr_funct = distr_funct
        self._timestamp_func = timestamp_func
        self._last_timestamp = None
        self._interval = interval

    @abstractmethod
    def _apply_delay(self):
        ...

    def start(self):
        self.tick()

    def tick(self):
        current_timestamp = self._timestamp_func()
        if self._last_timestamp is None or current_timestamp >= self._last_timestamp + self._interval:
            self._apply_delay()
            self._last_timestamp = current_timestamp

    @abstractmethod
    def finish(self):
        ...

class TcNetworkDelayManager(PhysycNetworkDelayManager):

    def __init__(self, distr_funct, timestamp_func, interval, user_pw):
        super().__init__(distr_funct, timestamp_func, interval)
        self._user_pw = user_pw

    def _apply_delay(self):
        self.finish()
        os.system(f'echo {self._user_pw} | sudo -S sudo tc qdisc add dev wlp2s0 root netem delay {self._distr_funct()}ms 2> /dev/null')

    def finish(self):
        os.system(f'echo {self._user_pw} | sudo -S tc qdisc del dev wlp2s0 root 2> /dev/null')


if __name__ == '__main__':
    network_delay = TcNetworkDelayManager(_constant_family(20), lambda: round(3), 0, 'valecislavale')
    network_delay.start()
    network_delay.finish()
