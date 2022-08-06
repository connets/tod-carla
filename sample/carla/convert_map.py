import carla

f = open("documentation/towns/segrate_map.osm", 'r', encoding='utf-8')
osm_data = f.read()
f.close()

# Define the desired settings. In this case, default values.
vertex_distance = 2.0  # in meters
max_road_length = 500.0 # in meters
wall_height = 0.5      # in meters
extra_width = 0.6      # in meters

settings = carla.Osm2OdrSettings(wall_height=wall_height)
# Set OSM road types to export to OpenDRIVE
settings.set_osm_way_types(["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential"])
# Convert to .xodr
print(settings)
xodr_data = carla.Osm2Odr.convert(osm_data, settings)

# save opendrive file
f = open("documentation/towns/segrate_map.xodr", 'w')
f.write(xodr_data)
f.close()


