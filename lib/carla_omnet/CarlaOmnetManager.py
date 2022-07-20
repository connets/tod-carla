import itertools

import zmq
import json
from types import SimpleNamespace

from lib.carla_omnet.CommunicationMessage import CommunicationMessage, SimulationStepRequest


class CarlaOmnetError(RuntimeError):
    ...


class CarlaOmnetCommunicationError(CarlaOmnetError):
    ...


class UnknownMessageCarlaOmnetError(RuntimeError):
    def __init__(self, unknown_msg):
        self.unknown_msg = unknown_msg

    def __repr__(self) -> str:
        return "I don't know how to handle the following msg: " + self.unknown_msg


class CarlaOmnetManager:
    _id_iter = itertools.count(0)

    def __init__(self, protocol, port, init_timeout, timeout, vehicle_actual_position, step_listener=None):
        self._vehicle_actual_position = vehicle_actual_position
        self.step_listener = step_listener

        self._messages_to_send = set()
        self._queued_messages = dict()

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"{protocol}://*:{port}")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = init_timeout * 1000

        print("Waiting for connection...")
        handshake = self._receive_data()
        print(handshake)
        self.socket.send(b"Hello")

        print("Connected!")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = timeout * 1000

    def _receive_data(self):
        message = self.socket.recv()
        return json.loads(message.decode("utf-8"))

    def start(self):
        message = self._receive_data()
        if message.type == 'simulation_step':
            if self.step_listener is not None:
                self.step_listener(message.timestamp)
        elif message.type == 'receive_msg':
            ...
        else:
            ...
        for msg in self._messages_to_send:
            msg_id = next(self._id_iter)
            self._queued_messages[msg_id] = msg
        self._messages_to_send.clear()

        self.socket.send(b"Hello")

    def send_message(self, message):
        self._messages_to_send.add(message)


#  Socket to talk to server
if __name__ == '__main__':
    tmp = '{"timestamp": 2345}'
    obj = SimulationStepRequest.from_json(tmp)
    print(obj.timestamp)
