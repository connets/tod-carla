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
    RVP = 2  # Relative Velocity/Position
    MONTECARLO = 3  # Monte Carlo Simulation
    DTTC = 4  # Dynamic Time-to-Collision (DTTC)
    BAYESIANINFERENCE = 5  # Bayesian Inference
    MACHINELEARNING = 6  # Machine Learning
    
    @staticmethod
    def getMethodFromString(stringType):
        if stringType == "TTC":
            return CollisionCalculationMethod.TTC
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
            if val <= 0: return None
            if val > 1 and val < 2:
                return Decision.SLOW_DOWN
            elif val <= 1 and val >= 0.5:
                return Decision.BREAK
            elif val < 0.5:
                return Decision.EMERGENCY_BREAK
        elif method == CollisionCalculationMethod.RVP:
            val = CollisionCalculationMethod.calculate_rvp(*args, **kwargs)
            return None
        elif method == CollisionCalculationMethod.MONTECARLO:
            val = CollisionCalculationMethod.calculate_montecarlo(*args, **kwargs)
            return None
        elif method == CollisionCalculationMethod.DTTC:
            val = CollisionCalculationMethod.calculate_dttc(*args, **kwargs)
            return None
        elif method == CollisionCalculationMethod.BAYESIANINFERENCE:
            val = CollisionCalculationMethod.calculate_bayesianinference(*args, **kwargs)
            return None
        elif method == CollisionCalculationMethod.MACHINELEARNING:
            val = CollisionCalculationMethod.calculate_machinelearning(*args, **kwargs)
            return None
        else:
            raise ValueError("Invalid collision calculation method")
        
    @staticmethod
    def carladefault(me, other):
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
        projected_obstacles_list.extend(project_obstacles(other))
        
        
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
            print(f"distance with {vehicle} is: {distance}")
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
        return ttc

    @staticmethod
    def calculate_rvp():
        # Implementation for RVP method
        #TODO: choose if slown down, emercy break or null 
        return None

    @staticmethod
    def calculate_montecarlo():
        # Implementation for Monte Carlo method
        #TODO: choose if slown down, emercy break or null 
        return None

    @staticmethod
    def calculate_dttc():
        # Implementation for DTTC method
        #TODO: choose if slown down, emercy break or null 
        return None

    @staticmethod
    def calculate_bayesianinference():
        # Implementation for Bayesian Inference method
        #TODO: choose if slown down, emercy break or null 
        return None

    @staticmethod
    def calculate_machinelearning():
        # Implementation for Machine Learning method
        #TODO: choose if slown down, emercy break or null 
        return None




class MyBehaviorAgent(BehaviorAgent):

    def __init__(self, vehicle, sampling_resolution, behavior='normal', opt_dict={}, map_inst=None, grp_inst=None):
        super().__init__(vehicle, sampling_resolution, behavior, opt_dict=opt_dict, map_inst=map_inst, grp_inst=grp_inst)

        self.collision_calculation_method = CollisionCalculationMethod.getMethodFromString(opt_dict['collision_calculation_method'])

        print(self.collision_calculation_method)

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
        controlToAppy = self.pedestrian_avoid_manager()
        if controlToAppy is not None: return controlToAppy

        # 2.2: Car following behaviors
        controlToAppy = self.collision_and_car_avoid_manager()
        if controlToAppy is not None: return controlToAppy

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
            print(f"time to collision with {o} is: {dec}")
        print(decisions)
        if len(decisions) > 0:
            sorted_decisions = sorted(decisions, key=lambda x: x.value)
            return self.getControlFromDecision(sorted_decisions[-1])
        print()
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

        ego_vehicle_loc = self._last_vehicle_state.get_location()
        waypoint = self._map.get_waypoint(ego_vehicle_loc)

        decisions = []
        for o in walker_list:
            dec = CollisionCalculationMethod.calculate_collision(self.collision_calculation_method, me=self, other=o)
            if dec is not None:
                decisions.append(dec)
            print(f"time to collision with {o} is: {dec}")
        print(decisions)
        if len(decisions) > 0:
            sorted_decisions = sorted(decisions, key=lambda x: x.value)
            return self.getControlFromDecision(sorted_decisions[-1])
        print()
        return None
        #return walker_state, walker, distance

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

    # def _vehicle_obstacle_detected(self, obstacles_list=None, max_distance=None, up_angle_th=90, low_angle_th=0, lane_offset=0):
    #     print("MyBehaviorAgent _vehicle_obstacle_detected")
        

    #     #project obstacles_list to keep track of the movements
    #     def project_obstacles(o, circleCount = 10, pointsPerCircle = 24):
    #         projected_obstacles_list = []
    #         maxVelocity = max(abs(o.velocity.x), abs(o.velocity.y), abs(o.velocity.z)) * 2 # consider base acceleration + 2m/s for the pedestrian
    #         distances = [(i * maxVelocity) / (circleCount - 1) for i in range(circleCount)]
            
    #         o_location = o.get_transform().location
    #         for distance in distances:
    #             for angle in range(0, 360, 15):  #Loop through angles from 0 to 360 degrees
    #                 rad = angle * (math.pi / 180)  #Convert angle to radians
    #                 pr_location = carla.Location(
    #                     x=o_location.x + (distance * math.cos(rad)),
    #                     y=o_location.y + (distance * math.sin(rad)),
    #                     z=o_location.z
    #                 )
    #                 pr = OtherPedestrianState(o.get_timestamp(), 'pr', carla.Transform(pr_location, o.get_transform().rotation), o.get_bounding_box(), o.get_velocity())
    #                 projected_obstacles_list.append(pr)

    #         return projected_obstacles_list

    #     projected_obstacles_list = []
    #     for o in obstacles_list:            
    #         projected_obstacles_list.append(o)
    #         projected_obstacles_list.extend(project_obstacles(o))


        
        
    #     speed = get_speed(self._last_vehicle_state) / 3.6  # m/s
    #     d_pr = speed * self.t_pr  # perception-reaction distance
    #     d_braking = speed ** 2 / (2 * self.u * self.g)  # braking distance
    #     d_total = max(d_pr + d_braking, 6)
    #     safe_distance_waypoints = [self._map.get_waypoint(self._last_vehicle_state.get_location(),
    #                                                       lane_type=carla.LaneType.Any)] + \
    #                               [w_d[0] for w_d in self._local_planner.get_next_waypoint_and_direction(
    #                                   int(d_total / self._sampling_resolution))]

    #     for path_wpt, vehicle in itertools.product(safe_distance_waypoints, projected_obstacles_list):
    #         vehicle_transform = vehicle.get_transform()
    #         vehicle_wpt = self._map.get_waypoint(vehicle_transform.location, lane_type=carla.LaneType.Any)
    #         if vehicle_wpt.road_id != path_wpt.road_id: continue
    #         distance = compute_distance(vehicle_transform.location, path_wpt.transform.location)
    #         print(f"distance with {vehicle} is: {distance}")
    #         if distance <= max_distance:
    #             return True, vehicle, distance

    #     return False, None, -1

    def getControlFromDecision(self, decision):
        if decision == Decision.SLOW_DOWN:
            print("slown down")
            return self.slow_down()
        elif decision == Decision.BREAK:
            print("slow stop")
            return self.slow_stop()
        elif decision == Decision.EMERGENCY_BREAK:
            print("emergency stop")
            return self.emergency_stop()

