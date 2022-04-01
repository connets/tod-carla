import inspect
import sys
import time

import carla
import pygame
from carla import libcarla

from src.TeleActor import TeleVehicle
from src.TeleSensor.CameraManager import CameraManager
from src.args_parse import my_parser
from src.TeleWorld import TeleActuatorWorld
from src.utils.Hud import HUD
from src.TeleWorldController import KeyboardTeleWorldController


def main():

    conf_files = my_parser.parse_configuration_files()
    carla_conf = my_parser.parse_carla_args(conf_files['carla_server_file'])
    pygame.init()
    pygame.font.init()

    client: libcarla.Client = carla.Client(carla_conf['host'], carla_conf['port'])
    client.set_timeout(carla_conf['timeout'])
    sim_world = client.load_world(carla_conf['world'], carla.MapLayer.Buildings)

    traffic_manager = client.get_trafficmanager()
    display = pygame.display.set_mode((carla_conf['camera.width'], carla_conf['camera.height']), pygame.HWSURFACE | pygame.DOUBLEBUF)
    display.fill((0, 0, 0))
    pygame.display.flip()

    player_attrs = {'role_name': 'hero'}
    player = TeleVehicle(carla_conf['vehicle_player'], '1', player_attrs, modify_vehicle_physics=True)

    hud = HUD(carla_conf['camera.width'], carla_conf['camera.height'])
    controller = KeyboardTeleWorldController(None)  # TODO remove from here
    tele_world = TeleActuatorWorld(sim_world, carla_conf, controller, hud)
    tele_world.add_vehicle_player(player)

    print(player.get_world(), sim_world)
    camera_manager = CameraManager(hud, 2.2, 1280, 720)
    tele_world.add_sensor(camera_manager, player)
    sim_world.wait_for_tick()
    clock = pygame.time.Clock()

    exit = False
    while not exit:
        clock.tick_busy_loop(60)
        exit = tele_world.tick(clock) != 0
        tele_world.render(display)
        pygame.display.flip()
        # exit = i == 1000 | exit
    # TODO destroy everything
    pygame.quit()
    tele_world.destroy()


if __name__ == '__main__':
    main()
