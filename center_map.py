
from geopy.geocoders import Nominatim
import numpy as np
import networkx as nx
import osmnx as ox


## function to get the background map centered over a given location
def center():
    address = str('Roma' + ', IT')
    geolocator = Nominatim(user_agent="id_explorer")
    location = geolocator.geocode(address)
    latitude = location.latitude
    longitude = location.longitude
    return latitude, longitude

## function to get the latitude & longitude
## defne a function to return the LATITUDE - LONGITUDE of a selected point
def get_pos(lat,lng):
    return lat,lng


# define distance between two coordinates (in meters)
def haversine(coord1, coord2):
    # Coordinates in decimal degrees (e.g. 43.60, -79.49)
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371000  # radius of Earth in meters
    phi_1 = np.radians(lat1)
    phi_2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi_1) * np.cos(phi_2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    meters = R * c  # output distance in meters
    km = meters / 1000.0  # output distance in kilometers
    meters = round(meters)
    km = round(km, 3)
    # print(f"Distance: {meters} m")
    # print(f"Distance: {km} km")
    return meters



####################################################
# assign weight and cost (time) to the grapho ######
# weight/cost assignment ###########################
####################################################
def cost_assignment(grafo):
# def cost_assignment(file_graphml, place_country):
    # these numbers are the speeds on different type of road
    # grafo = ox.load_graphml(file_graphml)
    way_dict = {
        "residential": [30, 50, 10],
        "secondary": [40, 90, 30],
        "primary": [50, 70, 20],
        "tertiary": [35, 70, 10],
        "unclassified": [40, 60, 10],
        "secondary_link": [40, 55, 30],
        "trunk": [70, 90, 40],
        "tertiary_link": [35, 50, 30],
        "primary_link": [50, 90, 40],
        "motorway_link": [80, 100, 30],
        "trunk_link": [42, 70, 40],
        "motorway": [110, 130, 40],
        "living_street": [20, 50, 30],
        "road": [30, 30, 30],
        "other": [30, 30, 30]
    }
    # weight/cost assignment
    # u and v are the start and ending point of each edge (== arco).
    for u, v, key, attr in grafo.edges(keys=True, data=True):
        # print(attr["highway"])
        # select first way type from list
        if type(attr["highway"]) is list:
            # verify if the attribute field is a list (it might happen)
            attr["highway"] = str(attr["highway"][0])  # first element of the list
            # print(attr["highway"], '=================')
        # verify if the attribute exists, the way type in the dictionary
        if attr["highway"] not in way_dict.keys():
            speedlist = way_dict.get("other")
            speed = speedlist[0] * 1000 / 3600
            # create a new attribute time == "cost" in the field "highway"
            attr['cost'] = attr.get("length") / speed
            # print(attr.get("highway"), speedlist[0], attr.get("cost"), '^^^^^^^^^^^')
            # add the "attr_dict" to the edge file
            grafo.add_edge(u, v, key, attr_dict=attr)
            continue

        if 'maxspeed' in set(attr.keys()) and len(attr.get("maxspeed")) < 4:
            if type(attr.get("maxspeed")) is list:
                speedList = [int(i) for i in attr.get("maxspeed")]
                speed = np.mean(speedList) * 1000 / 3600
                attr['cost'] = attr.get("length") / speed
                # print(attr.get("highway"), attr.get("maxspeed"), attr.get("cost"), '========')
            else:
                speed = float(attr.get("maxspeed")) * 1000 / 3600
                attr['cost'] = attr.get("length") / speed
                # print(attr.get("highway"), attr.get("maxspeed"), attr.get("cost"), '°°°°°°°°°')
            grafo.add_edge(u, v, key, attr_dict=attr)
        else:  # read speed from way class dictionary
            speedlist = way_dict.get(attr["highway"])
            speed = speedlist[0] * 1000 / 3600
            attr['cost'] = attr.get("length") / speed
            # print(attr.get("highway"), speedlist[0], attr.get("cost"), '-----------')
            grafo.add_edge(u, v, key, attr_dict=attr)
            # when I save, the field "cost" becomes a string...wrong!


