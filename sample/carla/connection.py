from __future__ import print_function

import argparse
import collections
import datetime
import glob
import logging
import math
import os
import numpy.random as random
import re
import sys
import weakref

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_q
except ImportError:
    raise RuntimeError('*** cannot import pygame, make sure pygame package is installed ***')

import carla

client = carla.Client("172.16.1.219", 2000)
client.set_timeout(50.0)
traffic_manager = client.get_trafficmanager()
