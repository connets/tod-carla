import itertools
from abc import ABC, abstractmethod

import zmq
import json

from src.carla_omnet.CommunicationMessage import *


class CarlaOmnetError(RuntimeError):
    ...


class CarlaOmnetCommunicationError(CarlaOmnetError):
    ...


class UnknownMessageCarlaOmnetError(RuntimeError):
    def __init__(self, unknown_msg):
        self.unknown_msg = unknown_msg

    def __repr__(self) -> str:
        return "I don't know how to handle the following msg: " + self.unknown_msg


class MessageHandlerState(ABC):
    def __init__(self, carla_omnet_manager):
        self._carla_omnet_manager = carla_omnet_manager

    @abstractmethod
    def handle_message(self, message: OMNeTMessage):
        ...


class StartMessageHandlerState(MessageHandlerState):

    def handle_message(self, message: OMNeTMessage):
        if isinstance(message, InitOMNeTMessage):
            ...
        else:
            RuntimeError(f"""I'm in the following state: {self.__class__.__name__} and 
            I don't know how to handle {message.__class__.__name__} message""")


class CarlaOMNeTManager(ABC):

    def __init__(self):
        self._socket = None
        self._message_handler_state = None

        self.set_message_handler_state(StartMessageHandlerState)

    def set_message_handler_state(self, msg_handler_cls):
        self._message_handler_state = msg_handler_cls(self)

    @abstractmethod
    def handle_message(self):
        ...

    def _receive_data_from_omnet(self):
        message = self._socket.recv()
        json_data = json.loads(message.decode("utf-8"))
        request = CoSimulationRequest.from_json(json_data)
        self.timestamp = request.timestamp
        return request

    def _send_data_to_omnet(self, answer: CoSimulationAnswer):
        self._socket.send(answer.to_json())


class CarlaOmnetManager:
    _id_iter = itertools.count(1000)

    def __init__(self, protocol, port, connection_timeout, timeout):
        self._protocol = protocol
        self._port = port
        self._connection_timeout = connection_timeout
        self._timeout = timeout
        self.timestamp = 0

    def _receive_data_from_omnet(self):
        message = self.socket.recv()
        json_data = json.loads(message.decode("utf-8"))
        request = CoSimulationRequest.from_json(json_data)
        self.timestamp = request.timestamp
        return request

    def _connect(self, current_timestamp):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"{self._protocol}://*:{self._port}")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(self._connection_timeout * 100000)

        print("Waiting for connection...")
        handshake = self._receive_data_from_omnet()
        if not isinstance(handshake, HandshakeRequest):
            raise RuntimeError("Error in connection")

        self._send_data_to_omnet(HandshakeAnswer(current_timestamp))
        print("Connected!")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(self._timeout * 500000)

    def do_omnet_step(self):
        if self._last_received_request is not None:
            # TODO change to allow multi-messages as answer
            if self._message_to_send is not None:
                msg_id = next(self._id_iter)
                self._actions_to_do[msg_id] = self._message_to_send
                answer = ReceiveMessageAnswer(msg_id, 100)
            else:
                answer = ReceiveMessageAnswer(-1, -1)
            self._message_to_send = None
            self._send_data_to_omnet(answer)

        action = None
        while action is None:
            self._last_received_request = request = self._receive_data_from_omnet()
            if isinstance(request, StepRequest):
                self._send_data_to_omnet(StepAnswer(self._vehicle_actual_location()))
            elif isinstance(request, ReceiveMessageRequest):
                action = self._actions_to_do.get(request.msg_id, self._default_actions.get(request.msg_id))
                self._actions_to_do.pop(request.msg_id, None)
            else:
                raise RuntimeError("Message don't recognize", request.type)

        return action

    def has_scheduled_events(self):
        return

    def add_default_action(self, id, action):
        self._default_actions[id] = action

    def schedule_message(self, message):
        self._message_to_send = message


#  Socket to talk to server
if __name__ == '__main__':
    manager = CarlaOmnetManager('tcp', 5555, 100, 20, lambda: "2")


    def car_send_msg():
        print('**** CAR send msg')
        manager.schedule_message(server_receive_msg)


    def server_receive_msg():
        print('**** SERVER received msg')
        manager.schedule_message(car_receive_msg)


    def car_receive_msg():
        print('**** CAR received msg')


    manager.add_default_action(1, car_send_msg)

    manager.start(lambda ts: print("updated with timestamp", ts))
