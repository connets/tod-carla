import abc
import enum
import json


class OMNeTMessage(abc.ABC):
    ...


class InitOMNeTMessage(OMNeTMessage):
    ...


class CoSimulationAnswer(abc.ABC):
    def to_json(self):
        return json.dumps(self.__dict__).encode("utf-8")


class CoSimulationRequest:
    def __init__(self, timestamp):
        self.timestamp = timestamp

    @staticmethod
    def from_json(j):
        classes = {HandshakeRequest, StepRequest, ReceiveMessageRequest}
        msg_type = j['request_type']
        del j['request_type']
        for cls in classes:
            if cls.request_type == msg_type:
                return cls(**j)

        raise RuntimeError(f"Message type {msg_type} not recognized")
        # for key, value in json.loads(j):
        #     setattr(self, key, value)


class HandshakeRequest(CoSimulationRequest):
    request_type = 'handshake'


class HandshakeAnswer(CoSimulationAnswer):
    def __init__(self, timestamp):
        self.timestamp = timestamp


class StepRequest(CoSimulationRequest):
    request_type = 'simulation_step'


class StepAnswer(CoSimulationAnswer):
    def __init__(self, location):
        self.location = location


class ReceiveMessageRequest(CoSimulationRequest):
    request_type = 'receive_msg'

    def __init__(self, timestamp, msg_id):
        super().__init__(timestamp)
        self.msg_id = msg_id


class ReceiveMessageAnswer(CoSimulationAnswer):
    def __init__(self, msg_id, size):
        self.msg_id = msg_id
        self.size = size
