import pickle
from abc import ABC


class NetworkMessage(ABC):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def to_bytes(self):
        return pickle.dumps(self)

    @staticmethod
    def from_bytes(msg_bytes):
        return pickle.loads(msg_bytes)


# from operator to vehicle (or from mec?)
class InstructionNetworkMessage(NetworkMessage):
    def __init__(self, command):
        self.command = command


# from vehicle to mec
class InfoUpdateNetworkMessage(NetworkMessage):
    ...


# from mec to operator
class AugmentedInfoUpdateNetworkMessage(NetworkMessage):
    ...


