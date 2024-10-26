import carla
import numpy as np
import pygame
from carla import ColorConverter as cc
import sys, os
import weakref

from pycarlanet import CarlaClient
from pycarlanet.utils import InstanceExist


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Actor.Sensors.TeleCarlaSensor import TeleCarlaRenderingSensor


class TeleCarlaCameraSensor(TeleCarlaRenderingSensor):

    def __init__(self, parent_actor, gamma_correction=2.2):
        self.display = None
        self._gamma_correction = gamma_correction
        self.sensor = None
        self.surface = None
        self._output_path = None
        self.image = None
        self._attach_to_actor(parent_actor=parent_actor)

    def add_display(self, display, output_path=None):
        self.display = display
        self._output_path = output_path

    @InstanceExist(CarlaClient)
    def _attach_to_actor(self, parent_actor):
        bound_x = 0.5 + parent_actor.bounding_box.extent.x
        bound_y = 0.5 + parent_actor.bounding_box.extent.y
        bound_z = 0.5 + parent_actor.bounding_box.extent.z

        bp_library = CarlaClient.instance.world.get_blueprint_library()
        bp = bp_library.find('sensor.camera.rgb')
        #TODO: fix, calling in __init__ self.diplay is always None
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

        self.sensor = CarlaClient.instance.world.spawn_actor(
            bp,
            carla.Transform(carla.Location(x=-2.0 * bound_x, y=+0.0 * bound_y, z=2.0 * bound_z), carla.Rotation(pitch=8.0)),
            attach_to=parent_actor,
            attachment_type=carla.AttachmentType.SpringArm
        )

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
        print('camera_sensor callback')
        self = weak_self()
        if not self or (self.image is not None and image.frame < self.image.frame):
            return
        self.image = image
        image.convert(cc.Raw)
        if self.display:
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self._output_path is not None:
            image.save_to_disk(f'{self._output_path}{image.frame}')
