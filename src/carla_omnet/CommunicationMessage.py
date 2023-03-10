import abc
import enum
import json
import re

from src.carla_omnet.SimulationStatus import SimulationStatus


class CarlanetppMessage(abc.ABC):

    def __repr__(self) -> str:
        return self.to_json()

    def to_json(self):
        res = self.__dict__.copy()
        res['message_type'] = self.__class__.MESSAGE_TYPE
        return json.dumps(res)


class InitCarlanetppMessage(CarlanetppMessage):
    MESSAGE_TYPE = "INIT"

    def __init__(self, user_defined, carla_configuration, run_id):
        self.user_defined = user_defined
        self.carla_configuration = carla_configuration
        self.run_id = run_id


class SimulationStepCarlanetppMessage(CarlanetppMessage):
    MESSAGE_TYPE = 'SIMULATION_STEP'

    def __init__(self, omnet_timestamp):
        self.omnet_timestamp = omnet_timestamp


class CommonCarlanetppMessage(CarlanetppMessage):
    MESSAGE_TYPE = 'COMMON_MESSAGE'

    def __init__(self, timestamp, user_defined_message):
        self.omnet_timestamp = timestamp
        self.user_defined_message = user_defined_message

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
        msg_type = j['user_message_type']
        del j['user_message_type']
        for msg_cls in classes:
            if msg_cls.MESSAGE_TYPE == msg_type:
                instance = msg_cls(**j)
                user_defined = instance.user_defined
                clean_objects(user_defined)
                return instance

        raise RuntimeError(f"Message type {msg_type} not recognized")


class ActorStatusOMNetMessage(CommonCarlanetppMessage):
    USER_MESSAGE_TYPE = 'ACTOR_STATUS_UPDATE'


class ComputeInstructionCarlanetppMessage(CommonCarlanetppMessage):
    USER_MESSAGE_TYPE = 'COMPUTE_INSTRUCTION'


class ApplyInstructionCarlanetppMessage(CommonCarlanetppMessage):
    USER_MESSAGE_TYPE = 'APPLY_INSTRUCTION'
