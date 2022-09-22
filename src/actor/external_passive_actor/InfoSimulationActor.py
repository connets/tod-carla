import time

from src.TeleOutputWriter import DataCollector
from src.actor.TeleActor import TeleActor
from src.actor.external_passive_actor.ExternalPassiveActor import ExternalPassiveActor
from src.utils.decorators import preconditions


class PeriodicDataCollectorActor(ExternalPassiveActor):
    def __init__(self, writing_interval: float, file_path, items: dict):
        super().__init__(writing_interval)
        self._data_collector = DataCollector(file_path)
        self._items = items
        self._data_collector.write(*(key for key in self._items.keys()))


    def do_action(self):
        # @tele_event('writing_out', log=False)
        current_rows = [func() for func in self._items.values()]
        # if self._last_rows != current_rows:
        self._data_collector.write(*current_rows)


class SimulationRatioActor(ExternalPassiveActor):
    def __init__(self, writing_interval: float, file_path, timestamp_func):
        super().__init__(writing_interval)
        self._data_collector = DataCollector(file_path)
        self._data_collector.write('timestamp')
        self._timestamp_func = timestamp_func
        self._begin_time = None


    def do_action(self):
        if self._begin_time is None:
            self._begin_time = time.time()
        else:
            current_real_time = time.time()
            total_elapsed_time = round(current_real_time - self._begin_time, 2)
            simulation_duration = self._timestamp_func()
            whole_speed = round(simulation_duration / total_elapsed_time, 2)
            self._data_collector.write(f'{whole_speed}x')

            print(f'simulation ratio: {whole_speed}x')
