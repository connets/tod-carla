#TODO: FIX IT

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
