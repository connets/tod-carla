import os
import socket
from abc import ABC, abstractmethod
from collections.abc import Callable
from queue import PriorityQueue

from src.network.NetworkMessage import NetworkMessage
from src.utils.distribution_utils import _constant_family
from threading import Thread


class NetworkInterface(ABC):
    def __init__(self, timestamp_func, distr_func, interval):
        self._timestamp_func = timestamp_func
        self._distr_func = distr_func
        self._interval = interval
        self._last_timestamp = None

    def bind(self, network_node):
        ...
        # self.tick()

    def tick(self):
        ...

    def send(self, msg, destination_node):
        ...


class PhysicNetworkInterface(NetworkInterface):
    def __init__(self, timestamp_func, distr_func, interval):
        super().__init__(timestamp_func, distr_func, interval)
        self.network_node = None
        self._socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # UDP socket

    def start(self, network_node):
        self.network_node = network_node
        self._socket.bind((network_node.host, network_node.port))  # Bind to the port

        def listen():
            while True:
                data, addr = self._socket.recvfrom(4096)
                msg = NetworkMessage.from_bytes(data)
                print('Got connection from', msg.timestamp)
                self.network_node.receive_msg(msg)

        Thread(target=listen)

    @abstractmethod
    def _apply_delay(self):
        ...

    def send(self, msg, destination_node):
        # self._socket.connect((destination_node.host, destination_node.port))
        self._socket.sendto(msg.to_bytes(), (destination_node.host, destination_node.port))
        # init_msg = NetworkMessage.from_bytes(s.recv(4096))
        # print(datetime.datetime.now().timestamp() - init_msg.timestamp)

    def tick(self):
        current_timestamp = self._timestamp_func()
        if self._last_timestamp is None or current_timestamp >= self._last_timestamp + self._interval:
            self._apply_delay()
            self._last_timestamp = current_timestamp

    @abstractmethod
    def finish(self):
        ...


class TcNetworkChannel(PhysicNetworkInterface):

    def __init__(self, distr_funct, timestamp_func, interval, user_pw):
        super().__init__(distr_funct, timestamp_func, interval)
        self._user_pw = user_pw

    def _apply_delay(self):
        self.finish()
        os.system(
            f'echo {self._user_pw} | sudo -S sudo tc qdisc add dev wlp2s0 root netem delay {self._distr_func()}ms 2> /dev/null')

    def finish(self):
        os.system(f'echo {self._user_pw} | sudo -S tc qdisc del dev wlp2s0 root 2> /dev/null')


class DiscreteNetworkInterface(NetworkInterface):
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
    network_delay = TcNetworkChannel(_constant_family(20), lambda: round(3), 0, 'valecislavale')
    network_delay.start()
    network_delay.finish()
