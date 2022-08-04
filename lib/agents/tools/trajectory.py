import math
from typing import List

import carla
from scipy.spatial import distance
from shapely.geometry import Point, Polygon
from shapely.affinity import rotate


def compute_safe_area(p1: Point, p2: Point, p_center: Point, p_target: Point, vs, dvs, theta):
    s = distance.euclidean((p_target.x, p_target.y), (p_center.x, p_center.y))
    dts = s / vs
    vs_plus = vs * (1 + dvs)
    vs_minus = vs * (1 - dvs)
    rs_plus = dts * vs_plus
    rs_minus = dts * vs_minus

    direction = Point(p2.x - p1.x, p2.y - p1.y)
    #     print(direction)
    module = math.sqrt(direction.x ** 2 + direction.y ** 2)

    direction = Point(direction.x / module, direction.y / module)
    inner_circle = p_center.buffer(rs_minus)
    outer_circle = p_center.buffer(rs_plus)

    ring = outer_circle.difference(inner_circle)
    radius_outer_circle = vs + dvs
    triangle = Polygon([p_center,
                        (p_center.x + radius_outer_circle, p_center.y + math.tan(theta) * radius_outer_circle),
                        (p_center.x + radius_outer_circle, p_center.y - math.tan(theta) * radius_outer_circle)])

    #     θ = math.ta tan-1 (y/x)
    direction_sign = 1 if direction.y >= 0 else -1
    direction_angle = math.acos(1 * direction.x) * direction_sign
    rotated_triangle = rotate(triangle, direction_angle, origin=p_center, use_radians=True)
    return ring.intersection(rotated_triangle)


def joint_safe_area(routes, v_ms, delta_ms, thresholds_grades):
    # def are_waypoints_the_same(w0, w1):
    #     return w0.transform.location.x == w1.transform.location.x and w0.transform.location.y == w1.transform.location.y
    waypoints = [routes[0]]
    for w in routes[1:]:
        if w[0].transform.location != waypoints[-1][0].transform.location:
            waypoints.append(w)
    pairwise_list = zip(waypoints, waypoints[1:], waypoints[2:])
    results = [waypoints[0], waypoints[1]]
    for w1, w2, w_target in pairwise_list:
        p1 = Point(w1[0].transform.location.x, w1[0].transform.location.y)
        p2 = Point(w2[0].transform.location.x, w2[0].transform.location.y)
        p_target = Point(w_target[0].transform.location.x, w_target[0].transform.location.y)

        second_last = Point(results[-2][0].transform.location.x, results[-2][0].transform.location.y)
        last = Point(results[-1][0].transform.location.x, results[-1][0].transform.location.y)

        SA_based_thresholds = compute_safe_area(second_last, last, p2, p_target, v_ms, delta_ms,
                                                math.radians(thresholds_grades))

        SA_based_awkward_case = compute_safe_area(p1, p2, p2, p_target, v_ms, delta_ms, math.radians(thresholds_grades))
        SA = SA_based_thresholds.intersection(SA_based_awkward_case)
        if not SA.contains(p_target):
            results.append(w_target)

    results.append(waypoints[-1])
    return results
