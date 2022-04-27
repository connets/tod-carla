import logging
import os

from src.folder_path import LOG_PATH
from src.utils.MySingleton import Singleton
from datetime import datetime


def _configure_logger(log_format="%(asctime)s [%(threadName)-12.12s] %(message)s", output_file_path=None):
    log_formatter = logging.Formatter(log_format)
    # logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    if output_file_path is not None:
        handler = logging.FileHandler(output_file_path)
        handler.setFormatter(log_formatter)
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(log_formatter)
    logger.propagate = False

    logger.addHandler(handler)

    return logger


@Singleton
class TeleLogger:
    _dt_string = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    _current_simulation_log_path = LOG_PATH + _dt_string + '/'
    os.mkdir(_current_simulation_log_path)

    network_logger = _configure_logger(output_file_path=f'{_current_simulation_log_path}/network.log')
