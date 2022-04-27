import os

PROJECT_PATH = ''.join(map(lambda x: x + '/', os.path.abspath(__file__).split('/')[:-2]))

CONFIGURATION_FILE_PATH = PROJECT_PATH + 'configuration/'
CONFIGURATION_ROUTE_PATH = CONFIGURATION_FILE_PATH + 'route/'
SRC_PATH = PROJECT_PATH + 'src/'
OUT_PATH = PROJECT_PATH + 'out/'
LOG_PATH = PROJECT_PATH + 'log/'
