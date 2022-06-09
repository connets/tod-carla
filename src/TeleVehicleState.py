from carla import Vector3D, Transform, Location, Rotation, BoundingBox


class OtherActorState:
    def __init__(self, _id, transform, bounding_box):
        self.id = _id
        self.transform = transform
        self.bounding_box = bounding_box

    def get_location(self):
        return self.transform.location

    def get_transform(self):
        return self.transform

    def update_state(self, actor_state):
        assert isinstance(actor_state, self.__class__)


class OtherVehicleState(OtherActorState):
    def __init__(self, _id, transform, bounding_box, velocity):
        super().__init__(_id, transform, bounding_box)
        self.velocity = velocity

    def get_velocity(self):
        return self.velocity

    @staticmethod
    def generate_visible_vehicle(vehicle):
        return OtherVehicleState(vehicle.id, vehicle.get_transform(),
                                 vehicle.bounding_box, vehicle.get_velocity())


class OtherPedestrianState(OtherActorState):
    @staticmethod
    def generate_visible_pedestrian(pedestrian):
        return OtherPedestrianState(pedestrian.id, pedestrian.get_transform(),
                                    pedestrian.bounding_box)


class TeleVehicleState:

    def __init__(self, timestamp, _id, velocity, transform, speed_limit, bounding_box, visible_vehicles,
                 visible_pedestrians):
        self.timestamp = timestamp
        self.id = _id
        self.velocity = velocity
        self.transform = transform
        self.speed_limit = speed_limit
        self.bounding_box = bounding_box
        self.collisions = []
        self.visible_vehicles = visible_vehicles
        self.visible_pedestrians = visible_pedestrians

    @staticmethod
    def generate_vehicle_state(timestamp, vehicle, visible_vehicles, visible_pedestrians):
        vehicle_state = TeleVehicleState(timestamp, vehicle.id, vehicle.get_velocity(), vehicle.get_transform(),
                                         vehicle.get_speed_limit(),
                                         vehicle.bounding_box,
                                         [OtherVehicleState.generate_visible_vehicle(v) for v in
                                          visible_vehicles],
                                         [OtherPedestrianState.generate_visible_pedestrian(p) for p in
                                          visible_pedestrians])
        for sensor in vehicle.sensors:
            sensor.attach_data(vehicle_state)

        return vehicle_state

    def get_location(self):
        return self.transform.location

    def get_velocity(self):
        return self.velocity

    def get_transform(self):
        return self.transform

    def get_speed_limit(self):
        return self.speed_limit

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
