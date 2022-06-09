import os
import re
import socket
from abc import ABC, abstractmethod
from collections.abc import Callable
from queue import PriorityQueue

from src.TeleEvent import tele_event
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

        @tele_event('change_delay_network_channel')
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


class DiscreteNetworkChannel(NetworkChannel):

    def __init__(self, destination_node, distr_func, interval):
        super().__init__(destination_node, distr_func, interval)
        self._tele_context = None

    def _apply_delay(self):
        self._delay = self._distr_func()

    @needs_member('_tele_context')
    def send(self, msg):
        super().send(msg)

        @tele_event('send_' + re.sub(r'(?<!^)(?=[A-Z])', '_', msg.__class__.__name__).lower())
        def send_message():
            msg.action(self.destination_node)

        self._tele_context.schedule(send_message, self._delay)

    def quit(self):
        pass


if __name__ == '__main__':
    ...
