import socket
from abc import ABC
from typing import List

from src.network.NetworkChannel import NetworkChannel


class NetworkNode(ABC):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        # self._network_delay_manager = NetworkChannel()
        self._channels: List[NetworkChannel] = []

    def add_channel(self, channel):
        channel.bind(self)
        self._channels.append(channel)


    def send_message(self, network_message):
        for channel in self._channels:
            channel.send(network_message)

    def quit(self):
        for channel in self._channels:
            channel.quit()


class OperatorNetworkNode(NetworkNode):
    ...


class MecNetworkNode(NetworkNode):
    ...


class VehicleNetworkNode(NetworkNode):
    ...
