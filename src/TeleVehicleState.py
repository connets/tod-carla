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
