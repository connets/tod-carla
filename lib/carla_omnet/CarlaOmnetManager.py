import itertools

import zmq
import json
from types import SimpleNamespace

from lib.carla_omnet.CommunicationMessage import SimulationStepRequest, HandshakeRequest, \
    SimulationRequest, ReceiveMessageRequest, ReceiveMessageAnswer, SimulationStepAnswer


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

    def __init__(self, protocol, port, connection_timeout, timeout, vehicle_actual_position):
        self.step_listener = None
        self._vehicle_actual_location = vehicle_actual_position

        self._messages_to_send = set()
        self._actions_to_do = dict()

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"{protocol}://*:{port}")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(connection_timeout * 1000)

        print("Waiting for connection...")
        handshake = self._receive_data()
        if not isinstance(handshake, HandshakeRequest):
            raise RuntimeError("Error in connection")

        self.socket.send(b"Hello")
        print("Connected!")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(timeout * 1000)

    def _receive_data(self):
        message = self.socket.recv()
        print(message)
        json_data = json.loads(message.decode("utf-8"))
        print(json_data.keys())
        return SimulationRequest.from_json_factory(json_data)

    def start(self, step_listener=None):
        self.step_listener = step_listener
        self._do_simulation()

    def _do_simulation(self):
        while True:
            request = self._receive_data()
            if isinstance(request, SimulationStepRequest):
                if self.step_listener is not None:
                    self.step_listener(request.timestamp)
                answer = SimulationStepAnswer(self._vehicle_actual_location())
                self.socket.send(json.dumps(answer.__dict__).encode("utf-8"))
                continue
            elif isinstance(request, ReceiveMessageRequest):
                action = self._messages_to_send[request.msg_id]
                action()
            else:
                ...
            messages = []
            for msg in self._messages_to_send:
                msg_id = next(self._id_iter)
                self._actions_to_do[msg_id] = msg
                messages.append(ReceiveMessageAnswer(msg_id, 100))  # TODO change to allow multi-messages as answer
            self._messages_to_send.clear()

            self.socket.send(json.dumps(messages).encode("utf-8"))

    def send_message(self, message):
        self._messages_to_send.add(message)


#  Socket to talk to server
if __name__ == '__main__':
    manager = CarlaOmnetManager('tcp', 5555, 100, 20, lambda:  "2")
    manager.start()


