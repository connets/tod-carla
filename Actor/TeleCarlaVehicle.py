from pycarlanet.utils import InstanceExist
from pycarlanet import CarlanetActor, CarlaClient
import carla

import sys,os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.TeleVehicleControl import TeleVehicleControl
from utils.TeleVehicleState import TeleVehicleState

from Actor.Sensors.TeleCarlaCameraSensor import TeleCarlaCameraSensor
from Actor.Sensors.TeleCarlaLidarSensor import TeleCarlaLidarSensor

import lib.camera_visibility.carla_vehicle_annotator as cva

class TeleCarlaVehicle(CarlanetActor):
    _last_control = None
    sensors = set()

    def __init__(self, carla_actor: carla.Actor, actor_type: str):
        super().__init__(carla_actor, actor_type)

    
    def get_sensor_by_class(self, cls):
        return next(iter([s for s in self.sensors if isinstance(s, cls)]), None)

    def attach_sensor(self, tele_carla_sensor):
        self.sensors.add(tele_carla_sensor)



    #methods for API calls
    @InstanceExist(CarlaClient)
    def apply_instruction(self, tele_vehicle_control: TeleVehicleControl):
        # execute only if the instruction is newer than the last one, otherwise ignore it beacuse it is outdated caused by network latency
        if self._last_control is None or self._last_control.timestamp.elapsed_seconds < tele_vehicle_control.timestamp.elapsed_seconds:
            self._last_control = tele_vehicle_control
            CarlaClient.instance.client.apply_batch_sync([carla.command.ApplyVehicleControl(
                self.carla_actor.id,
                tele_vehicle_control.vehicle_control
            )])

    @InstanceExist(CarlaClient)
    def generate_status(self):
        #visible_vehicles, visible_pedestrians = [], []
        #return TeleVehicleState.generate_vehicle_state(CarlaClient.instance.world.get_snapshot().timestamp, self, visible_vehicles, visible_pedestrians)
        
        camera_sensor = self.get_sensor_by_class(TeleCarlaCameraSensor)
        lidar_sensor = self.get_sensor_by_class(TeleCarlaLidarSensor)
        
        lidar_image = lidar_sensor.image if lidar_sensor is not None else None
        
        visible_vehicles, visible_pedestrians = [], []

        snapshot = CarlaClient.instance.world.get_snapshot()
        
        if lidar_image and camera_sensor:
            # get all vehicles in the world
            vehicles_raw = [v for v in CarlaClient.instance.world.get_actors().filter('vehicle.*') if
                            v.id != self.carla_actor.id]
            # does it need snap_processing filter?
            # vehicles = cva.snap_processing(vehicles_raw, snap)
            if vehicles_raw:
                vehicles_res, _ = cva.auto_annotate_lidar(vehicles_raw, camera_sensor.sensor, lidar_image)
                visible_vehicles = vehicles_res['vehicles']
            
            pedestrian_raw = CarlaClient.instance.world.get_actors().filter('*walker.pedestrian*')
            if pedestrian_raw:
                pedestrians_res, _ = cva.auto_annotate_lidar(pedestrian_raw, camera_sensor.sensor, lidar_image)
                visible_pedestrians = pedestrians_res['vehicles']
        
        return TeleVehicleState.generate_vehicle_state(snapshot.timestamp, self, visible_vehicles, visible_pedestrians)
    
    def done(self, timestamp):
        return all(sensor.done(timestamp) for sensor in self.sensors)