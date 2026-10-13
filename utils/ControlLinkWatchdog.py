class ControlLinkWatchdog:
    """
    Dead-man's switch of the teleoperated vehicles.

    The loss_ratio threshold only covers partial loss, when instructions still
    arrive. If the control channel goes silent, CARLA would keep applying the last
    instruction received: after control_timeout seconds without instructions the
    vehicle performs the minimum risk maneuver on its own, re-applied at every step
    until an instruction arrives again.
    """

    def __init__(self):
        self._last_instruction_time = dict()
        self._link_lost = dict()

    def is_link_lost(self, actor_id):
        return bool(self._link_lost.get(actor_id, False))

    def rearm(self, actor_id, now):
        """An instruction was applied at simulated time now: the teleoperator is alive."""
        self._last_instruction_time[actor_id] = now
        if self._link_lost.pop(actor_id, False):
            print(f"[dead-man] {actor_id}: canale di controllo ripristinato a t={now:.3f}s")

    def check(self, actor_id, actor, controller, now):
        """Applies the minimum risk maneuver to the actor if its control link is silent."""
        # silence is counted from the first check until the first instruction arrives
        last = self._last_instruction_time.setdefault(actor_id, now)
        silence = now - last
        if silence < controller.control_timeout:
            return

        if not self._link_lost.get(actor_id, False):
            self._link_lost[actor_id] = True
            print(f"[dead-man] {actor_id}: nessuna istruzione da {silence:.3f}s "
                  f"a t={now:.3f}s -> manovra a rischio minimo")

        instruction = controller.minimum_risk_maneuver()
        if instruction is not None:
            actor.apply_instruction(instruction)
