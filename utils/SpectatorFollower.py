import carla


class SpectatorFollower:
    """Chase camera: keeps the CARLA spectator behind an actor, looking slightly down at it."""

    def __init__(self, actor_id, distance=8.0, height=4.0, pitch=-12.0):
        self.actor_id = actor_id
        self._distance = distance
        self._height = height
        self._pitch = pitch
        self._attached_logged = False
        self._error_logged = False

    @classmethod
    def from_config(cls, spectator_conf):
        """Builds the follower from the 'spectator' block of the yaml ('follow' + optional offsets)."""
        return cls(spectator_conf['follow'],
                   spectator_conf.get('follow_distance', 8.0),
                   spectator_conf.get('follow_height', 4.0),
                   spectator_conf.get('follow_pitch', -12.0))

    def update(self, world, find_actor):
        """
        Moves the spectator behind the actor returned by find_actor(actor_id). Errors are
        only reported once: the actor may not exist yet in the first ticks, and the camera
        must never stop the simulation.
        """
        try:
            transform = find_actor(self.actor_id).carla_actor.get_transform()
            forward = transform.get_forward_vector()
            world.get_spectator().set_transform(carla.Transform(
                carla.Location(x=transform.location.x - self._distance * forward.x,
                               y=transform.location.y - self._distance * forward.y,
                               z=transform.location.z + self._height),
                carla.Rotation(pitch=self._pitch, yaw=transform.rotation.yaw)))
            if not self._attached_logged:
                print(f"[follow] spettatore agganciato a {self.actor_id}")
                self._attached_logged = True
        except Exception as e:
            if not self._error_logged:
                print(f"[follow] errore: {e!r}")
                self._error_logged = True
