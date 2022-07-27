import abc
import enum
import json


class OMNeTMessage(abc.ABC):

    def __init__(self, timestamp, payload):
        self.timestamp = timestamp
        self.payload = payload

    @classmethod
    def from_json(cls, j):
        classes = cls.__subclasses__()
        msg_type = j['message_type']
        del j['message_type']
        for msg_cls in classes:
            if msg_cls.MESSAGE_TYPE == msg_type:
                return msg_cls(**j)

        raise RuntimeError(f"Message type {msg_type} not recognized")


class InitOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = "INIT"


class SimulationStepOMNetMessage(OMNeTMessage):
    MESSAGE_TYPE = 'SIMULATION_STEP'


class VehicleStatusOMNetMessage(OMNeTMessage):
    MESSAGE_TYPE = 'VEHICLE_STATUS_UPDATE'


class ComputeInstructionOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = 'COMPUTE_INSTRUCTION'


class ApplyInstructionOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = 'APPLY_INSTRUCTION'


class CarlaMessage(abc.ABC):
    def to_json(self):
        res = self.__dict__.copy()
        res['message_type'] = self.__class__.MESSAGE_TYPE
        return json.dumps(res).encode("utf-8")


class InitCompletedCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'INIT_COMPLETED'

    def __init__(self, payload):
        self.payload = payload


if __name__ == '__main__':
    tmp = dict()
    tmp['initial_timestamp'] = 100.34

    i = InitCompletedCarlaMessage(tmp)
    print(i.to_json())


class CoSimulationAnswer(abc.ABC):
    ...


class CoSimulationRequest:
    def __init__(self, timestamp):
        self.timestamp = timestamp

    @staticmethod
    def from_json(j):
        classes = {HandshakeRequest, StepRequest, ReceiveMessageRequest}
        msg_type = j['message_type']
        del j['request_type']
        for cls in classes:
            if cls.message_type == msg_type:
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
