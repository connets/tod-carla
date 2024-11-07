# 0 	Unlabeled 	(0, 0, 0) 	Elements that have not been categorized are considered Unlabeled. This category is meant to be empty or at least contain elements with no collisions.
# 1 	Roads 	(128, 64, 128) 	Part of ground on which cars usually drive.
# E.g. lanes in any directions, and streets.
# 2 	SideWalks 	(244, 35, 232) 	Part of ground designated for pedestrians or cyclists. Delimited from the road by some obstacle (such as curbs or poles), not only by markings. This label includes a possibly delimiting curb, traffic islands (the walkable part), and pedestrian zones.
# 3 	Building 	(70, 70, 70) 	Buildings like houses, skyscrapers,... and the elements attached to them.
# E.g. air conditioners, scaffolding, awning or ladders and much more.
# 4 	Wall 	(102, 102, 156) 	Individual standing walls. Not part of a building.
# 5 	Fence 	(190, 153, 153) 	Barriers, railing, or other upright structures. Basically wood or wire assemblies that enclose an area of ground.
# 6 	Pole 	(153, 153, 153) 	Small mainly vertically oriented pole. If the pole has a horizontal part (often for traffic light poles) this is also considered pole.
# E.g. sign pole, traffic light poles.
# 7 	TrafficLight 	(250, 170, 30) 	Traffic light boxes without their poles.
# 8 	TrafficSign 	(220, 220, 0) 	Signs installed by the state/city authority, usually for traffic regulation. This category does not include the poles where signs are attached to.
# E.g. traffic- signs, parking signs, direction signs...
# 9 	Vegetation 	(107, 142, 35) 	Trees, hedges, all kinds of vertical vegetation. Ground-level vegetation is considered Terrain.
# 10 	Terrain 	(152, 251, 152) 	Grass, ground-level vegetation, soil or sand. These areas are not meant to be driven on. This label includes a possibly delimiting curb.
# 11 	Sky 	(70, 130, 180) 	Open sky. Includes clouds and the sun.
# 12 	Pedestrian 	(220, 20, 60) 	Humans that walk
# 13 	Rider 	(255, 0, 0) 	Humans that ride/drive any kind of vehicle or mobility system
# E.g. bicycles or scooters, skateboards, horses, roller-blades, wheel-chairs, etc. .
# 14 	Car 	(0, 0, 142) 	Cars, vans
# 15 	Truck 	(0, 0, 70) 	Trucks
# 16 	Bus 	(0, 60, 100) 	Busses
# 17 	Train 	(0, 80, 100) 	Trains
# 18 	Motorcycle 	(0, 0, 230) 	Motorcycle, Motorbike
# 19 	Bicycle 	(119, 11, 32) 	Bicylces
# 20 	Static 	(110, 190, 160) 	Elements in the scene and props that are immovable.
# E.g. fire hydrants, fixed benches, fountains, bus stops, etc.
# 21 	Dynamic 	(170, 120, 50) 	Elements whose position is susceptible to change over time.
# E.g. Movable trash bins, buggies, bags, wheelchairs, animals, etc.
# 22 	Other 	(55, 90, 80) 	Everything that does not belong to any other category.
# 23 	Water 	(45, 60, 150) 	Horizontal water surfaces.
# E.g. Lakes, sea, rivers.
# 24 	RoadLine 	(157, 234, 50) 	The markings on the road.
# 25 	Ground 	(81, 0, 81) 	Any horizontal ground-level structures that does not match any other category. For example areas shared by vehicles and pedestrians, or flat roundabouts delimited from the road by a curb.
# 26 	Bridge 	(150, 100, 100) 	Only the structure of the bridge. Fences, people, vehicles, an other elements on top of it are labeled separately.
# 27 	RailTrack 	(230, 150, 140) 	All kind of rail tracks that are non-drivable by cars.
# E.g. subway and train rail tracks.
# 28 	GuardRail 	(180, 165, 180) 	All types of guard rails/crash barriers.
import carla
from enum import Enum

Semantic_types = {
    0: "Unlabeled",
    1: "Roads",
    2: "SideWalks",
    3: "Building",
    4: "Wall",
    5: "Fence",
    6: "Pole",
    7: "TrafficLight",
    8: "TrafficSign",
    9: "Vegetation",
    10: "Terrain",
    11: "Sky",
    12: "Pedestrian",
    13: "Rider",
    14: "Car",
    15: "Truck",
    16: "Bus",
    17: "Train",
    18: "Motorcycle",
    19: "Bicycle",
    20: "Static",
    21: "Dynamic",
    22: "Other",
    23: "Water",
    24: "RoadLine",
    25: "Ground",
    26: "Bridge",
    27: "RailTrack",
    28: "GuardRail",
}

class SensorPosition(Enum):
    Up = 0
    Front = 1
    FrontRight = 2
    FrontLeft = 3
    Back = 4
    BackLeft = 5
    BackRight = 6

def getCarlaRelativeLocation(boundingBox, sensor_position: SensorPosition) -> carla.Location:

    x=0
    y=0
    z=0

    if sensor_position == SensorPosition.Up:
        z = 1
    if sensor_position == SensorPosition.Front:
        x, y = 1, 0
    elif sensor_position == SensorPosition.FrontRight:
        x, y = 1, 1
    elif sensor_position == SensorPosition.FrontLeft:
        x, y = 1, -1
    elif sensor_position == SensorPosition.Back:
        x, y = -1, 0
    elif sensor_position == SensorPosition.BackRight:
        x, y = -1, 1
    elif sensor_position == SensorPosition.BackLeft:
        x, y = -1, -1

    return carla.Location(x=boundingBox.extent.x * x, y=boundingBox.extent.y * y, z=boundingBox.extent.z * z)

