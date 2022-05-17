import time

from src.TeleOutputWriter import DataCollector
from src.actor.TeleActor import TeleActor


class PeriodicDataCollectorActor(TeleActor):
    def __init__(self, file_path, items: dict, writing_interval):
        super().__init__()
        self._data_collector = DataCollector(file_path)
        self._items = items
        self._writing_interval = writing_interval
        self._data_collector.write(*(key for key in self._items.keys()))
        self._last_rows = None

    def run(self):
        def daemon_write():
            current_rows = [func() for func in self._items.values()]
            if self._last_rows != current_rows:
                self._data_collector.write(*current_rows)
                self._last_rows = current_rows
            self._tele_context.schedule(daemon_write, self._writing_interval)

        daemon_write()


class InfoSpeedSimulationActor(TeleActor):
    def __init__(self, writing_interval: float):
        super().__init__()
        self._writing_interval = writing_interval
        self._begin_time = time.time()

    def run(self):
        def print_simulation_state():
            current_real_time = time.time()
            total_elapsed_time = round(current_real_time - self._begin_time, 2)
            simulation_duration = self._tele_context.current_duration()
            whole_speed = round(simulation_duration / total_elapsed_time, 2)
            print(f'simulation speed ratio: {whole_speed}x')
            self._tele_context.schedule(print_simulation_state, self._writing_interval)

        print_simulation_state()
