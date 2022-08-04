import abc
import json
import re


class OMNeTMessage(abc.ABC):

    def __init__(self, timestamp, payload):
        self.timestamp = round(timestamp, 6)
        self.payload = payload

    @classmethod
    def from_json(cls, j):
        def clean_objects(item: dict):
            keys_to_remove = set()
            for key, value in item.items():
                if isinstance(value, list):
                    for v in value: clean_objects(v)
                elif isinstance(value, dict):
                    clean_objects(value)
                elif isinstance(value, str):  # remove null object or empty string
                    if re.match(r'^\s*$', value):
                        keys_to_remove.add(key)
                    else:

                        item[key] = value.replace('"', '')
            for key in keys_to_remove: del item[key]

        classes = cls.__subclasses__()
        msg_type = j['message_type']
        del j['message_type']
        for msg_cls in classes:
            if msg_cls.MESSAGE_TYPE == msg_type:
                instance = msg_cls(**j)
                payload = instance.payload
                clean_objects(payload)
                return instance

        raise RuntimeError(f"Message type {msg_type} not recognized")

    def __repr__(self) -> str:
        return self.to_json()

    def to_json(self):
        res = self.__dict__.copy()
        res['message_type'] = self.__class__.MESSAGE_TYPE
        return json.dumps(res)


class InitOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = "INIT"


class SimulationStepOMNetMessage(OMNeTMessage):
    MESSAGE_TYPE = 'SIMULATION_STEP'


class ActorStatusOMNetMessage(OMNeTMessage):
    MESSAGE_TYPE = 'ACTOR_STATUS_UPDATE'


class ComputeInstructionOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = 'COMPUTE_INSTRUCTION'


class ApplyInstructionOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = 'APPLY_INSTRUCTION'


class CarlaMessage(abc.ABC):
    def __init__(self, payload, simulation_finished=False):
        self.payload = payload
        self.simulation_finished = simulation_finished

    def __repr__(self) -> str:
        return self.to_json().decode('utf-8')

    def to_json(self):
        res = self.__dict__.copy()
        res['message_type'] = self.__class__.MESSAGE_TYPE
        return json.dumps(res).encode('utf-8')


class InitCompletedCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'INIT_COMPLETED'


class UpdatedPositionCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'UPDATED_POSITIONS'


class ActorStatusCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'ACTOR_STATUS'


class InstructionCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'INSTRUCTION'


class OkCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'OK'
