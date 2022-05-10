import os
import re
import socket
from abc import ABC, abstractmethod
from collections.abc import Callable
from queue import PriorityQueue

from src.TeleContext import TeleContext
from src.network.NetworkMessage import NetworkMessage
from src.utils.decorators import needs_member
from src.utils.distribution_utils import _constant_family
from threading import Thread


class NetworkChannel(ABC):
    def __init__(self, destination_node, distr_func, interval):
        self.destination_node = destination_node

        self._distr_func = distr_func
        self._interval = interval
        self._delay = distr_func()
        self._binded = False

    @needs_member('_binded', lambda x: x)
    def start(self, tele_context):
        self._tele_context = tele_context

        def change_delay():
            self._apply_delay()
            self._tele_context.schedule(change_delay, self._interval)

        change_delay()

    @abstractmethod
    def _apply_delay(self):
        ...

    def bind(self, source_node):
        self._binded = True

    @abstractmethod
    def send(self, msg):
        ...

    @abstractmethod
    def quit(self):
        ...


class PhysicNetworkChannel(NetworkChannel):
    def __init__(self, destination_node, distr_func, interval):
        super().__init__(destination_node, distr_func, interval)
        self._last_tick_timestamp = 0
        # self.network_node = None
        # self._socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # UDP socket
        self._out_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self._input_daemon = None

    # def start(self):
    #     current_timestamp = self._timestamp_func()
    #     if current_timestamp >= self._last_tick_timestamp + self._interval:
    #         self._apply_delay()
    #         self._last_tick_timestamp = current_timestamp

    def bind(self, source_node):
        super().bind(source_node)

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
                        msg.action(source_node)
                    except socket.timeout:
                        ...

        self._input_daemon = InputDaemon()
        self._input_daemon.start()

    def send(self, msg):
        super().send(msg)
        # self._socket.connect((destination_node.host, destination_node.port))
        self._out_socket.sendto(msg.to_bytes(), (self.destination_node.host, self.destination_node.port))
        # init_msg = NetworkMessage.from_bytes(s.recv(4096))
        # print(datetime.datetime.now().timestamp() - init_msg.timestamp)

    def quit(self):
        if self._input_daemon is not None:
            self._input_daemon.stop()


class TcNetworkInterface(PhysicNetworkChannel):

    def __init__(self, destination_node, distr_func, interval, network_interface):
        super().__init__(destination_node, distr_func, interval)
        self._network_interface = network_interface


    def _apply_delay(self):
        tc_config = f"""tcset {self._network_interface} --delay {self._distr_func()}ms --network {self.destination_node.host} --port {self.destination_node.port} --change"""  # TODO change stderr
        # print(tc_config)
        os.system(tc_config)

class DiscreteNetworkChannel(NetworkChannel):

    def __init__(self, destination_node, distr_func, interval):
        super().__init__(destination_node, distr_func, interval)
        self._tele_context = None

    def _apply_delay(self):
        self._delay = self._distr_func()

    @needs_member('_tele_context')
    def send(self, msg):
        super().send(msg)

        def send_message():
            msg.action(self.destination_node)

        send_message.__name__ += '_' + re.sub(r'(?<!^)(?=[A-Z])', '_', msg.__class__.__name__).lower()

        self._tele_context.schedule(send_message, self._delay)

    def quit(self):
        pass


if __name__ == '__main__':
    ...
