import abc
import enum
import json
import re
from typing import List

import carla

from src.actor.TeleCarlaActor import TeleCarlaActor


class OMNeTMessage(abc.ABC):

    def __init__(self, timestamp, payload):
        self.timestamp = timestamp
        self.payload = payload

    @classmethod
    def from_json(cls, j):
        def remove_null_object(item: dict):
            keys_to_remove = set()
            for key, value in item.items():
                if isinstance(value, dict):
                    remove_null_object(value)
                elif isinstance(value, str) and re.match(r'^\s*$', value):
                    keys_to_remove.add(key)
            for key in keys_to_remove: del item[key]

        classes = cls.__subclasses__()
        msg_type = j['message_type']
        print(cls.__subclasses__())
        del j['message_type']
        for msg_cls in classes:
            if msg_cls.MESSAGE_TYPE == msg_type:
                instance = msg_cls(**j)
                payload = instance.payload
                remove_null_object(payload)
                return instance

        raise RuntimeError(f"Message type {msg_type} not recognized")


class InitOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = "INIT"


class SimulationStepOMNetMessage(OMNeTMessage):
    MESSAGE_TYPE = 'SIMULATION_STEP'


class ActorStatusOMNetMessage(OMNeTMessage):
    MESSAGE_TYPE = 'VEHICLE_STATUS_UPDATE'


class ComputeInstructionOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = 'COMPUTE_INSTRUCTION'


class ApplyInstructionOMNeTMessage(OMNeTMessage):
    MESSAGE_TYPE = 'APPLY_INSTRUCTION'


class CarlaMessage(abc.ABC):
    def __init__(self, payload):
        self.payload = payload

    def to_json(self):
        res = self.__dict__.copy()
        res['message_type'] = self.__class__.MESSAGE_TYPE
        return json.dumps(res).encode("utf-8")


class InitCompletedCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'INIT_COMPLETED'


class UpdatedPositionCarlaMessage(CarlaMessage):
    MESSAGE_TYPE = 'UPDATED_POSITIONS'

    @staticmethod
    def generate_payload(actors : List[TeleCarlaActor]):
        payload = dict()
        for actor in actors:
            t = actor.get_transform()


