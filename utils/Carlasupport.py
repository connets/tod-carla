import math
import re

import carla
import numpy as np


def find_weather_presets():
    """Method to find weather presets"""
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')

    def name(x): return ' '.join(m.group(0) for m in rgx.finditer(x))

    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    """Method to get actor display name"""
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


def get_closest_spawning_points(carla_map, loc):
    res = []
    for spawn_point in carla_map.get_spawn_points():
        if abs(loc.x - spawn_point.location.x) < 5 and abs(loc.y - spawn_point.location.y) < 5:
            res.append(spawn_point)
    return res


def angle_between(v1: carla.Vector3D, v2: carla.Vector3D):
    """
    Return the degrees of the angle between two vector
    """
    v1_u = v1.make_unit_vector()
    v2_u = v2.make_unit_vector()
    return math.degrees((np.arccos(np.clip(v1_u.dot(v2_u), -1.0, 1.0))))
