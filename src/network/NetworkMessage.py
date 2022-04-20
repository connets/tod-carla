import pickle
from abc import ABC, abstractmethod


class NetworkMessage(ABC):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def to_bytes(self):
        return pickle.dumps(self)

    @staticmethod
    def from_bytes(msg_bytes):
        return pickle.loads(msg_bytes)

    @abstractmethod
    def action(self):
        ...


# from operator to vehicle (or from mec?)
class InstructionNetworkMessage(NetworkMessage):
    def __init__(self, timestamp, command):
        super().__init__(timestamp)
        self.command = command

    def action(self, ):
        pass


# from vehicle to mec
class InfoUpdateNetworkMessage(NetworkMessage):
    ...


# from mec to operator
class AugmentedInfoUpdateNetworkMessage(NetworkMessage):
    ...


