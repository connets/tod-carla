import csv
import logging
from src.utils.decorators import DecoratorSingleton


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


@DecoratorSingleton
class TeleLogger():
    def __init__(self, log_path):
        self.network_logger = _NetworkLogger(f'{log_path}network.log')
        self.event_logger = _EventLogger(f'{log_path}event.log')
    # simulation_ratio_logger = _EventLogger(f'{CURRENT_LOG_PATH}simulation_ratio.log')


class DataCollector:
    def __init__(self, file_path):
        super().__init__()
        self._file = open(file_path, 'w', newline='')
        self._writer = csv.writer(self._file)

    def write(self, *args):
        self._writer.writerow(args)
        self._file.flush()
