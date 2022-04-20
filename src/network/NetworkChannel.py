import os
import socket
from abc import ABC, abstractmethod
from collections.abc import Callable
from queue import PriorityQueue

from src.network.NetworkMessage import NetworkMessage
from src.utils.distribution_utils import _constant_family
from threading import Thread


class NetworkChannel(ABC):
    def __init__(self, destination_node, timestamp_func, distr_func, interval):
        self.destination_node = destination_node

        self._timestamp_func = timestamp_func
        self._distr_func = distr_func
        self._interval = interval
        self._last_tick_timestamp = None

    def tick(self):
        current_timestamp = self._timestamp_func()
        if self._last_tick_timestamp is None or current_timestamp >= self._last_tick_timestamp + self._interval:
            self._apply_delay()
            self._last_tick_timestamp = current_timestamp

    @abstractmethod
    def _apply_delay(self):
        pass

    @abstractmethod
    def bind(self, source_node):
        ...

    @abstractmethod
    def send(self, msg):
        ...

    @abstractmethod
    def quit(self):
        ...


class PhysicNetworkChannel(NetworkChannel):
    def __init__(self, destination_node, timestamp_func, distr_func, interval):
        super().__init__(destination_node, timestamp_func, distr_func, interval)
        # self.network_node = None
        # self._socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # UDP socket
        self._out_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self._input_daemon = None

    def bind(self, source_node):
        # self.network_node = network_node

        class InputDaemon(Thread):

            def __init__(self):
                super().__init__()
                self._socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                self._socket.bind((source_node.host, source_node.port))  # Bind to the port
                self._running = True

            def stop(self):
                self._running = False

            def run(self) -> None:
                self._socket.settimeout(5)
                while self._running:
                    try:
                        data, addr = self._socket.recvfrom(4096)
                        msg = NetworkMessage.from_bytes(data)
                        print('Got connection', source_node.host, source_node.port)
                        source_node.receive_msg(msg)
                    except socket.timeout:
                        ...

        self._input_daemon = InputDaemon()
        self._input_daemon.start()

    @abstractmethod
    def _apply_delay(self):
        ...

    def send(self, msg):
        # self._socket.connect((destination_node.host, destination_node.port))
        self._out_socket.sendto(msg.to_bytes(), (self.destination_node.host, self.destination_node.port))
        # init_msg = NetworkMessage.from_bytes(s.recv(4096))
        # print(datetime.datetime.now().timestamp() - init_msg.timestamp)

    def quit(self):
        if self._input_daemon is not None:
            self._input_daemon.stop()

    @abstractmethod
    def _remove_delay(self):
        ...


class TcNetworkInterface(PhysicNetworkChannel):

    def __init__(self, destination_node, timestamp_func, distr_func, interval, network_interface):
        super().__init__(destination_node, timestamp_func, distr_func, interval)
        self._network_interface = network_interface

    def _apply_delay(self):
        tc_config = f"""tcset {self._network_interface} --delay {self._distr_func()}ms --network {self.destination_node.host} --port {self.destination_node.port} --change 2> /dev/null"""  # TODO change stderr
        print(tc_config)
        os.system(tc_config)

    def _remove_delay(self):
        os.system(f'tcdel {self._network_interface}')


class DiscreteNetworkChannel(NetworkChannel):

    def __init__(self, destination_node, timestamp_func, distr_func, interval):
        super().__init__(destination_node, timestamp_func, distr_func, interval)
        self._queue = PriorityQueue()
        self._delay = None

    def bind(self, source_node):
        ...

    def _apply_delay(self):
        self._delay = self._distr_func()

    def send(self, msg):
        current_timestamp = self._timestamp_func()
        self._queue.put(self.TimingEvent(lambda: self.destination_node.receive_msg(msg), current_timestamp + self._delay))

    def quit(self):
        pass

    def tick(self):
        super()
        if not self._queue.empty() and self._queue.queue[0].timestamp_scheduled <= self._timestamp_func():
            self._queue.get().event()

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


if __name__ == '__main__':
    ...
