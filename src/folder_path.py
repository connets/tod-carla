import os

PROJECT_PATH = ''.join(map(lambda x: x + '/', os.path.abspath(__file__).split('/')[:-2]))

CONFIGURATION_FILE_PATH = PROJECT_PATH + 'configuration/'
SRC_PATH = PROJECT_PATH + 'src/'
