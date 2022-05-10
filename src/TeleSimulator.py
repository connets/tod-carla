import threading


class TeleSimulator:
    def __init__(self, tele_world, tele_context, clock):
        self._tele_world = tele_world
        self._tele_context = tele_context
        self._clock = clock
        self._step_callbacks = set()
        self._nodes = set()

    @property
    def tele_world(self):
        return self._tele_world

    def add_network_node(self, *network_nodes):
        self._nodes.update(network_nodes)

    def add_tick_listener(self, callback):
        self._tele_world.add_tick_listener(callback)

    def add_step_listener(self, callback):
        self._step_callbacks.add(callback)

    def start(self):
        for actor in self._nodes:
            actor.set_context(self._tele_context)
            actor.start(self._tele_world)

    def do_simulation(self, sync):
        if sync:
            self._do_sync_simulation()
        else:
            self._do_async_simulation()

    def _do_sync_simulation(self):
        finish = False

        while not finish:
            # network_delay.tick()
            simulator_timestamp = round(self._tele_context.timestamp, 6)
            while not finish and simulator_timestamp > self._tele_world.timestamp.elapsed_seconds:
                self._clock.tick()
                self._tele_world.tick(self._clock)

            for callback in self._step_callbacks: callback()

            self._tele_context.run_next_event()

            # data_collector.tick()
            # print(sim_world.get_snapshot().timestamp)

        return

    def _do_async_simulation(self):
        finish = False

        while not finish:
            simulator_timestamp = round(self._tele_context.timestamp, 6)
            self._clock.tick()
            self._tele_world.tick(self._clock)

            for callback in self._step_callbacks: callback()

            while self._tele_world.timestamp.elapsed_seconds > self._tele_context.next_timestamp_event():
                self._tele_context.run_next_event()
