import pickle
from abc import ABC


class NetworkMessage(ABC):
    def __init__(self, timestmap):
        self.timestamp = timestmap

    def to_bytes(self):
        return pickle.dumps(self)

    @staticmethod
    def from_bytes(msg_bytes):
        return pickle.loads(msg_bytes)