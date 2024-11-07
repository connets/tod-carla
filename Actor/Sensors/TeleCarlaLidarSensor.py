import carla
import sys, os
import weakref

from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Actor.Sensors.TeleCarlaSensor import TeleCarlaRenderingSensor
import utils.LidarUtility as LidarUtility

class TeleCarlaLidarSensor(TeleCarlaRenderingSensor):

    def __init__(self, parent_actor, position: LidarUtility.SensorPosition):
        print(f"generate lidar to position {position.name}")
        self.sensor = None
        self.image = None
        self._attach_to_actor(parent_actor=parent_actor, location=LidarUtility.getCarlaRelativeLocation(parent_actor.bounding_box, position))

    @InstanceExist(CarlaClient)
    def _attach_to_actor(self, parent_actor, location: carla.Location):
        #bound_x = 0.5 + parent_actor.bounding_box.extent.x
        #bound_y = 0.5 + parent_actor.bounding_box.extent.y
        #bound_z = 0.5 + parent_actor.bounding_box.extent.z

        bp_library = CarlaClient.instance.world.get_blueprint_library()
        lidar_bp = bp_library.find('sensor.lidar.ray_cast_semantic')
        # lidar_bp.set_attribute('sensor_tick', '1.0')
        lidar_bp.set_attribute('channels', '64')
        lidar_bp.set_attribute('points_per_second', '1120000')
        lidar_bp.set_attribute('upper_fov', '40')
        lidar_bp.set_attribute('lower_fov', '-40')
        lidar_bp.set_attribute('range', '100')
        lidar_bp.set_attribute('rotation_frequency', '100') #original 20, 100 with fix_time_delta 0.01 => 360 each timestep
        lidar_transform = carla.Transform(location)

        self.sensor = CarlaClient.instance.world.spawn_actor(
            lidar_bp,
            lidar_transform,
            attach_to=parent_actor
        )

        # # Define the location relative to the vehicle
        # vehicle_transform = parent_actor.get_transform()
        # offset = carla.Location(x=0, y=0, z=2)  # 2 meter above the vehicle
        # marker_location = vehicle_transform.location + offset
        # # Define the marker's blueprint (using a simple box for demonstration)
        # marker_bp = CarlaClient.instance.world.get_blueprint_library().find('static.prop.box')
        # # Spawn the marker at the calculated location
        # marker = CarlaClient.instance.world.spawn_actor(marker_bp, marker_location, vehicle_transform.rotation)
        # # Attach the marker directly to the vehicle
        # marker.attach_to(parent_actor)


        # print("====>", self.sensor)>
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: TeleCarlaLidarSensor._parse_image(weak_self, image))

    def destroy(self):
        self.sensor.destroy()

    # def done(self, timestamp):
    #     return self.image is not None and self.image.frame == timestamp.frame

    """
    This method causes the simulator to misbehave with rendering option, because this method is on another thread,
    so the main thread doesn't wait this one to complete, and it could happen that finishes before that the last frame 
    is rendered. if the option to save the image is enabled is also slower, maybe because it's an hard operation and cpu is full. 
    """

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if self.image is None or self.image.frame < image.frame:
            #image.save_to_disk("/home/stefano/Documents/tesi/plyVisualizer/output")
            self.image = image

    def done(self, timestamp):
        return self.image is None or self.image.frame == timestamp.frame


    def render(self):
        pass

    def get_detected_objects(self):
        if self.image is None: return set()
        return set([obj.object_idx for obj in self.image])
        #objs = [LidarUtility.Semantic_types[t.object_tag] for t in lidar_image if t.object_tag>=12 and t.object_tag<=19 ]
