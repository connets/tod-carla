from carla import libcarla, Transform, Location, Rotation
import carla
from numpy import random


def create_sim_world(host, port, timeout, world, seed, sync, time_step=None):
    client: libcarla.Client = carla.Client(host, port)
    client.set_timeout(timeout)
    sim_world: carla.World = client.load_world(world)
    sim_world.set_weather(carla.WeatherParameters.ClearSunset)

    random.seed(seed)

    if sync:
        settings = sim_world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = time_step
        sim_world.apply_settings(settings)
        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_synchronous_mode(True)  # TODO move from here, check if sync is active or not
        traffic_manager.set_random_device_seed(seed)
    client.reload_world(False)  # reload map keeping the world settings
    sim_world.tick()

    # traffic_manager.set_synchronous_mode(True)

    return client, sim_world


def destroy_sim_world(client, sim_world):
    settings = sim_world.get_settings()
    settings.synchronous_mode = False
    settings.fixed_delta_seconds = None
    sim_world.apply_settings(settings)
    traffic_manager = client.get_trafficmanager()
    traffic_manager.set_synchronous_mode(False)
    client.reload_world(False)  # reload map keeping the world settings


def create_route(tele_world, scenario_conf):
    carla_map = tele_world.carla_map
    if 'route' in scenario_conf:
        # for spawn_point in carla_map.get_spawn_points():
        #     if abs(367.227295 - spawn_point.location.x) < 6:
        #         print(spawn_point)
        start_transform = Transform(
            Location(x=scenario_conf['route']['start']['x'], y=scenario_conf['route']['start']['y'],
                     z=scenario_conf['route']['start']['z']),
            Rotation(pitch=scenario_conf['route']['start']['pitch'],
                     yaw=scenario_conf['route']['start']['yaw'],
                     roll=scenario_conf['route']['start']['roll']))
        destination_location = Location(x=scenario_conf['route']['end']['x'],
                                        y=scenario_conf['route']['end']['y'],
                                        z=scenario_conf['route']['end']['z'])
    else:
        spawn_points = carla_map.get_spawn_points()
        start_transform = random.choice(spawn_points) if spawn_points else carla.Transform()
        destination_location = random.choice(spawn_points).location

    return start_transform, destination_location
