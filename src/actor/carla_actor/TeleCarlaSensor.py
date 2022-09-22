import abc
import collections
import math
import weakref
from abc import ABC, abstractmethod

import carla
import numpy as np
import pygame
from carla import ColorConverter as cc

from src.utils.carla_utils import get_actor_display_name


class TeleCarlaSensor(ABC):

    def stop(self):
        ...

    @abstractmethod
    def destroy(self):
        ...

    def attach_to_actor(self, tele_world, parent_actor):
        ...

    def attach_data(self, vehicle_state):
        ...

    def done(self, timestamp):
        return True


class TeleCarlaRenderingSensor(TeleCarlaSensor):
    @abstractmethod
    def render(self):
        ...


class TeleCarlaCameraSensor(TeleCarlaRenderingSensor):

    def __init__(self, gamma_correction):
        self.display = None
        self._tele_world = None
        self._gamma_correction = gamma_correction
        self.sensor = None
        self.surface = None
        self._output_path = None
        self.parent_actor = None
        self.image = None

    def add_display(self, display, output_path=None):
        self.display = display
        self._output_path = output_path

    def attach_to_actor(self, tele_world, parent_actor):
        self._tele_world = tele_world
        self.parent_actor = parent_actor
        bound_x = 0.5 + parent_actor.bounding_box.extent.x
        bound_y = 0.5 + parent_actor.bounding_box.extent.y
        bound_z = 0.5 + parent_actor.bounding_box.extent.z

        bp_library = parent_actor.get_world().get_blueprint_library()
        bp = bp_library.find('sensor.camera.rgb')
        if self.display is not None:
            bp.set_attribute('image_size_x', str(self.display.get_width()))
            bp.set_attribute('image_size_y', str(self.display.get_height()))

        # bp.set_attribute('image_size_x', str(hud.dim[0]))
        # bp.set_attribute('image_size_y', str(hud.dim[1]))
        if bp.has_attribute('gamma'):
            bp.set_attribute('gamma', str(self._gamma_correction))
        # attributes
        # for attr_name, attr_value in item[3].items():
        #     bp.set_attribute(attr_name, attr_value)

        self.sensor = self.parent_actor.get_world().spawn_actor(
            bp,
            carla.Transform(carla.Location(x=-2.0 * bound_x, y=+0.0 * bound_y, z=2.0 * bound_z),
                            carla.Rotation(pitch=8.0)),
            attach_to=self.parent_actor.model,
            attachment_type=carla.AttachmentType.SpringArm)

        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: TeleCarlaCameraSensor._parse_image(weak_self, image))

    def render(self):
        """Render method"""
        if self.surface is not None:
            self.display.blit(self.surface, (0, 0))
            self.surface = None

    def destroy(self):
        self.sensor.destroy()

    def done(self, timestamp):
        return self.image is None or self.image.frame == timestamp.frame

    """
    This method causes the simulator to misbehave with rendering option, because this method is on another thread,
    so the main thread doesn't wait this one to complete, and it could happen that finishes before that the last frame 
    is rendered. if the option to save the image is enabled is also slower, maybe because it's an hard operation and cpu is full. 
    """

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self or (self.image is not None and image.frame < self.image.frame):
            return
        self.image = image
        if self.display:
            image.convert(cc.Raw)
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
            if self._output_path is not None:
                image.save_to_disk(f'{self._output_path}{image.frame}')

def draw_image(surface, image, blend=False):
    array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    array = np.reshape(array, (image.height, image.width, 4))
    array = array[:, :, :3]
    array = array[:, :, ::-1]
    image_surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
    if blend:
        image_surface.set_alpha(100)
    surface.blit(image_surface, (0, 0))
class TeleCarlaLidarSensor(TeleCarlaRenderingSensor):

    def __init__(self):
        self._tele_world = None
        self.sensor = None
        self.parent_actor = None
        self.image = None

    def attach_to_actor(self, tele_world, parent_actor):
        self._tele_world = tele_world
        self.parent_actor = parent_actor
        bound_x = 0.5 + parent_actor.bounding_box.extent.x
        bound_y = 0.5 + parent_actor.bounding_box.extent.y
        bound_z = 0.5 + parent_actor.bounding_box.extent.z

        bp_library = parent_actor.get_world().get_blueprint_library()
        lidar_bp = bp_library.find('sensor.lidar.ray_cast_semantic')
        # lidar_bp.set_attribute('sensor_tick', '1.0')
        lidar_bp.set_attribute('channels', '64')
        lidar_bp.set_attribute('points_per_second', '1120000')
        lidar_bp.set_attribute('upper_fov', '40')
        lidar_bp.set_attribute('lower_fov', '-40')
        lidar_bp.set_attribute('range', '100')
        lidar_bp.set_attribute('rotation_frequency', '20')
        lidar_transform = carla.Transform(carla.Location(x=-2.0 * bound_x, y=+0.0 * bound_y, z=2.0 * bound_z),
                                          carla.Rotation(pitch=8.0))
        self.sensor = self.parent_actor.get_world().spawn_actor(lidar_bp, lidar_transform,
                                                                attach_to=self.parent_actor.model)

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
            self.image = image

    def done(self, timestamp):
        return self.image is None or self.image.frame == timestamp.frame


    def render(self):
        pass


class TeleCarlaCollisionSensor(TeleCarlaSensor):
    """ Class for collision sensors"""

    def __init__(self):
        self._parent = None
        self.sensor = None
        self.history = []

    def attach_to_actor(self, tele_world, parent_actor):
        """Constructor method"""
        self._parent = parent_actor
        world = self._parent.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self._parent.model)
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: self._on_collision(weak_self, event))

    def get_collision_history(self):
        """Gets the history of collisions"""
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        """On collision method"""
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        print("**** ACCIDENT ****", actor_type)
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)

    def destroy(self):
        self.sensor.destroy()

    def attach_data(self, vehicle_state):
        vehicle_state.collisions = self.history


class TeleCarlaGnssSensor(TeleCarlaSensor):

    def __init__(self):
        self.sensor = None
        self._parent = None
        self.altitude = 0.0
        self.latitude = 0.0
        self.longitude = 0.0

    def spawn_in_world(self, parent_actor):
        self._parent = parent_actor
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent.model)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: TeleCarlaGnssSensor._on_gnss_event(weak_self, event))

    def stop(self):
        self.sensor.stop()

    def destroy(self):
        self.sensor.destroy()
        self.sensor = None
        self.index = None

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.altitude = event.altitude
        self.latitude = event.latitude
        self.longitude = event.longitude
        # print("**** =", self.lat, self.lon)
