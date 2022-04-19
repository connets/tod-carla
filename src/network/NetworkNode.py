import socket
from abc import ABC
from typing import List

from src.network.NetworkDelayManager import NetworkDelayManager


class NetworkNode(ABC):
    def __init__(self):
        self._network_delay_manager = NetworkDelayManager()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._next_steps: List[NetworkNode] = []

    def add_next_step(self, network_node):
        self._next_steps.append(network_node)  # Add next step, for building the network

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
