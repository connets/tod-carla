import itertools
import traceback

import zmq
from carla.libcarla import World
from pycarlanet import CarlanetManager, CarlanetEventListener, SimulatorStatus, CarlanetActor
from src.EnvironmentHandler import EnvironmentHandler, CarlaTimeoutError
from src.utils import bcolors


class CarlaOmnetError(RuntimeError):
    ...


class CarlaOmnetCommunicationError(CarlaOmnetError):
    ...


class UnknownMessageCarlaOmnetError(RuntimeError):
    def __init__(self, unknown_msg):
        self.unknown_msg = unknown_msg

    def __repr__(self) -> str:
        return "I don't know how to handle the following msg: " + self.unknown_msg


class CarlaOMNeTManager(CarlanetEventListener):
    _id_iter = itertools.count(1000)

    def __init__(self, protocol, port, connection_timeout, data_transfer_timeout):
        self._external_active_actors = None
        self._tele_world = None
        self._carla_actors = None
        self._protocol = protocol
        self._port = port
        self._carlanet_manager = CarlanetManager(port, self)#, log_messages=True)  # , socket_options={zmq.RCVTIMEO: connection_timeout*1000,
        # zmq.SNDTIMEO: connection_timeout*1000})
        self.environment_handler: EnvironmentHandler = EnvironmentHandler()
        self.timestamp = 0
        self._do_nothing_id = -1

        self.status = dict()
        self.instructions = dict()

        self.running = False

    # NOTE: It's not possibile to launch different simulations with different instances of carla_simulator,
    # I've tried to relaunch every times a different instance of carla-simulator to avoid crashes,
    # but a tcp connection remains always active  (https://github.com/carla-simulator/carla/issues/3212)
    # def start_simulation(self):
    #     self._start_server()
    #     self.set_message_handler_state(StartMessageHandlerState)
    #     try:
    #         while not isinstance(self._message_handler_state, FinishMessageHandlerState):
    #             message = self._receive_data_from_omnet()
    #             answer = self._message_handler_state.handle_message(message)
    #             self._send_data_to_omnet(answer)
    #             # print(message, answer, '\n\n')
    #         # except zmq.error.Again:
    #         #     print(f"{bcolors.WARNING}Warning: Exception ZMQ timeout{bcolors.ENDC}")
    #     except Exception as e:
    #         print(traceback.format_exc())
    #         print(f"{bcolors.WARNING}Warning: Exception {e.__class__.__name__} {e} {bcolors.ENDC}")
    #         self._message_handler_state.finish_current_simulation(SimulationStatus.FINISHED_ERROR)
    #     finally:
    #         if self.environment_handler is not None:
    #             self.socket.close()
    #             self.environment_handler.close()
    # self._message_handler_state.timeout()

    def omnet_init_completed(self, run_id, carla_configuration, user_defined) -> (SimulatorStatus, World):
        # self.environment_handler = EnvironmentHandler(carla_configuration, user_defined, run_id)
        self.environment_handler.add_carla_scenario_config(carla_configuration, user_defined, run_id)
        self.environment_handler.build_world()
        self._tele_world = self.environment_handler.tele_world

        initial_timestamp = round(self._tele_world.timestamp.elapsed_seconds, 9)
        self.running = True
        return SimulatorStatus.RUNNING, self._tele_world.sim_world

    def actor_created(self, actor_id: str, actor_type: str, actor_config) -> CarlanetActor:
        carla_actor = self.environment_handler.create_active_actors(actor_id, actor_type, actor_config)

        return CarlanetActor(carla_actor.model, True)

    def carla_init_completed(self):
        self.environment_handler.world_init_completed()
        self._carla_actors = self.environment_handler.carla_actors
        self._external_active_actors = self.environment_handler.external_active_actors
        self._external_passive_actors = self.environment_handler.external_passive_actors

        super().carla_init_completed()

    def carla_simulation_step(self, timestamp) -> SimulatorStatus:
        if timestamp > self.environment_handler.sim_time_limit:
            return SimulatorStatus.FINISHED_TIME_LIMIT

        rounded_timestamp = round(timestamp, 6)
        for actor in self._external_passive_actors:
            actor.tick(rounded_timestamp)
        self.environment_handler.tick()

        # print(','.join(*payload['actors'][0]['position']), ','.join(*payload['actors'][0]['rotation']))
        return SimulatorStatus.RUNNING

    def generic_message(self, timestamp, user_defined_message) -> (SimulatorStatus, dict):

        if timestamp > self.environment_handler.sim_time_limit:
            return SimulatorStatus.FINISHED_TIME_LIMIT, dict()
        user_message_type = user_defined_message['user_message_type']

        if user_message_type == 'ACTOR_STATUS_UPDATE':
            return self._actor_status(user_defined_message)
        elif user_message_type == 'COMPUTE_INSTRUCTION':
            return self._compute_instruction(user_defined_message)
        elif user_message_type == 'APPLY_INSTRUCTION':
            return self._apply_instruction(user_defined_message)
        elif user_message_type == 'FINISH_SIMULATION':
            return SimulatorStatus.FINISHED_OK, dict() # TODO Maybe add a new finish code for this specific case?
        return SimulatorStatus.FINISHED_ERROR, dict()

    def _actor_status(self, user_defined_message):
        while any(not actor.done(self._tele_world.timestamp) for actor in self._carla_actors.values()):
            ...

        actor_id = user_defined_message['actor_id']
        actor_status = self._carla_actors[actor_id].generate_status()
        status_id = str(next(self._id_iter))
        self.status[status_id] = actor_status
        res = dict()
        res['user_message_type'] = 'ACTOR_STATUS'
        res['actor_id'] = actor_id
        res['status_id'] = status_id

        return SimulatorStatus.RUNNING, res

    def _compute_instruction(self, user_defined_message):
        agent_id = user_defined_message['agent_id']
        actor_id = user_defined_message['actor_id']
        status_id = user_defined_message['status_id']
        status = self.status.pop(status_id)
        agent = self._external_active_actors[agent_id]
        simulator_status, instruction = agent.receive_vehicle_state_info(status,
                                                                         self._tele_world.timestamp.elapsed_seconds)
        res = dict()
        res['user_message_type'] = 'INSTRUCTION'
        res['actor_id'] = actor_id

        if simulator_status != SimulatorStatus.RUNNING:
            instruction_id = str(self._do_nothing_id)
            # self.environment_handler.finish_simulation(simulator_status)
            # self._manager.bui
        elif instruction is None:
            instruction_id = str(self._do_nothing_id)
        else:
            instruction_id = status_id
        self.instructions[instruction_id] = instruction
        res['instruction_id'] = instruction_id

        return simulator_status, res

    def _apply_instruction(self, user_defined_message):
        instruction_id = user_defined_message['instruction_id']
        actor_id = user_defined_message['actor_id']
        actor = self._carla_actors[actor_id]
        if instruction_id != str(self._do_nothing_id):
            actor.apply_instruction(self.instructions.pop(instruction_id))

        res = dict()
        res['user_message_type'] = 'OK'

        return SimulatorStatus.RUNNING, res

    def simulation_finished(self, simulator_status):
        self.environment_handler.finish_simulation(simulator_status)

    def simulation_error(self, e):

        print(traceback.format_exc())
        print(f"{bcolors.WARNING}Warning: Exception {e.__class__.__name__} {e} {bcolors.ENDC}")
        if self.running:
            self.environment_handler.close()
            self.environment_handler.finish_simulation(SimulatorStatus.FINISHED_ERROR)

    def start_simulation(self):
        self.environment_handler.launch_carla_server()
        self._carlanet_manager.start_simulation()
