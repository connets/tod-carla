import argparse

import carla
import numpy.random as random
import pygame
from carla import libcarla
from carla.libcarla import World, BlueprintLibrary

from src.args_parse import my_parser
from src.TeleWorld import TeleWorld, TeleActuatorWorld
from src.utils.Hud import HUD
from src.utils.KeyboardController import KeyboardController


def main():
    conf_files = my_parser.parse_configuration_files()
    carla_conf = my_parser.parse_carla_args(conf_files.carla_server_file)
    client: libcarla.Client = carla.Client(carla_conf.host, carla_conf.port)
    client.set_timeout(carla_conf.timeout)
    print("Connected to Carla Server v.", client.get_server_version())
    traffic_manager = client.get_trafficmanager()

    pygame.init()
    pygame.font.init()

    sim_world = client.load_world(carla_conf.world)

    display = pygame.display.set_mode((1280, 720), pygame.HWSURFACE | pygame.DOUBLEBUF)
    display.fill((0, 0, 0))
    pygame.display.flip()

    hud = HUD(1280, 720)
    controller = KeyboardController()
    world = TeleActuatorWorld(sim_world, carla_conf, controller, hud)
    sim_world.wait_for_tick()
    clock = pygame.time.Clock()
    while True:
        clock.tick_busy_loop(60)
        world.tick(clock)
        world.render(display)
        pygame.display.flip()


if __name__ == '__main__':
    main()
