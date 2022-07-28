import itertools
from abc import ABC, abstractmethod

import carla
import zmq
import json

from src.args_parse.TeleConfiguration import TeleConfiguration
from src.build_enviroment import EnvironmentBuilder
from src.carla_bridge.TeleWorld import TeleWorld
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


class CarlaOMNeTManager(ABC):
    _id_iter = itertools.count(1000)

    def __init__(self, protocol, port, connection_timeout, timeout):
        self._protocol = protocol
        self._port = port
        self._connection_timeout = connection_timeout
        self._timeout = timeout

        self.tele_world: TeleWorld = None
        self.actors = self.operators = None
        self.timestamp = 0
        self.socket = None
        self._message_handler_state: MessageHandlerState = None

    def set_message_handler_state(self, msg_handler_cls):
        self._message_handler_state = msg_handler_cls(self)

    def _receive_data_from_omnet(self):
        message = self.socket.recv()
        json_data = json.loads(message.decode("utf-8"))
        request = OMNeTMessage.from_json(json_data)
        self.timestamp = request.timestamp
        return request

    def _send_data_to_omnet(self, answer):
        self.socket.send(answer.to_json())

    def _start_server(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"{self._protocol}://*:{self._port}")
        self.socket.RCVTIMEO = self.socket.SNDTIMEO = int(self._connection_timeout * 1000)
        print("server running")

    def start_simulation(self):
        self._start_server()
        self.set_message_handler_state(StartMessageHandlerState)
        while True:
            message = self._receive_data_from_omnet()
            answer = self._message_handler_state.handle_message(message)
            self._send_data_to_omnet(answer)


class MessageHandlerState(ABC):
    def __init__(self, carla_omnet_manager: CarlaOMNeTManager):
        self._manager = carla_omnet_manager

    def handle_message(self, message: OMNeTMessage) -> CarlaMessage:
        raise RuntimeError(f"""I'm in the following state: {self.__class__.__name__} and 
                    I don't know how to handle {message.__class__.__name__} message""")


class StartMessageHandlerState(MessageHandlerState):

    def handle_message(self, message: OMNeTMessage):
        if isinstance(message, InitOMNeTMessage):
            payload = message.payload
            world_builder = EnvironmentBuilder(payload['seed'], payload['carla_world_configuration'],
                                               payload['carla_timestep'], payload['actors'])
            world_builder.build()

            self._manager.actors = world_builder.actors.copy()
            self._manager.operators = world_builder.operators.copy()
            self._manager.tele_world = world_builder.tele_world

            self._manager.set_message_handler_state(RunningMessageHandlerState)

            return InitCompletedCarlaMessage(round(self._manager.tele_world.timestamp.elapsed_seconds, 9))
        else:
            super(StartMessageHandlerState, self).handle_message(message)


class RunningMessageHandlerState(MessageHandlerState):
    _id_iter = itertools.count(1000)

    def __init__(self, carla_omnet_manager: CarlaOMNeTManager):
        super().__init__(carla_omnet_manager)
        self.status = dict()
        self.instructions = dict()

    def handle_message(self, message: OMNeTMessage):
        if isinstance(message, SimulationStepOMNetMessage):
            self._manager.tele_world.tick()
            payload = dict()
            actors_payload = []
            for actor_id, actor in self._manager.actors.items():
                transorm: carla.Transform = actor.get_transform()
                velocity: carla.Vector3D = actor.get_velocity()
                actor_payload = dict()
                actor_payload['actor_id'] = actor_id
                actor_payload['position'] = [transorm.location.x, transorm.location.y, transorm.location.z]
                actor_payload['rotation'] = [transorm.rotation.pitch, transorm.rotation.yaw, transorm.rotation.roll]
                actor_payload['velocity'] = [velocity.x, velocity.y, velocity.z]
                actors_payload.append(actor_payload)
            payload['actors'] = actors_payload
            return UpdatedPositionCarlaMessage(payload)

        elif isinstance(message, ActorStatusOMNetMessage):
            actor_id = message.payload['actor_id']
            actor_status = self._manager.actors[actor_id].generate_status()
            status_id = str(next(self._id_iter))
            self.status[status_id] = actor_status
            payload = dict()
            payload['actor_id'] = actor_id
            payload['status_id'] = status_id
            return ActorStatusCarlaMessage(payload)

        elif isinstance(message, ComputeInstructionOMNeTMessage):
            agent_id = message.payload['agent_id']
            actor_id = message.payload['actor_id']
            status_id = message.payload['status_id']
            status = self.status[status_id]
            agent = self._manager.operators[agent_id]
            instruction = agent.receive_vehicle_state_info(status, self._manager.tele_world.timestamp.elapsed_seconds)
            instruction_id = str(next(self._id_iter))
            self.instructions[instruction_id] = instruction
            payload = dict()
            payload['instruction_id'] = instruction_id
            payload['actor_id'] = actor_id
            return InstructionCarlaMessage(payload)

        elif isinstance(message, ApplyInstructionOMNeTMessage):
            instruction_id = message.payload['instruction_id']
            actor_id = message.payload['actor_id']
            actor = self._manager.actors[actor_id]
            actor.apply_instruction(self.instructions[instruction_id])
            return OkCarlaMessage(dict())
        else:
            super().handle_message(message)


class CarlaOmnetManagerOld:
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
    TeleConfiguration('configuration/server/ubiquity.yaml')
    manager = CarlaOMNeTManager('tcp', 1234, 100, 20)
    manager.start_simulation()
