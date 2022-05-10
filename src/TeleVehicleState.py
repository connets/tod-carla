from carla import Vector3D, Transform, Location, Rotation, BoundingBox


class TeleVehicleState:
    def __init__(self, _id, velocity, transform, speed_limit, bounding_box):
        self.id = _id
        self.velocity = velocity
        self.transform = transform
        self.speed_limit = speed_limit
        self.bounding_box = bounding_box

    @staticmethod
    def generate_current_state(vehicle):
        print(vehicle.get_transform().location)
        return TeleVehicleState(vehicle.id, vehicle.get_velocity(), vehicle.get_transform(), vehicle.get_speed_limit(),
                                vehicle.bounding_box)

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
