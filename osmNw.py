
import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.cm as cm
import geopandas
import json
from datetime import datetime

class OsmNw:
      def __init__(self, pathname, filename):
        self.path = pathname
        self.fn = filename

      def import_walknet(self):
          print('importing walk graph...')
          G = ox.graph_from_place('Rome, Italy', network_type='walk')
          #RMWalkNet_nodes_proj, RMWalkNet_edges_proj = ox.graph_to_gdfs(G, nodes=True, edges=True)
          #print(type(RMWalkNet_nodes_proj))
          #RMWalkNet_nodes_proj.to_file("RMWalkNet_nodes_proj.geojson", driver='GeoJSON')
          #RMWalkNet_edges_proj.to_file("RMWalkNet_edges_proj.geojson", driver='GeoJSON')

          # ox.plot_graph(G)
          # using NetworkX to calculate the shortest path between two random nodes

          # route = nx.shortest_path(G, np.random.choice(G.nodes),np.random.choice(G.nodes))
          # ox.plot_graph_route(G, route, fig_height=10, fig_width=10)
          # G_projected = ox.project_graph(G)
          # save street network as GraphML file
          # ox.save_graphml(G_projected, filename='networkRM.graphml')
          # save street network as ESRI shapefile
          # ox.save_graph_shapefile(G_projected, filename='networkLazio-shape')

          # street network from bounding box
          # G = ox.graph_from_bbox(42.2511, 41.3860, 11.6586, 13.4578, network_type='drive_service')

          # G=ox.graph_from_address('Rome, Italy',distance=60000,network_type='drive')
          # G_projected = ox.project_graph(G)
          #ox.plot_graph(G)
          ox.save_graphml(G, filename=self.fn, folder=self.path)
          # street network from lat-long point
          # This gets the street network within 0.75 km (along the network) of a latitude-longitude point:
          # G = ox.graph_from_point((37.79, -122.41), distance=750, network_type='all')
          # ox.plot_graph(G)

      def load_walknet(self):
          # load Graph
          G = ox.load_graphml('D:/Federico/Mobility/flask_app_2022/static/GTFS/gtfs_osmnet/walknet_epgs4326.graphml')
          # G = ox.load_graphml(filename=self.fn, folder=self.path)
          return G
          '''
          Y=[41.868177]
          X=[12.518942]
          print(type(X))
          ne3 = ox.get_nearest_edges(G, X, Y, method='kdtree', dist=0.001)
          print(ne3)
         
          print(now1 - now)
          nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
          print(nodes.columns)
          print(edges.columns)
          
          nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
          print(nodes.columns)
          print(edges.columns)
          edges.to_csv('RM_walk_edges_proj'+'.csv')
          nodes.to_csv('RM_walk_nodes_proj'+'.csv')
          nodes.to_file("nodes_proj.json", driver='GeoJSON')
          edges.to_file("edges_proj.json", driver='GeoJSON')
          '''


'''
fld='/Users/gaeval/Documents/sw/gtfs_osmnet/'
fn='walknetworkRM_epgs4326.graphml'
b=OsmNw(fld,fn)
G=b.load_walknet()

#from_n = np.random.choice(G.nodes)
#to_n = np.random.choice(G.nodes)
now = datetime.now()
orig_xy = (41.868362, 12.518942)
target_xy = (41.874781, 12.522694)
from_n, distance_from = ox.get_nearest_node(G, orig_xy, method='euclidean', return_dist=True)
to_n, distance_to = ox.get_nearest_node(G, target_xy, method='euclidean', return_dist=True)
route = nx.shortest_path(G, from_n, to_n, weight='length')
lr = nx.shortest_path_length(G, from_n, to_n, weight='length')
#print(lr, distance_from, distance_to)
now1 = datetime.now()
print(now1-now)
print(route)

now = datetime.now()
# G = ox.project_graph(G, to_crs={'init': 'epsg:32632'})
# G2 = nx.Graph(G1)
          
path_edges = list(zip(route, route[1:]))
lunghezza = []
# route_length_km = sum([G2.edge[u][v][0]['length'] for u, v in zip(route, route[1:])]) / 1000.
for l in path_edges:
  lunghezza.append(G[l[0]][l[1]][0]['length'])
print("km:{0:.3f} h:{1:.3f} vm:{2:.0f}".format(sum(lunghezza) / 1000, lr / 3600, sum(lunghezza) / 1000 / lr * 3600))
route1 = nx.dijkstra_path(G, from_n, to_n, weight='length')
lr1 = nx.dijkstra_path_length(G, from_n, to_n, weight='length')
# route2 = nx.astar_path(G2,from_n,to_n,weight='length')
# lr2=nx.astar_path_length(G2, from_n,to_n,weight='length')
ox.plot_graph_route(G, route, route_color='green', fig_height=12, fig_width=12)
# ox.plot_route_folium(G2, route, route_color='green')
# print(len(route), type(G2))

# print(G2[265551871])
# print( G2[265551871][32630067])
# print(G2.size(weight='length'), G2.number_of_edges(), G2.number_of_nodes())

# print(lr, lr1)
# save street network as ESRI shapefile
ox.save_graph_shapefile(G, filename='networkCT42Km-shape')
'''
