import pickle
from abc import ABC, abstractmethod


class NetworkMessage(ABC):
    def __init__(self):
        self.timestamp = None

    def to_bytes(self):
        return pickle.dumps(self)

    @staticmethod
    def from_bytes(msg_bytes):
        return pickle.loads(msg_bytes)

    @abstractmethod
    def action(self, destination):
        ...


# from operator to vehicle (or from mec?)
class InstructionNetworkMessage(NetworkMessage):
    def __init__(self, command):
        super().__init__()
        self.command = command

    def action(self, destination):
        destination.receive_instruction_network_message(self.command)
        ...


# from vehicle to mec
class InfoUpdateNetworkMessage(NetworkMessage):
    def __init__(self, snapshot):
        super().__init__()
        self._snapshot = snapshot

    def action(self, destination):
        destination.receive_state_info(self._snapshot)


# from mec to operator
class AugmentedInfoUpdateNetworkMessage(NetworkMessage):
    def action(self, destination):
        ...
