import re
from abc import ABC, abstractmethod

from lib.carla_omnet.CarlaOmnetManager import CarlaOmnetManager
from src.core import TeleEvent
from src.core.TeleEvent import tele_event, EventType
from src.utils.decorators import preconditions


class NetworkChannel(ABC):
    def __init__(self, destination_node):
        self.destination_node = destination_node
        self._binded = False
        self._tele_context = None

    @preconditions('_binded', valid=lambda x: x)
    def start(self, tele_context):
        self._tele_context = tele_context

    def bind(self, source_node):
        self._binded = True

    def _create_event(self, msg):
        @tele_event('send_' + re.sub(r'(?<!^)(?=[A-Z])', '_', msg.__class__.__name__).lower() + '-' + str(id(msg)),
                    EventType.NETWORK)
        def network_event():
            msg.action(self.destination_node)

        return network_event

    @abstractmethod
    def send(self, msg):
        ...

    @abstractmethod
    def quit(self):
        ...


class TODNetworkChannel(NetworkChannel):
    def __init__(self, destination_node, distr_func, interval):
        super().__init__(destination_node)
        self._distr_func = distr_func
        self._interval = interval
        self._delay = distr_func()
        self._binded = False

    @preconditions('_binded', valid=lambda x: x)
    def start(self, tele_context):
        super().start(tele_context)

        @tele_event('change_delay_network_channel-' + str(id(self)))
        def change_delay():
            self._delay = self._distr_func()
            self._tele_context.schedule(change_delay, self._interval)

        change_delay()

    @preconditions('_tele_context')
    def send(self, msg):
        network_event = self._create_event(msg)
        self._tele_context.schedule(network_event, self._delay)

    def quit(self):
        ...


class CarlaOmnetNetworkChannel(NetworkChannel):
    def __init__(self, destination_node, carla_omnet_manager: CarlaOmnetManager):
        super().__init__(destination_node)
        self._carla_omnet_manager = carla_omnet_manager
        self._binded = False

    def bind(self, source_node):
        self._binded = True

    @preconditions('_carla_omnet_manager')
    def send(self, msg):
        network_event = self._create_event(msg)
        self._carla_omnet_manager.send_message(network_event)

    def quit(self):
        ...


if __name__ == '__main__':
    ...
