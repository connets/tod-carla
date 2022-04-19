import socket
from abc import ABC
from typing import List

from src.network.NetworkInterface import NetworkInterface


class NetworkNode(ABC):

    def __init__(self, host, port, network_interface):
        self.host = host
        self.port = port
        # self._network_delay_manager = NetworkChannel()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._next_steps: List[NetworkNode] = []
        self._network_interface = network_interface

    def start(self):
        self._network_interface.bind(self)

    def create_channel(self, network_node):
        self._next_steps.append(network_node)  # Add next step, for building the network

    def send_message(self, network_message):
        for network_node in self._next_steps:
            self._network_interface.send(network_message, network_node)

    def bind(self, host, port):
        self._socket.bind((host, port))  # Bind to the port

    def quit(self):
        self._socket.close()


class OperatorNetworkNode(NetworkNode):
    ...


class MecNetworkNode(NetworkNode):
    ...


class VehicleNetworkNode(NetworkNode):
    ...
