import csv
import logging
import os
from datetime import datetime

from src import utils
from src.actor.TeleActor import TeleActor
from src.args_parse.TeleConfiguration import TeleConfiguration
from src.folder_path import GENERAL_OUT_PATH, GENERAL_LOG_PATH

DIR_SIMULATION = TeleConfiguration()['carla_scenario_file']['delay']['backhaul']['uplink_extra_delay'][
                     'family'] + '_' + '_'.join(str(v) for v in
                                                TeleConfiguration()['carla_scenario_file']['delay']['backhaul'][
                                                    'uplink_extra_delay'][
                                                    'parameters'].values()) + '|' + datetime.now().strftime(
    "%Y-%m-%d_%H:%M:%S")

CURRENT_OUT_PATH = GENERAL_OUT_PATH + DIR_SIMULATION + '/'
os.mkdir(CURRENT_OUT_PATH)

CURRENT_LOG_PATH = GENERAL_LOG_PATH + DIR_SIMULATION + '/'
os.mkdir(CURRENT_LOG_PATH)


def _configure_logger(name, log_format="%(asctime)s [%(threadName)-12.12s] %(message)s", output_file_path=None):
    log_formatter = logging.Formatter(log_format)
    if output_file_path is not None:
        handler = logging.FileHandler(output_file_path)
        handler.setFormatter(log_formatter)
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(log_formatter)

    # logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # logger.propagate = False

    logger.addHandler(handler)

    return logger


class _NetworkLogger:
    def __init__(self, file_path):
        self._logger = _configure_logger('network', log_format='%(message)s',
                                         output_file_path=file_path)

    def write(self, text):
        self._logger.info(text)


class _EventLogger:
    def __init__(self, file_path):
        self._logger = _configure_logger('event', log_format='%(message)s',
                                         output_file_path=file_path)

        self._logger.info('scheduled_timestamp, type, event')

    def write(self, scheduled_timestamp, event_type, event):
        self._logger.info(f'{(scheduled_timestamp)}, {event_type}, {event.name_event}')


class TeleLogger():
    network_logger = _NetworkLogger(f'{CURRENT_LOG_PATH}network.log')
    event_logger = _EventLogger(f'{CURRENT_LOG_PATH}event.log')
    # simulation_ratio_logger = _EventLogger(f'{CURRENT_LOG_PATH}simulation_ratio.log')


class DataCollector:
    def __init__(self, file_path):
        super().__init__()
        self._file = open(file_path, 'w', newline='')
        self._writer = csv.writer(self._file)

    def write(self, *args):
        self._writer.writerow(args)
        self._file.flush()
