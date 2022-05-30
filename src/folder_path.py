from datetime import datetime
import os
from pathlib import Path

PROJECT_PATH = ''.join(map(lambda x: x + '/', os.path.abspath(__file__).split('/')[:-2]))

CONFIGURATION_FILE_PATH = PROJECT_PATH + 'configuration/'
CONFIGURATION_SCENARIO_PATH = CONFIGURATION_FILE_PATH + 'scenario/'
SRC_PATH = PROJECT_PATH + 'src/'

GENERAL_OUT_PATH = PROJECT_PATH + 'out/'
Path(GENERAL_OUT_PATH).mkdir(parents=True, exist_ok=True)

GENERAL_LOG_PATH = PROJECT_PATH + 'log/'
Path(GENERAL_LOG_PATH).mkdir(parents=True, exist_ok=True)