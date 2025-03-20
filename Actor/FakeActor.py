import carla
import numpy as np

class StaticFakeActor():
    def __init__(self, position: carla.Location = carla.Location(x=0, y=0, z=0)):
        self.id = 0
        self.position = position
        self.bounding_box = carla.BoundingBox(self.position, carla.Vector3D(x=0.2, y=0.2, z=0.2))

    def get_transform(self):
        return carla.Transform(self.position, carla.Rotation(pitch=0, yaw=0, roll=0))
    def get_velocity(self):
        return carla.Vector3D(x=0, y=0, z=0)
    def get_speed_limit(self):
        return 0.0
    def get_acceleration(self):
        return carla.Vector3D(x=0, y=0, z=0)

class MovingFakeActor():
    def __init__(self, position: carla.Location = carla.Location(x=0, y=0, z=0)):
        self.id = 0
        self.position = position
        self.bounding_box = carla.BoundingBox(self.position, carla.Vector3D(x=0.2, y=0.2, z=0.2))

    def get_transform(self):
        x = self.position.x + np.random.normal(0, 0.5, 1)[0]
        y = self.position.y + np.random.normal(0, 0.5, 1)[0]
        z = self.position.z + np.random.normal(0, 0.5, 1)[0]
        self.position = carla.Location(x=x, y=y, z=z)
        return carla.Transform(self.position, carla.Rotation(pitch=0, yaw=0, roll=0))
    def get_velocity(self):
        return carla.Vector3D(x=0, y=0, z=0)
    def get_speed_limit(self):
        return 0.0
    def get_acceleration(self):
        return carla.Vector3D(x=0, y=0, z=0)