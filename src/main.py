import carla
import pygame
from carla import libcarla

from src.CarlaVehicle import CarlaVehicle
from src.args_parse import my_parser
from src.TeleWorld import TeleActuatorWorld
from src.sensors.CameraManager import CameraManager
from src.utils.Hud import HUD
from src.CarlaWorldController import KeyboardCarlaWorldController


def main():
    conf_files = my_parser.parse_configuration_files()
    carla_conf = my_parser.parse_carla_args(conf_files.carla_server_file)
    client: libcarla.Client = carla.Client(carla_conf.host, carla_conf.port)
    client.set_timeout(carla_conf.timeout)
    traffic_manager = client.get_trafficmanager()

    pygame.init()
    pygame.font.init()

    sim_world = client.load_world(carla_conf.world)

    display = pygame.display.set_mode((1280, 720), pygame.HWSURFACE | pygame.DOUBLEBUF)
    display.fill((0, 0, 0))
    pygame.display.flip()

    player_attrs = {'role_name': 'hero'}
    player = CarlaVehicle(carla_conf.vehicle_player, '1', player_attrs)

    hud = HUD(1280, 720)
    controller = KeyboardCarlaWorldController(None)  # TODO remove from here
    tele_world = TeleActuatorWorld(sim_world, carla_conf, controller, hud)
    tele_world.add_vehicle_player(player)

    print(player.get_world(), sim_world)
    camera_manager = CameraManager(hud, 2.2)
    camera_manager.spawn_in_world(player) #TODO remove from here and add to TeleWorld class
    tele_world.camera_manager = camera_manager
    sim_world.wait_for_tick()
    clock = pygame.time.Clock()

    exit = False
    while not exit:
        clock.tick_busy_loop(60)
        exit = tele_world.tick(clock) != 0
        tele_world.render(display)
        pygame.display.flip()

    # TODO destroy everything
    pygame.quit()
    tele_world.destroy()


if __name__ == '__main__':
    main()
