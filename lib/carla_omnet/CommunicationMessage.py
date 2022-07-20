import abc
import json


class CommunicationMessage(abc.ABC):
    @classmethod
    def from_json(cls, j):
        return cls(**json.loads(j))
        # for key, value in json.loads(j):
        #     setattr(self, key, value)

class SimulationStepRequest(CommunicationMessage):
    def __init__(self, timestamp):
        self.timestamp = timestamp


class SimulationStepAnswer:
    def __init__(self, location):
        self.location = location


class ReceiveMessageAnswer:
    def __init__(self, message_id, size):
        self.message_id = message_id
        self.size = size