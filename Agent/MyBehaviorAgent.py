from enum import Enum
import carla
import math
import itertools
import numpy as np

from lib.agents.navigation.behavior_agent import BehaviorAgent
from lib.agents.navigation.local_planner import RoadOption
#from lib.agents.navigation.behavior_types import Cautious, Aggressive, Normal, Custom
from lib.agents.tools.misc import get_speed, positive, is_within_distance, compute_distance

from utils.TeleVehicleState import OtherPedestrianState

from utils.InterCommunicationListeners import InterCommunicationListeners
from pycarlanet.listeners import ActorManager
from pycarlanet import CarlanetActor

class Decision(Enum):
    SLOW_DOWN = 0
    BREAK = 1
    EMERGENCY_BREAK = 2

#Method                             Inputs                                          Key Outputs                              	            Advantages	                                Limitations
#Time-to-Collision (TTC)            Position, velocity	                            Time until potential collision                          Simple and intuitive	                    Assumes constant velocity; no evasive maneuvers
#Relative Velocity/Position         Position, velocity, orientation	                Direction of relative motion	                        Fast, works with basic information	        Assumes constant motion, no acceleration
#Monte Carlo Simulation	            Position, velocity, acceleration	            Probability of collision from many scenarios	        Handles uncertainty and variability	        Computationally expensive, complex modeling
#Dynamic Time-to-Collision (DTTC)	Position, velocity, acceleration	            Updated time-to-collision	                            Considers acceleration and steering	        Still assumes some predictability
#Bayesian Inference	                Position, velocity, sensor data	                Real-time collision probability	                        Handles uncertainty, adapts in real time	Requires probabilistic models and computation
#Machine Learning	                Sensor data, position, velocity	                Collision probability prediction	                    Can handle complex, real-world scenarios	Needs large data for training
class CollisionCalculationMethod(Enum):
    CARLADEFAULT = 0  # Carla Default
    TTC = 1  # Time-to-Collision (TTC)
    TTC_WITH_ROUTE = 2  # Time-to-Collision (TTC) with route    
    RVP = 3  # Relative Velocity/Position
    MONTECARLO = 4  # Monte Carlo Simulation
    DTTC = 5  # Dynamic Time-to-Collision (DTTC)
    BAYESIANINFERENCE = 6  # Bayesian Inference
    MACHINELEARNING = 7  # Machine Learning
    
    @staticmethod
    def getMethodFromString(stringType):
        if stringType == "TTC":
            return CollisionCalculationMethod.TTC
        elif stringType == "TTC_WITH_ROUTE":
            return CollisionCalculationMethod.TTC_WITH_ROUTE
        elif stringType == "RVP":
            return CollisionCalculationMethod.RVP
        elif stringType == "MONTECARLO":
            return CollisionCalculationMethod.MONTECARLO
        elif stringType == "DTTC":
            return CollisionCalculationMethod.DTTC
        elif stringType == "BAYESIANINFERENCE":
            return CollisionCalculationMethod.BAYESIANINFERENCE
        elif stringType == "MACHINELEARNING":
            return CollisionCalculationMethod.MACHINELEARNING
        else:
            return CollisionCalculationMethod.CARLADEFAULT
    
    @staticmethod
    def calculate_collision(method, *args, **kwargs) -> Decision:
        #ingore specific actors
        if kwargs['other'].id in kwargs['me'].ignoreIds: return None

        #if other vehicle is stopped use my route to understand if is on my route
        if abs(kwargs['other'].velocity.x) < 0.2 and abs(kwargs['other'].velocity.y) < 0.2 and abs(kwargs['other'].velocity.z) < 0.2:
            kwargs['projection'] = False
            walker_state, walker, distance = CollisionCalculationMethod.carladefault(*args, **kwargs)
            self = kwargs['me']
            # walker_state, walker, distance = self._vehicle_obstacle_detected(
            #     walker_list,
            #     max(self._behavior.min_proximity_threshold, self._speed_limit / 3),
            #     up_angle_th=60
            # )

            if walker_state:
                # Distance is computed from the center of the two cars,
                # we use bounding boxes to calculate the actual distance
                distance = distance - max(
                    walker.bounding_box.extent.y, walker.bounding_box.extent.x) - max(
                    self._vehicle_extent.y, self._vehicle_extent.x)
                # Emergency brake if the car is very close.
                if distance < self._behavior.braking_distance:
                    #print("emergency stop")
                    #return self.emergency_stop()
                    return Decision.EMERGENCY_BREAK
                if distance < self._behavior.braking_distance + 5:
                    #print("slow down")
                    #return self.slow_down()
                    return Decision.SLOW_DOWN

            return None

        if method == CollisionCalculationMethod.CARLADEFAULT:
            walker_state, walker, distance = CollisionCalculationMethod.carladefault(*args, **kwargs)
            self = kwargs['me']
            # walker_state, walker, distance = self._vehicle_obstacle_detected(
            #     walker_list,
            #     max(self._behavior.min_proximity_threshold, self._speed_limit / 3),
            #     up_angle_th=60
            # )

            if walker_state:
                # Distance is computed from the center of the two cars,
                # we use bounding boxes to calculate the actual distance
                distance = distance - max(
                    walker.bounding_box.extent.y, walker.bounding_box.extent.x) - max(
                    self._vehicle_extent.y, self._vehicle_extent.x)
                # Emergency brake if the car is very close.
                if distance < self._behavior.braking_distance:
                    #print("emergency stop")
                    #return self.emergency_stop()
                    return Decision.EMERGENCY_BREAK
                if distance < self._behavior.braking_distance + 5:
                    #print("slow down")
                    #return self.slow_down()
                    return Decision.SLOW_DOWN

            return None


        if method == CollisionCalculationMethod.TTC:
            val = CollisionCalculationMethod.calculate_ttc(*args, **kwargs)
            if val <= 0 or val >= 2: return None
            if val > 1 and val < 2:
                return Decision.SLOW_DOWN
            elif val <= 1 and val >= 0.5:
                return Decision.BREAK
            elif val < 0.5:
                return Decision.EMERGENCY_BREAK
            
        if method == CollisionCalculationMethod.TTC_WITH_ROUTE:
            val = CollisionCalculationMethod.calculate_ttc_with_route(*args, **kwargs)
            if val <= 0 or val >= 2: return None
            if val > 1 and val < 2:
                return Decision.SLOW_DOWN
            elif val <= 1 and val >= 0.5:
                return Decision.BREAK
            elif val < 0.5:
                return Decision.EMERGENCY_BREAK
            
        if method == CollisionCalculationMethod.RVP:
            val = CollisionCalculationMethod.calculate_rvp(*args, **kwargs)
            return None
        
        if method == CollisionCalculationMethod.MONTECARLO:
            val = CollisionCalculationMethod.calculate_montecarlo(*args, **kwargs)
            return None
        
        if method == CollisionCalculationMethod.DTTC:
            val = CollisionCalculationMethod.calculate_dttc(*args, **kwargs)
            return None
        
        if method == CollisionCalculationMethod.BAYESIANINFERENCE:
            val = CollisionCalculationMethod.calculate_bayesianinference(*args, **kwargs)
            return None
        
        if method == CollisionCalculationMethod.MACHINELEARNING:
            val = CollisionCalculationMethod.calculate_machinelearning(*args, **kwargs)
            return None
        
        raise ValueError("Invalid collision calculation method")
        
    @staticmethod
    def carladefault(me, other, projection = True):
        self = me
        # Implementation for carla default
        #project obstacles_list to keep track of the movements
        def project_obstacles(o, circleCount = 10, pointsPerCircle = 24):
            projected_obstacles_list = []
            maxVelocity = max(abs(o.velocity.x), abs(o.velocity.y), abs(o.velocity.z)) * 2 # consider base acceleration + 2m/s for the pedestrian
            distances = [(i * maxVelocity) / (circleCount - 1) for i in range(circleCount)]
            
            o_location = o.get_transform().location
            for distance in distances:
                for angle in range(0, 360, 15):  #Loop through angles from 0 to 360 degrees
                    rad = angle * (math.pi / 180)  #Convert angle to radians
                    pr_location = carla.Location(
                        x=o_location.x + (distance * math.cos(rad)),
                        y=o_location.y + (distance * math.sin(rad)),
                        z=o_location.z
                    )
                    pr = OtherPedestrianState(o.get_timestamp(), 'pr', carla.Transform(pr_location, o.get_transform().rotation), o.get_bounding_box(), o.get_velocity())
                    projected_obstacles_list.append(pr)

            return projected_obstacles_list

        projected_obstacles_list = []
        projected_obstacles_list.append(other)
        if projection: projected_obstacles_list.extend(project_obstacles(other))
        
        
        speed = get_speed(self._last_vehicle_state) / 3.6  # m/s
        d_pr = speed * self.t_pr  # perception-reaction distance
        d_braking = speed ** 2 / (2 * self.u * self.g)  # braking distance
        d_total = max(d_pr + d_braking, 6)
        safe_distance_waypoints = [self._map.get_waypoint(self._last_vehicle_state.get_location(),
                                                          lane_type=carla.LaneType.Any)] + \
                                  [w_d[0] for w_d in self._local_planner.get_next_waypoint_and_direction(
                                      int(d_total / self._sampling_resolution))]

        for path_wpt, vehicle in itertools.product(safe_distance_waypoints, projected_obstacles_list):
            vehicle_transform = vehicle.get_transform()
            vehicle_wpt = self._map.get_waypoint(vehicle_transform.location, lane_type=carla.LaneType.Any)
            if vehicle_wpt.road_id != path_wpt.road_id: continue
            distance = compute_distance(vehicle_transform.location, path_wpt.transform.location)
            #print(f"distance with {vehicle} is: {distance}")
            if distance <= max(self._behavior.min_proximity_threshold, self._speed_limit / 3):
                return True, vehicle, distance

        return False, None, -1

    @staticmethod
    def calculate_ttc(me, other):
        """
        Calculate the Time-to-Collision (TTC) between the observer and the object.
        
        Parameters:
        - position_me: (x1, y1, z1) position of your vehicle (numpy array)
        - velocity_me: (vx1, vy1, vz1) velocity of your vehicle (numpy array)
        - position_obs: (x2, y2, z2) position of the observer or object (numpy array)
        - velocity_obs: (vx2, vy2, vz2) velocity of the observer or object (numpy array)
        
        Returns:
        - ttc: Time to collision in seconds (positive value means collision in the future)
        """

        position_me = np.array([
            me._last_vehicle_state.get_transform().location.x,
            me._last_vehicle_state.get_transform().location.y,
            me._last_vehicle_state.get_transform().location.z
        ])
        velocity_me = np.array([
            me._last_vehicle_state.get_velocity().x,
            me._last_vehicle_state.get_velocity().y,
            me._last_vehicle_state.get_velocity().z
        ])
        position_other = np.array([
            other.get_transform().location.x,
            other.get_transform().location.y,
            other.get_transform().location.z
        ])
        velocity_other = np.array([
            other.get_velocity().x,
            other.get_velocity().y,
            other.get_velocity().z
        ])


        
        
        # Calculate the relative position and relative velocity
        relative_position = position_other - position_me
        relative_velocity = velocity_other - velocity_me
        
        # Calculate the dot product of relative position and relative velocity
        dot_product = np.dot(relative_position, relative_velocity)
        
        # Calculate the squared magnitude of the relative velocity
        relative_velocity_magnitude_squared = np.dot(relative_velocity, relative_velocity)
        
        # Avoid division by zero (if relative velocity is zero, no collision will occur)
        if relative_velocity_magnitude_squared == 0:
            return float('inf')  # No collision if objects are moving together with same velocity
        
        # Calculate TTC
        ttc = -dot_product / relative_velocity_magnitude_squared
        
        # Return TTC (positive value means collision in the future)
        #print(f"TTC with {other} is: {ttc}")
        return ttc

    @staticmethod
    def calculate_ttc_with_route(me, other, time_step=0.2, max_time=5.0):
        """
        Calculate the Time-to-Collision (TTC) between the observer and the object, 
        considering the route of the vehicle.
        
        Parameters:
        - me: the vehicle object (your vehicle)
        - other: the other vehicle object (the object you're calculating TTC with)
        - route_func: a function that returns the vehicle's position and velocity along its route as a function of time
        - time_step: time increment in seconds to check positions along the route
        - max_time: maximum time to check for collision (this prevents infinite loops)
        
        Returns:
        - ttc: Time to collision in seconds (positive value means collision in the future)
        """
        def route_func(current_position, velocity, t, route_points):
            """
            Calculates the position and velocity of the agent at time t based on a list of waypoints (route).
            
            Parameters:
            - current_position: my current position
            - velocity: current my current velocity
            - t: time in seconds
            - route_points: List of waypoints, where each waypoint is a dictionary {'x': x, 'y': y, 'z': z}
            
            Returns:
            - future_position: the position of the vehicle at time t (numpy array)
            - future_velocity: the velocity of the vehicle at time t (numpy array)
            """
            
            # Total distance the agent will travel in time 't'
            distance_to_move = np.linalg.norm(velocity) * t  # Distance = speed * time

            route_points = [np.array([point['x'], point['y'], point['z']]) for point in route_points]
            
            # find_closest_point, Find the current segment in the route
            ## Calculate the distance from the current position to each waypoint
            distances = [np.linalg.norm(point - current_position) for point in route_points]
            ## Return the index of the closest waypoint
            closest_point_idx = np.argmin(distances)
            
            # Start at the closest waypoint and move towards the next waypoints
            remaining_distance = distance_to_move
            current_position_segment = route_points[closest_point_idx]
            
            # Iterate over the route to estimate the future position
            for i in range(closest_point_idx, len(route_points) - 1):
                next_position_segment = route_points[i + 1]
                
                # Calculate the direction and distance to the next waypoint
                segment_direction = next_position_segment - current_position_segment
                segment_distance = np.linalg.norm(segment_direction)
                
                if remaining_distance < segment_distance:
                    # If remaining distance is less than the segment distance, move along this segment
                    direction_normalized = segment_direction / segment_distance
                    future_position = current_position_segment + direction_normalized * remaining_distance
                    return future_position, velocity
                
                # Otherwise, move the full distance to the next waypoint and update remaining distance
                remaining_distance -= segment_distance
                current_position_segment = next_position_segment
            
            # If we run out of route segments, return the last waypoint's position
            return route_points[-1], velocity

        # Get the initial position and velocity of your vehicle
        position_me = np.array([
            me._last_vehicle_state.get_transform().location.x,
            me._last_vehicle_state.get_transform().location.y,
            me._last_vehicle_state.get_transform().location.z
        ])
        velocity_me = np.array([
            me._last_vehicle_state.get_velocity().x,
            me._last_vehicle_state.get_velocity().y,
            me._last_vehicle_state.get_velocity().z
        ])
        
        # Get the position and velocity of the other vehicle
        position_other = np.array([
            other.get_transform().location.x,
            other.get_transform().location.y,
            other.get_transform().location.z
        ])
        velocity_other = np.array([
            other.get_velocity().x,
            other.get_velocity().y,
            other.get_velocity().z
        ])
        
        # For each time step, get the future position of your vehicle based on the route function
        for t in np.arange(0, max_time, time_step):
            # Get future position and velocity of your vehicle at time t along the route
            future_position_me, future_velocity_me = route_func(current_position=position_me, velocity=velocity_me, t=t, route_points=me._waypoints)
            
            # Calculate the relative position and relative velocity at time t
            relative_position = position_other - future_position_me
            relative_velocity = velocity_other - future_velocity_me
            
            # Calculate the dot product of relative position and relative velocity
            dot_product = np.dot(relative_position, relative_velocity)
            
            # Calculate the squared magnitude of the relative velocity
            relative_velocity_magnitude_squared = np.dot(relative_velocity, relative_velocity)
            
            # Avoid division by zero (if relative velocity is zero, no collision will occur)
            if relative_velocity_magnitude_squared == 0:
                return float('inf')  # No collision if objects are moving together with same velocity
            
            # Calculate TTC at this time step
            ttc = -dot_product / relative_velocity_magnitude_squared
            
            # If TTC is positive and within the current time step, return it
            if ttc > 0:
                return ttc

        # If no collision within max_time, return inf
        return float('inf')

    @staticmethod
    def calculate_rvp():
        # Implementation for RVP method
        return None

    @staticmethod
    def calculate_montecarlo():
        # Implementation for Monte Carlo method
        return None

    @staticmethod
    def calculate_dttc():
        # Implementation for DTTC method
        return None

    @staticmethod
    def calculate_bayesianinference():
        # Implementation for Bayesian Inference method
        return None

    @staticmethod
    def calculate_machinelearning():
        # Implementation for Machine Learning method
        return None


class MyBehaviorAgent(BehaviorAgent):

    def __init__(self, vehicle, sampling_resolution, behavior='normal', opt_dict={}, map_inst=None, grp_inst=None):
        super().__init__(vehicle, sampling_resolution, behavior, opt_dict=opt_dict, map_inst=map_inst, grp_inst=grp_inst)

        self.collision_calculation_method = CollisionCalculationMethod.getMethodFromString(opt_dict['collision_calculation_method'])

        self.ignoreIds = []
        for e in opt_dict['ignoreIds']:
            founded = InterCommunicationListeners.instance.askToManager(ActorManager, 'get_actor_from_id', e)
            if founded is not None and isinstance(founded, CarlanetActor):
                self.ignoreIds.append(founded.carla_actor.id)                

    def run_step(self, debug=False):
        """
        Execute one step of navigation.

            :param debug: boolean for debugging
            :return control: carla.VehicleControl
        """
        self._update_information()

        control = None
        if self._behavior.tailgate_counter > 0:
            self._behavior.tailgate_counter -= 1

        #ego_vehicle_loc = self._last_vehicle_state.get_location()
        #ego_vehicle_wp = self._map.get_waypoint(ego_vehicle_loc)

        # 1: Red lights and stops behavior
        if self.traffic_light_manager():
            return self.emergency_stop()

        # 2.1: Pedestrian avoidance behaviors (use visible pedestrains getted from the state)
        #controlToAppy = self.pedestrian_avoid_manager()
        #if controlToAppy is not None: return controlToAppy

        # 2.2: Car following behaviors
        #controlToAppy = self.collision_and_car_avoid_manager()
        #if controlToAppy is not None: return controlToAppy

        # 3: Intersection behavior
        elif self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
            target_speed = min([
                self._behavior.max_speed,
                self._speed_limit - 5])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)

        # 4: Normal behavior
        else:
            target_speed = min([
                self._behavior.max_speed,
                self._speed_limit - self._behavior.speed_lim_dist])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)
        control.manual_gear_shift = False

        #move here control pedestrian and car avoid to keep the trajectory direction steer instead of stopping in front of me

        # 2.1: Pedestrian avoidance behaviors (use visible pedestrains getted from the state)
        controlToAppy = self.pedestrian_avoid_manager()
        if controlToAppy is not None:
            control.throttle = controlToAppy.throttle
            control.brake = controlToAppy.brake
            control.hand_brake = controlToAppy.hand_brake

        # 2.2: Car following behaviors
        controlToAppy = self.collision_and_car_avoid_manager()
        if controlToAppy is not None:            
            control.throttle = controlToAppy.throttle
            control.brake = controlToAppy.brake
            control.hand_brake = controlToAppy.hand_brake

        return control
    
    def collision_and_car_avoid_manager(self):
        """
        This module is in charge of warning in case of a collision
        and managing possible tailgating chances.

            :param location: current location of the agent
            :param waypoint: current waypoint of the agent
            :return vehicle_state: True if there is a vehicle nearby, False if not
            :return vehicle: nearby vehicle
            :return distance: distance to nearby vehicle
        """
        if self._ignore_vehicles: return None

        vehicle_list = self._other_vehicles.values()

        if len(vehicle_list) == 0: return None

        ego_vehicle_loc = self._last_vehicle_state.get_location()
        waypoint = self._map.get_waypoint(ego_vehicle_loc)

        decisions = []
        for o in vehicle_list:
            dec = CollisionCalculationMethod.calculate_collision(self.collision_calculation_method, me=self, other=o)
            if dec is not None:
                decisions.append(dec)
            #print(o)
            #print(f"time to collision with {o} is: {dec}")
        #print(decisions)
        if len(decisions) > 0:
            sorted_decisions = sorted(decisions, key=lambda x: x.value)
            return self.getControlFromDecision(sorted_decisions[-1])
        #print()
        return None
        #TODO: get worst case and apply

        

        #def dist(v):
        #    return v.get_location().distance(waypoint.transform.location)

        #vehicle_list = [v for v in vehicle_list if dist(v) < 45 and v.id != self._last_vehicle_state.id]

        vehicle_state, vehicle, distance = self._vehicle_obstacle_detected(
            vehicle_list,
            max(self._behavior.min_proximity_threshold, self._speed_limit / 3),
            up_angle_th=30
        )

        # Check for tailgating
        if not vehicle_state and self._direction == RoadOption.LANEFOLLOW \
                and not waypoint.is_junction and self._speed > 10 \
                and self._behavior.tailgate_counter == 0:
            self._tailgating(waypoint, vehicle_list)


        if vehicle_state:
            # Distance is computed from the center of the two cars,
            # we use bounding boxes to calculate the actual distance
            distance = distance - max(
                vehicle.bounding_box.extent.y, vehicle.bounding_box.extent.x) - max(
                self._vehicle_extent.y, self._vehicle_extent.x)

            # Emergency brake if the car is very close.
            if distance < self._behavior.braking_distance:
                return self.emergency_stop()
            #else:
            #    control = self.car_following_manager(vehicle, distance)

        return None

        #return vehicle_state, vehicle, distance

    def pedestrian_avoid_manager(self):
        """
        This module is in charge of warning in case of a collision
        with any pedestrian.

            :param location: current location of the agent
            :param waypoint: current waypoint of the agent
            :return vehicle_state: True if there is a walker nearby, False if not
            :return vehicle: nearby walker
            :return distance: distance to nearby walker
        """

        if self._ignore_pedestrian: return None

        walker_list = self._other_pedestrians.values()

        if len(walker_list) == 0: return None

        decisions = []
        for o in walker_list:
            dec = CollisionCalculationMethod.calculate_collision(self.collision_calculation_method, me=self, other=o)
            if dec is not None:
                decisions.append(dec)
            #print(f"time to collision with {o} is: {dec}")
        #print(decisions)
        if len(decisions) > 0:
            sorted_decisions = sorted(decisions, key=lambda x: x.value)
            return self.getControlFromDecision(sorted_decisions[-1])
        return None

    def slow_down(self):
        """
        Overwrites the throttle a brake values of a control to perform speed reduction.
        The steering is kept the same to avoid going out of the lane when stopping during turns

            :param speed (carl.VehicleControl): control to be modified
        """
        control = carla.VehicleControl()
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False
        return control

    def slow_stop(self):
        """
        Overwrites the throttle a brake values of a control to perform speed reduction.
        The steering is kept the same to avoid going out of the lane when stopping during turns

            :param speed (carl.VehicleControl): control to be modified
        """
        control = carla.VehicleControl()
        control.throttle = 0.0
        control.brake = 0.3
        control.hand_brake = False
        return control

    def getControlFromDecision(self, decision):
        if decision == Decision.SLOW_DOWN:
            #print("slown down")
            return self.slow_down()
        elif decision == Decision.BREAK:
            #print("slow stop")
            return self.slow_stop()
        elif decision == Decision.EMERGENCY_BREAK:
            #print("emergency stop")
            return self.emergency_stop()

    def set_destinations(self, *end_locations, start_location=None):
        waypoints = super().set_destinations(*end_locations, start_location=start_location)
        self._waypoints = waypoints
        return waypoints