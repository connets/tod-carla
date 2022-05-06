import json
import pickle
from abc import ABC, abstractmethod


class NetworkMessage(ABC):
    def __init__(self, timestamp=None, periodic=False):
        self.timestamp = timestamp
        self.periodic = periodic

    def to_bytes(self):
        return pickle.dumps(self)  # TODO this isn't working

    @staticmethod
    def from_bytes(msg_bytes):
        return pickle.loads(msg_bytes)

    @abstractmethod
    def action(self, destination):
        ...


# from operator to vehicle (or from mec?)
class InstructionNetworkMessage(NetworkMessage):
    def __init__(self, command, timestamp=None, periodic=False):
        super().__init__(timestamp, periodic)
        self.command = command

    def action(self, destination):
        destination.receive_instruction_network_message(self.command)
        ...


# from vehicle to mec
class InfoUpdateNetworkMessage(NetworkMessage):
    def __init__(self, tele_vehicle_state, timestamp=None, periodic=False):
        super().__init__(timestamp, periodic)

        self._tele_vehicle_state = tele_vehicle_state

    def action(self, destination):
        destination.receive_vehicle_state_info(self._tele_vehicle_state, self.timestamp)


# from mec to operator
class AugmentedInfoUpdateNetworkMessage(NetworkMessage):
    def action(self, destination):
        ...
