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
    _id_iter = itertools.count(1000)

    def __init__(self, protocol, port, connection_timeout, timeout, vehicle_actual_position):
        self.step_listener = None
        self._vehicle_actual_location = vehicle_actual_position
        self._last_timestamp = 0
        self._message_to_send = None  # TODO change here for multiple-messages
        self._default_actions = dict()
        self._actions_to_do = dict()

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"{protocol}://*:{port}")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(connection_timeout * 100000)

        print("Waiting for connection...")
        handshake = self._receive_data()
        if not isinstance(handshake, HandshakeRequest):
            raise RuntimeError("Error in connection")

        self.socket.send(b"Hello")
        print("Connected!")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(timeout * 500000)

    def _receive_data(self):
        message = self.socket.recv()
        print(message)
        json_data = json.loads(message.decode("utf-8"))
        return SimulationRequest.from_json_factory(json_data)

    def start(self, step_listener):
        assert step_listener is not None
        self.step_listener = step_listener
        self._do_simulation()

    def _do_simulation(self):
        while True:
            request = self._receive_data()
            if isinstance(request, SimulationStepRequest):
                self.step_listener(request.timestamp)
                answer = SimulationStepAnswer(self._vehicle_actual_location())
            elif isinstance(request, ReceiveMessageRequest):
                self.step_listener(request.timestamp)
                action = self._actions_to_do.get(request.msg_id, self._default_actions.get(request.msg_id))
                action()
                self._actions_to_do.pop(request.msg_id, None)
                if self._message_to_send is not None:
                    msg_id = next(self._id_iter)
                    self._actions_to_do[msg_id] = self._message_to_send
                    answer = ReceiveMessageAnswer(msg_id, 100)
                else:
                    answer = ReceiveMessageAnswer(-1, -1)
            else:

                raise RuntimeError("Message don't recognize", request.type)
            # TODO change to allow multi-messages as answer
            # messages.append(ReceiveMessageAnswer(msg_id, 100))
            self._message_to_send = None
            if answer is not None:
                self.socket.send(json.dumps(answer.__dict__).encode("utf-8"))

    def add_default_action(self, id, action):
        self._default_actions[id] = action

    def send_message(self, message):
        self._message_to_send = message


#  Socket to talk to server
if __name__ == '__main__':
    manager = CarlaOmnetManager('tcp', 5555, 100, 20, lambda: "2")


    def car_send_msg():
        print('**** CAR send msg')
        manager.send_message(server_receive_msg)

    def server_receive_msg():
        print('**** SERVER received msg')
        manager.send_message(car_receive_msg)

    def car_receive_msg():
        print('**** CAR received msg')


    manager.add_default_action(1, car_send_msg)

    manager.start(lambda ts: print("updated with timestamp", ts))
