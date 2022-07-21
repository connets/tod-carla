import abc
import json


class CommunicationMessage(abc.ABC):
    ...


class SimulationRequest:
    @staticmethod
    def from_json_factory(j):
        classes = {HandshakeRequest, SimulationStepRequest, ReceiveMessageRequest}
        msg_type = j['request_type']
        del j['request_type']
        for cls in classes:
            if cls.request_type == msg_type:
                return cls(**j)

        raise RuntimeError(f"Message type {msg_type} not recognized")
        # for key, value in json.loads(j):
        #     setattr(self, key, value)


class HandshakeRequest(SimulationRequest):
    request_type = 'handshake'


class SimulationStepRequest(SimulationRequest):
    request_type = 'simulation_step'

    def __init__(self, timestamp):
        self.timestamp = timestamp


class ReceiveMessageRequest(SimulationRequest):
    request_type = 'receive_msg'

    def __init__(self, timestamp, msg_id):
        self.timestamp = timestamp
        self.msg_id = msg_id


class SimulationStepAnswer(CommunicationMessage):
    def __init__(self, location):
        self.location = location


class ReceiveMessageAnswer(CommunicationMessage):
    def __init__(self, message_id, size):
        self.message_id = message_id
        self.size = size
