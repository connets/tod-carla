import carla
import sys
import os
import traceback
import yaml

from pycarlanet.listeners import WorldManager, ActorManager
from pycarlanet.enum import SimulatorStatus, CarlaMaplayers
from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist


#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.FolderPath import FolderPath
from utils.CarlaServerHandler import CarlaServerHandler
from utils.InterCommunicationListeners import InterCommunicationListeners
from otherManagers.LoggerManager import LoggerManager
import utils.YAMLLoader as YAMLLoader

class MyWorldManager(WorldManager):
    # Static spectator pose from the yaml, None when the yaml does not set one.
    _spectator = None
    # Follow-cam: actor the spectator is chained to, and how it sits behind it.
    _follow_actor_id = None
    _follow_distance = 8.0
    _follow_height = 4.0
    _follow_pitch = -12.0
    _follow_logged = False
    _follow_err_logged = False

    @InstanceExist(CarlaClient)
    def omnet_init_completed(self, message) -> SimulatorStatus:
        #define folder for results as run_id
        FolderPath.RESULTS_PATH += f"{message['run_id']}/"
        #open user defined configuration file
        data = YAMLLoader.load_and_merge_yaml_file(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml")
        InterCommunicationListeners.instance.askToManager(LoggerManager, 'writeYAMLconfig', data)
        # with open(f"{FolderPath.CONFIGURATION_PATH}{message['user_defined']['config_name']}.yaml", 'r') as file:
        #         #data = json.load(file)
        #         data = yaml.safe_load(file)
        worldName = data['world']
                
        super().omnet_init_completed(message=message)
        super().load_world(worldName=worldName,layer_to_unload=[CarlaMaplayers.Buildings, CarlaMaplayers.ParkedVehicles, CarlaMaplayers.Foliage]) #[x for x in CarlaMaplayers]
        self.tick()

        if 'spectator' in data:
            spectator_conf = data['spectator']
            # 'follow' chains the spectator to an actor instead of pinning it to a
            # fixed pose: useful to actually watch the ego drive a long route.
            if 'follow' in spectator_conf:
                self._follow_actor_id = spectator_conf['follow']
                self._follow_distance = spectator_conf.get('follow_distance', self._follow_distance)
                self._follow_height = spectator_conf.get('follow_height', self._follow_height)
                self._follow_pitch = spectator_conf.get('follow_pitch', self._follow_pitch)
            else:
                self._spectator = carla.Transform(
                    carla.Location(
                        x=spectator_conf['x'],
                        y=spectator_conf['y'],
                        z=spectator_conf['z']
                    ),
                    carla.Rotation(
                        pitch=spectator_conf['pitch'],
                        yaw=spectator_conf['yaw'],
                        roll=spectator_conf['roll']
                    )
                )


        dir_path = os.path.dirname(f'{FolderPath.RESULTS_PATH}recording.log')
        
        # Create the directory if it doesn't exist
        if dir_path and not os.path.exists(dir_path): os.makedirs(dir_path)
        CarlaClient.instance.client.start_recorder(f'{FolderPath.RESULTS_PATH}recording.log')
        #self.world.set_weather(carla.WeatherParameters.ClearNight)
        #self.tick()
        # traffic_manager = CarlaClient.instance.client.get_trafficmanager()
        # traffic_manager.set_synchronous_mode(self._synchronousMode)
        # traffic_manager.set_random_device_seed(message['carla_configuration']['seed'])
        # self.tick()

        self.sim_time_limit = message['carla_configuration']['sim_time_limit'] - 1

        return SimulatorStatus.RUNNING
    
    @InstanceExist(CarlaClient)
    def before_world_tick(self, timestamp):
        if self._follow_actor_id is not None:
            self._update_spectator_follow()
        elif self._spectator:
            # Get the spectator from the world
            spectator = CarlaClient.instance.world.get_spectator()
            # Set the camera view
            spectator.set_transform(self._spectator)

    @InstanceExist(CarlaClient)
    def _update_spectator_follow(self):
        """
        Keeps the spectator a few metres behind the followed actor, looking slightly
        down at it. Guarded because the actor may not be spawned yet during the very
        first ticks, and a failure here must not take the simulation down.
        """
        try:
            actor = InterCommunicationListeners.instance.askToManager(
                ActorManager, 'get_actor_from_id', self._follow_actor_id)
            transform = actor.carla_actor.get_transform()
            forward = transform.get_forward_vector()
            CarlaClient.instance.world.get_spectator().set_transform(carla.Transform(
                carla.Location(x=transform.location.x - self._follow_distance * forward.x,
                               y=transform.location.y - self._follow_distance * forward.y,
                               z=transform.location.z + self._follow_height),
                carla.Rotation(pitch=self._follow_pitch, yaw=transform.rotation.yaw)))
            if not self._follow_logged:
                print(f"[follow] spettatore agganciato a {self._follow_actor_id}")
                self._follow_logged = True
        except Exception as e:
            if not self._follow_err_logged:
                print(f"[follow] errore: {e!r}")
                self._follow_err_logged = True

    def after_world_tick(self, timestamp) -> SimulatorStatus:
        #print(f"{timestamp} of {self.sim_time_limit}")
        #if InterCommunicationListeners.instance.askToManager(ActorManager, 'check_hero_crash'):
        #    return SimulatorStatus.FINISHED_OK
        if InterCommunicationListeners.instance.askToManager(ActorManager, 'check_hero_destination_reached'):
            return SimulatorStatus.FINISHED_OK
        if timestamp > self.sim_time_limit:
            return SimulatorStatus.FINISHED_TIME_LIMIT
        
        return SimulatorStatus.RUNNING

    def generic_message(self, timestamp, message) -> (SimulatorStatus, dict):
        ...

    def simulation_finished(self, status_code):
        InterCommunicationListeners.instance.askToManager(LoggerManager, 'writeFinishStatus', status_code)
        exit()
        #self.writeFinishStatus(status_code)

    def simulation_error(self, e):
        print(traceback.format_exc())
        print(f"Warning: Exception {e.__class__.__name__} {e}")
        CarlaServerHandler.close()
        InterCommunicationListeners.instance.askToManager(LoggerManager, 'writeFinishStatus', SimulatorStatus.FINISHED_ERROR)
        #self.writeFinishStatus(SimulatorStatus.FINISHED_ERROR)

    #def writeFinishStatus(self, status_code: SimulatorStatus):
    #    with open(f'{FolderPath.RESULTS_PATH}/FINISH_STATUS.txt', 'w') as f:
    #        f.write(status_code.name)