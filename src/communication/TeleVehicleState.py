import re

from carla import Vector3D, Transform, Location, Rotation, BoundingBox


class ActorState:
    def __init__(self, timestamp, _id, transform, bounding_box):
        self.timestamp = timestamp
        self.id = _id
        self.transform = transform
        self.bounding_box = bounding_box

    def __getattr__(self, method_name, *args):
        m = re.match(r'get_(.*)', method_name)
        if m:
            name = m.group(1)
            return lambda: getattr(self, name)
        return super(self.__class__, self).__getattribute__(method_name, *args)

    def get_location(self):
        return self.transform.location

    def update_state(self, new_state):
        assert isinstance(new_state, self.__class__)
        for name, value in new_state.__dict__.items():
            if value is not None:
                setattr(self, name, value)


class OtherVehicleState(ActorState):
    def __init__(self, timestamp, _id, transform, bounding_box, velocity):
        super().__init__(timestamp, _id, transform, bounding_box)
        self.velocity = velocity


    @staticmethod
    def generate_visible_vehicle(timestamp, vehicle):
        return OtherVehicleState(timestamp, vehicle.id, vehicle.get_transform(),
                                 vehicle.bounding_box, vehicle.get_velocity())


class OtherPedestrianState(ActorState):
    @staticmethod
    def generate_visible_pedestrian(timestamp, pedestrian):
        return OtherPedestrianState(timestamp, pedestrian.id, pedestrian.get_transform(),
                                    pedestrian.bounding_box)


class TeleVehicleState(ActorState):

    def __init__(self, timestamp, _id, bounding_box, velocity, transform, speed_limit, acceleration, visible_vehicles,
                 visible_pedestrians):
        super().__init__(timestamp, _id, transform, bounding_box)
        self.velocity = velocity
        self.transform = transform
        self.speed_limit = speed_limit
        self.acceleration = acceleration
        self.collisions = []
        self.visible_vehicles = visible_vehicles
        self.visible_pedestrians = visible_pedestrians

    @staticmethod
    def generate_vehicle_state(timestamp, vehicle, visible_vehicles, visible_pedestrians):
        vehicle_state = TeleVehicleState(timestamp, vehicle.id, vehicle.bounding_box,
                                         vehicle.get_velocity(), vehicle.get_transform(),
                                         vehicle.get_speed_limit(), vehicle.get_acceleration(),
                                         [OtherVehicleState.generate_visible_vehicle(timestamp, v) for v in
                                          visible_vehicles],
                                         [OtherPedestrianState.generate_visible_pedestrian(timestamp, p) for p in
                                          visible_pedestrians])
        for sensor in vehicle.sensors:
            sensor.attach_data(vehicle_state)

        return vehicle_state


    def __getstate__(self):
        return {
            'id': self.id,
            'velocity_x': self.velocity.x,
            'velocity_y': self.velocity.y,
            'velocity_z': self.velocity.z,
            'transform_location_x': self.transform.location.x,
            'transform_location_y': self.transform.location.y,
            'transform_location_z': self.transform.location.z,
            'transform_rotation_pitch': self.transform.rotation.pitch,
            'transform_rotation_yaw': self.transform.rotation.yaw,
            'transform_rotation_roll': self.transform.rotation.roll,
            'speed_limit': self.speed_limit,

            'bounding_box_extent_x': self.bounding_box.extent.x,
            'bounding_box_extent_y': self.bounding_box.extent.y,
            'bounding_box_extent_z': self.bounding_box.extent.z,
            'bounding_box_location_x': self.bounding_box.location.x,
            'bounding_box_location_y': self.bounding_box.location.y,
            'bounding_box_location_z': self.bounding_box.location.z,
            'bounding_box_location_pitch': self.bounding_box.rotation.pitch,
            'bounding_box_location_yaw': self.bounding_box.rotation.yaw,
            'bounding_box_location_roll': self.bounding_box.rotation.roll,
        }

    def __setstate__(self, state):
        self.id = state['id']
        self.velocity = Vector3D(state['velocity_x'], state['velocity_y'], state['velocity_z'])
        self.transform = Transform(
            Location(state['transform_location_x'], state['transform_location_y'], state['transform_location_z']),
            Rotation(state['transform_rotation_pitch'], state['transform_rotation_yaw'],
                     state['transform_rotation_roll']))
        self.speed_limit = state['speed_limit']
        self.bounding_box = BoundingBox(
            Location(state['bounding_box_location_x'], state['bounding_box_location_y'],
                     state['bounding_box_location_z']),
            Vector3D(state['bounding_box_extent_x'], state['bounding_box_extent_y'], state['bounding_box_extent_z']))
        self.collisions = []  # TODO change for (un)marshalling of the object
