
import os
# os.chdir('D:\\Federico\\Mobility\\platform_mobility')
# os.getcwd()

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from geopandas import GeoDataFrame


import time
import datetime
import csv
import datetime as dt
from datetime import datetime
import math
import csv
import harvesine
import json
import osmnx as ox
import networkx as nx
import osmNw
import numpy as np
from pyproj import Proj, transform
from scipy import spatial


# data="20191213"
# data="20230405"
# path="D:/Federico/Mobility/platform_mobility/" + data +"/"
# path="D:/Federico/Mobility/platform_mobility/mycomponent_publictransport/gtfs_ROMA/"+data+'_RM/'
# graph_path='D:/Federico/Mobility/platform_mobility/mycomponent_publictransport/gtfs_ROMA/gtfs_osmnet/'


class PreCsa:

      """
      def __init__(self, pathname, graph_pathname, datefile):
        self.path = pathname
        self.date = datefile
        self.timetable=[]
        self.graph_path=graph_pathname
      """
      def __init__(self, pathname, graph_pathname, datefile):
        self.path = pathname
        self.date = datefile
        self.timetable=[]
        self.graph_path = graph_pathname


      # creazione della tabella timetable
      def create_timetable(self):
          service_id=dict() #dizionario dei service_id attivi
          trip_id=dict() #dizionario dei trip_id attivi associati al route_id
          timetab=[]
          timetable = []
          path = self.path
          # path='c:/Federico/gtfs_rm/'
          data = self.date
          dt = data + ' ' + '00:00:00'
          dt_obj = datetime.strptime(dt, '%Y%m%d %H:%M:%S')
          date_sec = datetime.timestamp(dt_obj)  # date in seconds, start time

          # read calendar_dates
          with open(self.path + "calendar_dates.txt", "r") as csv_file:
              csv_reader = csv.reader(csv_file, delimiter=',')
              # the below statement skips the first row
              next(csv_reader)
              for lines in csv_reader:
                  if lines[1]==self.date:
                     service_id[lines[0]]=True
              csv_file.close()

          # read trips
          with open(self.path + "trips.txt", "r") as csv_file:
              #route_id, service_id, trip_id,
              csv_reader = csv.reader(csv_file, delimiter=',')
              # the below statement will skip the first row
              next(csv_reader)
              for lines in csv_reader:
                  if lines[1] in service_id.keys():
                    trip_id[lines[2]]=lines[0]
              csv_file.close()

          # read stop_times
          with open(self.path + "stop_times.txt", "r") as csv_file:
              #trip_id, arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_dist_traveled,timepoint
              csv_reader = csv.reader(csv_file, delimiter=',')
              # the below statement will skip the first row
              next(csv_reader)
              for lines in csv_reader:
                  if lines[0] in trip_id.keys():
                    x = lines[1].split(":")
                    sec1=date_sec+int(x[0])*3600+int(x[1])*60+int(x[2])
                    y = lines[2].split(":")
                    sec2=date_sec+int(y[0])*3600+int(y[1])*60+int(y[2])
                    #print(trip_id.get(lines[0]),lines[0],lines[1], int(sec1), lines[2], int(sec2), lines[3],lines[4],lines[8])
                    if lines[8] == '':
                        timetab.append([str(trip_id.get(lines[0])), str(lines[0]), int(sec1), int(sec2), str(lines[3]), int(lines[4]), 0])
                    else:
                        timetab.append([str(trip_id.get(lines[0])), str(lines[0]), int(sec1), int(sec2), str(lines[3]),int(lines[4]), int(lines[8])])
              #print('timetable lenght: ', len(timetab))
              sorted_tt=sorted(timetab, key=lambda x: (x[0], x[1], x[2]))
              sorted_tt1=[]
              for i in range((len(sorted_tt)-1)):
                  #route_id, trip_id, stop_id, tostop_id, start_time, end_time, dist
                  if(sorted_tt[i][1]==sorted_tt[i+1][1]):
                    sorted_tt1.append([str(sorted_tt[i][0]), str(sorted_tt[i][1]), str(sorted_tt[i][4]), str(sorted_tt[i+1][4]), int(sorted_tt[i][3]), int(sorted_tt[i+1][2]), int((sorted_tt[i+1][6]-sorted_tt[i][6]))])
                    #print(sorted_tt[i][0], sorted_tt[i][1], sorted_tt[i][4], sorted_tt[i+1][4], sorted_tt[i][3], sorted_tt[i+1][2], (sorted_tt[i+1][6]-sorted_tt[i][6]))
              sorted_tt2=sorted(sorted_tt1, key=lambda x: (x[4]))
              print('timetable lenght: ', len(sorted_tt2))
              with open(path + data + '.csv', "w", newline="") as f:
                  writer = csv.writer(f)
                  writer.writerow(['route_id', 'trip_id', 'stop_id', 'tostop_id', 'start_time', 'end_time', 'dist'])
                  writer.writerows(sorted_tt2)
              csv_file.close()


############## create stopo-to-stop file with distance
      def create_walkNetstopToStopDistance(self, maxdist):
          #load walk_net
          print('loading graph....')
          fn = 'walknet_epgs4326.graphml'
          # b = osmNw.OsmNw(self.path_graph, fn)
          # G = b.load_walknet()
          G = ox.load_graphml('D:/Federico/Mobility/flask_app_2022/static/GTFS/gtfs_osmnet/walknet_epgs4326.graphml')
          # read stops
          inProj = Proj(init='epsg:4326')
          outProj = Proj(init='epsg:32633')
          outfile = open(self.path + "walknetstoptostop.txt", 'w')
          # outfile = open(path + "walknetstoptostop.txt", 'w')

          outfile.write("fromstop_id, fromstop_name, tostop_id, tostop_name, meters" + "\n")
          print('loading stops....')
          stops = self.path + "stops.txt";
          # stops = path + "stops.txt";
          fields = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
          dtype_dic = {'stop_id': str, 'stop_name': str, 'stop_lat': "float64", 'stop_lon': "float64"}
          stp = pd.read_csv(stops, usecols=fields, dtype=dtype_dic)
          stp['stop_id'] = stp['stop_id'].astype(str)
          stp['stop_name'] = stp['stop_name'].astype(str)
          stp['stop_lat'] = stp['stop_lat'].astype("float64")
          stp['stop_lon'] = stp['stop_lon'].astype("float64")
          liststoopcoo = stp.values.tolist()
          lat84 = stp['stop_lat'].values.tolist()
          lon84 = stp['stop_lon'].values.tolist()
          # myProj = Proj("+proj=utm +zone=33, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
          myProj = Proj('EPSG:32633')
          lon, lat = myProj(lon84, lat84)
          A = list(zip(lon, lat))
          kdtree = spatial.cKDTree(A)  # algorithm to optimize the calculation o nearest nodes
          for i in range(len(lon)):
              B = [lon[i], lat[i]]
              ix_list = kdtree.query_ball_point(B, maxdist)  # find the nodes within a fixed distance
              lon1 = "{:.6f}".format(liststoopcoo[i][3])
              lat1 = "{:.6f}".format(liststoopcoo[i][2])
              s1 = (float(lat1), float(lon1))
              orig_xy = s1
              from_n = ox.nearest_nodes(G, lon[i],lat[i], return_dist=False)
              for ix in ix_list:
                  dist = math.sqrt((lon[i] - lon[ix]) ** 2 + (lat[i] - lat[ix]) ** 2)
                  lon2 = "{:.6f}".format(liststoopcoo[ix][3])
                  lat2 = "{:.6f}".format(liststoopcoo[ix][2])
                  s2 = (float(lat2), float(lon2))
                  target_xy = s2
                  # to_n= ox.get_nearest_node(G, target_xy, method='euclidean', return_dist=False)
                  to_n = ox.nearest_nodes(G, float(lon2), float(lat2)  , return_dist=False)
                  dist_net = nx.dijkstra_path_length(G, from_n, to_n, weight='length')
                  if dist > dist_net: dist_net = dist
                  #print(liststoopcoo[i][0] + "," + liststoopcoo[i][1] + "," + liststoopcoo[ix][0] + "," + liststoopcoo[ix][1] + "," + str(int(dist))+","+str(int(dist_net)))
                  outfile.write(liststoopcoo[i][0] + "," + liststoopcoo[i][1] + "," + liststoopcoo[ix][0] + "," + liststoopcoo[ix][1] + "," + str(int(dist_net)) + "\n")
              print(liststoopcoo[i][0], '-', liststoopcoo[i][1])
          outfile.close()

############## create stopo-to-stop file with distance
      def create_stopToStopDistance(self, maxdist):
          # read stops
          print('loading stops....')
          inProj = Proj(init='epsg:4326')
          outProj = Proj(init='epsg:32633')
          outfile = open(self.path+"stoptostop.txt", 'w')
          outfile.write("fromstop_id, fromstop_name, tostop_id, tostop_name, meters" + "\n")
          print('loading stops....')
          stops = self.path + "stops.txt";
          fields = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
          dtype_dic = {'stop_id': str, 'stop_name': str, 'stop_lat': "float64", 'stop_lon': "float64"}
          stp = pd.read_csv(stops, usecols=fields, dtype=dtype_dic)
          stp['stop_id'] = stp['stop_id'].astype(str)
          stp['stop_name'] = stp['stop_name'].astype(str)
          stp['stop_lat'] = stp['stop_lat'].astype("float64")
          stp['stop_lon'] = stp['stop_lon'].astype("float64")
          liststoopcoo = stp.values.tolist()
          lat84 = stp['stop_lat'].values.tolist()
          lon84 = stp['stop_lon'].values.tolist()
          # myProj = Proj("+proj=utm +zone=33, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
          myProj = Proj('EPSG:32633')
          lon, lat = myProj(lon84, lat84)
          A = list(zip(lon, lat))
          kdtree = spatial.cKDTree(A)  # algorithm to optimize the calculation o nearest nodes
          for i in range(len(lon)):
              B = [lon[i], lat[i]]
              ix_list = kdtree.query_ball_point(B, maxdist)  # find the nodes within a fixed distance
              for ix in ix_list:
                  dist = math.sqrt((lon[i] - lon[ix]) ** 2 + (lat[i] - lat[ix]) ** 2)
                  # st=print(liststoopcoo[i][0],liststoopcoo[i][1],liststoopcoo[ix][0], liststoopcoo[ix][1], int(dist))
                  outfile.write(liststoopcoo[i][0] + "," + liststoopcoo[i][1] + "," + liststoopcoo[ix][0] + "," +
                                liststoopcoo[ix][1] + "," + str(int(dist)) + "\n")
              print(liststoopcoo[i][0], '-', liststoopcoo[i][1])
          outfile.close()


"""
body=PreCsa(path , graph_path, data)
# ----> a.path_graph=graph_path
body.create_timetable()


## load stop.times.txt from GTFS data
timetable_full = pd.read_csv("D:/Federico/Mobility/platform_mobility/mycomponent_publictransport/gtfs_ROMA/"+data+'_RM/'+ data + '.csv')
## sort data by time
timetable_full = timetable_full.sort_values(by=['start_time'])
## get a give bunch of data....


dt = data + ' ' + '00:00:00'
dt_obj = datetime.strptime(dt, '%Y%m%d %H:%M:%S')
date_sec = datetime.timestamp(dt_obj)
hh = '11'
mm = '00'
ss = '00'
time_limit = date_sec+int(hh)*3600+int(mm)*60+int(ss)


AAA = timetable_full[timetable_full['start_time'] < time_limit]
AAA.to_csv("mycomponent_publictransport/gtfs_ROMA/"+data+'_RM/'+ data + '.csv')
"""