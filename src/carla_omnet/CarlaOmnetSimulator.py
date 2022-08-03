import itertools
from abc import ABC, abstractmethod

import carla
import zmq
import json

from src.TeleOutputWriter import DataCollector
from src.actor.TeleOperator import TeleOperator
from src.args_parse.TeleConfiguration import TeleConfiguration
from src.EnvironmentHandler import EnvironmentHandler
from src.carla_bridge.TeleWorld import TeleWorld
from src.carla_omnet.CommunicationMessage import *
from src.utils import utils


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
        self.environment_handler: EnvironmentHandler = None
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
        print("server running")

    def start_simulation(self):
        self._start_server()
        self.set_message_handler_state(StartMessageHandlerState)
        while True:
            try:
                message = self._receive_data_from_omnet()
                answer = self._message_handler_state.handle_message(message)
                print(message, answer, '\n\n')
                self._send_data_to_omnet(answer)
            except zmq.error.Again:
                print("Timeout happened")
                self._message_handler_state.timeout()


class MessageHandlerState(ABC):
    def __init__(self, carla_omnet_manager: CarlaOMNeTManager):
        self._manager = carla_omnet_manager

    def handle_message(self, message: OMNeTMessage) -> CarlaMessage:
        raise RuntimeError(f"""I'm in the following state: {self.__class__.__name__} and 
                    I don't know how to handle {message.__class__.__name__} message""")

    def timeout(self):
        ...


class StartMessageHandlerState(MessageHandlerState):

    def __init__(self, carla_omnet_manager: CarlaOMNeTManager):
        super().__init__(carla_omnet_manager)
        self._manager.socket.RCVTIMEO = self._manager.socket.SNDTIMEO = -1

    def handle_message(self, message: OMNeTMessage):
        if isinstance(message, InitOMNeTMessage):
            payload = message.payload
            environment_handler = EnvironmentHandler(payload['seed'], payload['carla_world_configuration'],
                                                     payload['carla_timestep'], payload['actors'])
            environment_handler.build()

            # self._manager.actors = world_builder.carla_actors.copy()
            # self._manager.operators = world_builder.external_actors.copy()
            tele_world = environment_handler.tele_world
            self._manager.environment_handler = environment_handler

            self._manager.set_message_handler_state(RunningMessageHandlerState)

            payload = dict()
            payload['initial_timestamp'] = round(tele_world.timestamp.elapsed_seconds, 9)

            return InitCompletedCarlaMessage(payload)
        else:
            super(StartMessageHandlerState, self).handle_message(message)


class RunningMessageHandlerState(MessageHandlerState):
    _id_iter = itertools.count(1000)
    _do_nothing_id = -1

    def __init__(self, carla_omnet_manager: CarlaOMNeTManager):
        super().__init__(carla_omnet_manager)
        self._manager.socket.RCVTIMEO = self._manager.socket.SNDTIMEO = -1

        self.status = dict()
        self.instructions = dict()
        environment_handler = self._manager.environment_handler
        self._tele_world = environment_handler.tele_world
        self._carla_actors = environment_handler.carla_actors
        self._external_actors = environment_handler.external_actors

        # self._collector = DataCollector("tmp/" + 'results.csv')
        # self._collector.write('timestamp', 'velocity_x', 'velocity_y', 'velocity_z', 'acceleration_x', 'acceleration_y',
        #                       'acceleration_z', 'location_x', 'location_y', 'location_z')

        # self.status_msg_id = 1
        # self.compute_instruction_msg_id = 1
        # self.apply_instruction_msg_id = 1

    def _simulation_step(self, message: SimulationStepOMNetMessage):
        self._tele_world.tick()
        payload = dict()
        actors_payload = []
        for actor_id, actor in self._carla_actors.items():
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

    def _actor_status(self, message: ActorStatusOMNetMessage):

        while any(not actor.done(self._tele_world.timestamp) for actor in self._carla_actors.values()):
            ...

        actor_id = message.payload['actor_id']
        actor_status = self._carla_actors[actor_id].generate_status()
        status_id = str(next(self._id_iter))
        self.status[status_id] = actor_status
        payload = dict()
        payload['actor_id'] = actor_id
        payload['status_id'] = status_id
        return ActorStatusCarlaMessage(payload)

    def _finish_current_simulation(self):
        self._manager.environment_handler.destroy()
        self._manager.set_message_handler_state(StartMessageHandlerState)

    def _compute_instruction(self, message: ComputeInstructionOMNeTMessage):
        agent_id = message.payload['agent_id']
        actor_id = message.payload['actor_id']
        status_id = message.payload['status_id']
        status = self.status.pop(status_id)
        agent = self._external_actors[agent_id]
        operator_status, instruction = agent.receive_vehicle_state_info(status,
                                                                        self._tele_world.timestamp.elapsed_seconds)
        payload = dict()
        payload['actor_id'] = actor_id

        simulation_finished = operator_status == TeleOperator.OperatorStatus.FINISHED
        if simulation_finished:
            instruction_id = str(self._do_nothing_id)
            self._finish_current_simulation()
            # self._manager.bui
        elif instruction is None:
            instruction_id = str(self._do_nothing_id)
        else:
            instruction_id = str(next(self._id_iter))
        self.instructions[instruction_id] = instruction
        payload['instruction_id'] = instruction_id

        return InstructionCarlaMessage(payload, simulation_finished)

    def _apply_instruction(self, message: ApplyInstructionOMNeTMessage):
        instruction_id = message.payload['instruction_id']
        actor_id = message.payload['actor_id']
        actor = self._carla_actors[actor_id]
        actor.apply_instruction(self.instructions.pop(instruction_id))
        return OkCarlaMessage(dict())

    def handle_message(self, message: OMNeTMessage):
        if isinstance(message, SimulationStepOMNetMessage):
            return self._simulation_step(message)
        elif isinstance(message, ActorStatusOMNetMessage):
            return self._actor_status(message)
        elif isinstance(message, ComputeInstructionOMNeTMessage):
            return self._compute_instruction(message)
        elif isinstance(message, ApplyInstructionOMNeTMessage):
            return self._apply_instruction(message)
        else:
            return super().handle_message(message)

    def timeout(self):
        self._finish_current_simulation()


#  Socket to talk to server
if __name__ == '__main__':
    TeleConfiguration('configuration/server/ubiquity.yaml')
    manager = CarlaOMNeTManager('tcp', 5555, 1, 1)
    manager.start_simulation()
