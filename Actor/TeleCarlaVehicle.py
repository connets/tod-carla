from pycarlanet.utils import InstanceExist, ObjectStorage
from pycarlanet import CarlanetActor, CarlaClient
import carla

import sys,os
import numpy as np


#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.TeleVehicleControl import TeleVehicleControl
from utils.TeleVehicleState import TeleVehicleState, OtherVehicleState
import utils.LidarUtility as LidarUtility

from Actor.Sensors.TeleCarlaCameraSensor import TeleCarlaCameraSensor
from Actor.Sensors.TeleCarlaLidarSensor import TeleCarlaLidarSensor
from Actor.Mixin import CooperativeUpdateMixin

import lib.camera_visibility.carla_vehicle_annotator as cva

class TeleCarlaVehicle(CarlanetActor, CooperativeUpdateMixin):

    def __init__(self, carla_actor: carla.Actor, actor_type: str):
        super().__init__(carla_actor, actor_type)
        self.sensors = []
        self._last_control = None
        self.hero = False

        self.othersStates = {}
    
    def get_sensor_by_class(self, cls):
        return [s for s in self.sensors if isinstance(s, cls)][0]

    def get_all_sensors_by_class(self, cls):
        return [s for s in self.sensors if isinstance(s, cls)]

    def attach_sensor(self, tele_carla_sensor):
        #self.sensors.add(tele_carla_sensor)
        #print(f"Attaching sensor {tele_carla_sensor} to  {self.carla_actor.id}")
        self.sensors.append(tele_carla_sensor)



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

        def get_visible_obstacles(obstacles, max_distance=20.0):
            visible_obstacles = []
            vehicle_position = self.carla_actor.get_transform().location

            visible_obstacles = [obstacle for obstacle in obstacles if vehicle_position.distance(obstacle.get_transform().location) <= max_distance]
            #if self.hero:
            #    lidar_sensor = self.get_sensor_by_class(TeleCarlaLidarSensor)
            #    visible_obstacles = [obj for obj in visible_obstacles if obj.id in lidar_sensor.get_detected_objects()]

            lidar_detected_objects = set()
            for lidar_sensor in self.get_all_sensors_by_class(TeleCarlaLidarSensor):
                lidar_detected_objects.update(lidar_sensor.get_detected_objects())

            visible_obstacles = [obj for obj in visible_obstacles if obj.id in lidar_detected_objects]

            #error position based on GNSS + RTK N(0, 0.02)
            #error position based on LIDAR N(0, 0.02)
            #error orientation based on commercial IMU sensors
            #Pitch:  N(0, 0.02)
            #Roll:  N(0, 0.02)
            #Yaw: N(0, 0.5)
            #error velocity using high end radar sensor N(0, 0.2)

            for i, v in enumerate(visible_obstacles):
                # Simulate errors for each coordinate (x, y) using a Normal distribution
                v = OtherVehicleState.generate_visible_vehicle(0, v)
                gnss_error = np.random.normal(0, 0.02, 2)
                lidar_error = np.random.normal(0, 0.02, 2)
                pitch_error = np.random.normal(0, 0.02, 1)
                roll_error = np.random.normal(0, 0.02, 1)
                yaw_error = np.random.normal(0, 0.5, 1)
                radar_error = np.random.normal(0, 0.2, 3)
                
                t = v.get_transform()
                
                loc = carla.Location(
                    x=t.location.x + gnss_error[0] + lidar_error[0],
                    y=t.location.y + gnss_error[1] + lidar_error[1],
                    z=t.location.z
                )

                rot = carla.Rotation(
                    pitch=t.rotation.pitch + pitch_error[0],
                    yaw=t.rotation.yaw + yaw_error[0],
                    roll=t.rotation.roll + roll_error[0]
                )

                v.velocity.x += radar_error[0]
                v.velocity.y += radar_error[1]
                v.velocity.z += radar_error[2]

                v.transform = carla.Transform(loc, rot)
                visible_obstacles[i] = v

            return visible_obstacles
        
        def generate_union(obstacles, otherObjects, otherTimestamp):
            ids = [o.id for o in obstacles]
            tMine = CarlaClient.instance.world.get_snapshot().timestamp
            for obj in otherObjects:
                #check if the object is already in the list or is the same vehicle
                if obj.id == self.carla_actor.id or obj.id in ids: continue
                #calculate new position based on velocity vector?
                deltaSeconds = tMine.elapsed_seconds - otherTimestamp.elapsed_seconds
                obj.timestamp = tMine
                obj.transform.location = carla.Location(
                    x=obj.transform.location.x + obj.velocity.x * deltaSeconds,
                    y=obj.transform.location.y + obj.velocity.y * deltaSeconds,
                    z=obj.transform.location.z + obj.velocity.z * deltaSeconds
                )
                obstacles.append(obj)

            return obstacles


        allVehicles = [v for v in CarlaClient.instance.world.get_actors().filter('vehicle.*') if v.id != self.carla_actor.id]
        allPedestrian = CarlaClient.instance.world.get_actors().filter('*walker.pedestrian.*')



        visible_vehicles = get_visible_obstacles(allVehicles)
        visible_pedestrians = get_visible_obstacles(allPedestrian)

        for _,state in self.othersStates.items():
            #check who is the generator and decide to add or not, and where Vehicle or pedestrian?
            #trust generator position instead of my calculation of it?
            generator = CarlaClient.instance.world.get_actor(state.id)
            if generator.type_id.startswith('vehicle'):
                visible_vehicles = generate_union(visible_vehicles, [generator], state.timestamp)
            elif generator.type_id.startswith('walker.pedestrian'):
                visible_pedestrians = generate_union(visible_pedestrians, [generator], state.timestamp)
            #add other visible vehicles
            visible_vehicles = generate_union(visible_vehicles, state.visible_vehicles, state.timestamp)
            visible_pedestrians = generate_union(visible_pedestrians, state.visible_pedestrians, state.timestamp)

        #visible_vehicles, visible_pedestrians = [], []
        #camera_sensor = self.get_sensor_by_class(TeleCarlaCameraSensor)
        #lidar_sensor = self.get_sensor_by_class(TeleCarlaLidarSensor)
        #lidar_image = lidar_sensor.image if lidar_sensor is not None else None
        # if lidar_image and camera_sensor:
        #     # get all vehicles in the world
        #     vehicles_raw = [v for v in CarlaClient.instance.world.get_actors().filter('vehicle.*') if
        #                     v.id != self.carla_actor.id]
        #     # does it need snap_processing filter?
        #     # vehicles = cva.snap_processing(vehicles_raw, snap)
        #     if vehicles_raw:
        #         vehicles_res, _ = cva.auto_annotate_lidar(vehicles_raw, camera_sensor.sensor, lidar_image)
        #         visible_vehicles = vehicles_res['vehicles']
            
        #     pedestrian_raw = CarlaClient.instance.world.get_actors().filter('*walker.pedestrian.*')
        #     #print(f"all pedestrian detected {pedestrian_raw}")
        #     if pedestrian_raw:
        #         pedestrians_res, _ = cva.auto_annotate_lidar(pedestrian_raw, camera_sensor.sensor, lidar_image)
        #         visible_pedestrians = pedestrians_res['vehicles']
        #         #print(f"cva.auto_annotate_lidar {len(visible_pedestrians)}")
        # if len(visible_pedestrians) != 0:
        #     print(f"{self._carla_actor.type_id}: visible_pedestrians {len(visible_pedestrians)}")



        #add to visible_vehicles, visible_pedestrians actors received from coop_message
        #for each actor if i can see it do not consider it
        #project in all directions using the velocity and difference between coop_message timestamp and actual timestamp?
        return TeleVehicleState.generate_vehicle_state(CarlaClient.instance.world.get_snapshot().timestamp, self, visible_vehicles, visible_pedestrians)
    
    def done(self, timestamp):
        return all(sensor.done(timestamp) for sensor in self.sensors)
    
    def handle_cooperative_update(self, status_id):
        #print("handle_cooperative_update")
        state = ObjectStorage.get(status_id)
        #my state, do nothing
        if state.id == self.carla_actor.id:
            return
        
        print(f"received coop {status_id}")

        if len(state.visible_pedestrians) != 0:
            print(f"{self._carla_actor.type_id} handle_cooperative_update visible_pedestrians {len(state.visible_pedestrians)}")
        
        if state.id not in self.othersStates:
            self.othersStates[state.id] = state
            return
        
        if state.timestamp.elapsed_seconds > self.othersStates[state.id].timestamp.elapsed_seconds:
            self.othersStates[state.id] = state
            return




        
        #print(f"handle_cooperative_update {len(state.visible_pedestrians)}")
        #what if a message is older than tot (ex 60) seconds? it make sense to use the information to augment 3d perception?

        #check the timestamp to keep only last state, if receive a message older that last one 
        #add visible obstacle to my obj temp
        #add in some way in next generate_status function


