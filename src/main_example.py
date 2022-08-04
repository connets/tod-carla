import re

import carla
import math
import numpy as np
from numpy import char

from src.core import TeleSimulator
from src.utils import carla_utils


class TmpA:
    def __init__(self):
        self.b = 34
        self.tmp = lambda: print(self.b)


if __name__ == '__main__':
    a = TmpA()
    a.b = 100
    a.tmp()