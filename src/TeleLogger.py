import logging
import os

from src.folder_path import LOG_PATH
from datetime import datetime


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


class TeleLogger:
    _dt_string = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    _current_simulation_log_path = LOG_PATH + _dt_string + '/'
    os.mkdir(_current_simulation_log_path)


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

            self._logger.info('scheduled_timestamp, event')

        def write(self, scheduled_timestamp, event):
            self._logger.info(f'{scheduled_timestamp}, {event.__class__.__name__}')

    network_logger = _NetworkLogger(f'{_current_simulation_log_path}network.log')

    event_logger = _EventLogger(f'{_current_simulation_log_path}event.log')



def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


if __name__ == '__main__':
    # first file logger
    logger = setup_logger('first_logger', 'first_logfile.log')
    logger.info('This is just info message')

    # second file logger
    super_logger = setup_logger('second_logger', 'second_logfile.log')
    super_logger.info('This is an error message')


    def another_method():
        # using logger defined above also works here
        logger.info('Inside method')
