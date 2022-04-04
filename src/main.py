import carla
import pygame
from carla import libcarla

from src.TeleActor import TeleVehicle
from src.TeleSensor import CameraManager, GnssSensor
from src.args_parse import my_parser
from src.TeleWorld import TeleActuatorWorld
from src.utils.Hud import HUD
from src.TeleWorldController import KeyboardTeleWorldController, BasicAgentTeleWorldController, \
    BehaviorAgentTeleWorldController


def main():
    conf_files = my_parser.parse_configuration_files()
    carla_conf = my_parser.parse_carla_args(conf_files['carla_server_file'])
    pygame.init()
    pygame.font.init()

    client: libcarla.Client = carla.Client(carla_conf['host'], carla_conf['port'])
    client.set_timeout(carla_conf['timeout'])

    sim_world = client.load_world(carla_conf['world'])

    builds = sim_world.get_environment_objects(carla.CityObjectLabel.Buildings)
    objects_to_toggle = {build.id for build in builds}

    sim_world.enable_environment_objects(objects_to_toggle, False)

    traffic_manager = client.get_trafficmanager()
    display = pygame.display.set_mode((carla_conf['camera.width'], carla_conf['camera.height']),
                                      pygame.HWSURFACE | pygame.DOUBLEBUF)
    display.fill((0, 0, 0))
    pygame.display.flip()

    player_attrs = {'role_name': 'hero'}
    player = TeleVehicle(carla_conf['vehicle_player'], '1', player_attrs, modify_vehicle_physics=True)

    hud = HUD(carla_conf['camera.width'], carla_conf['camera.height'])
    tele_world = TeleActuatorWorld(sim_world, player, carla_conf, hud)

    camera_manager = CameraManager(hud, 2.2, 1280, 720)
    tele_world.add_sensor(camera_manager, player)

    controller = BehaviorAgentTeleWorldController('aggressive') #TODO change here
    tele_world.add_controller(controller)

    gnss_sensor = GnssSensor()
    tele_world.add_sensor(gnss_sensor, player)

    sim_world.wait_for_tick()
    clock = pygame.time.Clock()

    exit = False
    while not exit:
        clock.tick_busy_loop(60)
        exit = tele_world.tick(clock) != 0
        tele_world.render(display)
        pygame.display.flip()
        print(player.get_location())
        # exit = i == 1000 | exit
    # TODO destroy everything
    pygame.quit()
    tele_world.destroy()


if __name__ == '__main__':
    main()
