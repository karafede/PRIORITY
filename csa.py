
import os
path_app = os.getcwd() + "/"

import datetime as dt
import pandas as pd
from datetime import datetime

import harvesine
from geopandas import GeoDataFrame
import geopandas as gpd
import json
import folium
import random
import math
import csv
from shapely.geometry import LineString
from shapely.geometry import Point, Polygon
import osmnx as ox
import networkx as nx
import haversine as hs
from haversine import Unit


class Csa:
  def __init__(self, pathname, datefile):
    self.path = pathname
    self.date = datefile
    self.stopfile='stoptostop.txt'
    self.walknetstopfile='walknetstoptostop.txt'
    self.timetable=[]
    self.timetableCol=[]
    self.stp_dict = dict()
    self.stp_name = dict()
    self.footpathspeed = 1.0  # m/s
    self.stop_coo = []
    self.lin = 1.2
    self.transferTime=90
    self.adjList = dict()   #adj list of footpath between stops
    self.leg=dict()
    self.start_dt_sec=0.0
    self.lin1st = 1.3
    self.maxFootDistance = 800
    self.timetablemaxtime=3600*6
    self.shdict=dict()
    self.flag=True
    #OUTPUT#####################################################################
    self.distance=-1
    self.travel_time=-1
    self.travel_speed=-1
    self.walking_distance=-1
    self.transfer=-1
    self.waiting_time=-1

  def load_timetable(self):
      fields = ['route_id', 'trip_id', 'stop_id', 'start_time', 'tostop_id', 'end_time', 'dist']
      dtype_dic = {'route_id': str, 'trip_id': str, 'stop_id': str, 'start_time': "float64", 'tostop_id': str,
                   'end_time': "float64", 'dist': "float64"}
      connections = pd.read_csv(self.path + self.date + '.csv', usecols=fields, dtype=dtype_dic)
      # connections = pd.read_csv("D:/Federico/Mobility/flask_app_2022/static/GTFS/20230123/20230123.csv", usecols=fields, dtype=dtype_dic)
      # From partial dataframe to list 2D
      connections = connections.sort_values(['start_time'])
      #connections.sort_values(['start_time'], inplace=True)
      self.timetableCol = list(connections.columns)
      # print(colindex.index("route_id"))
      self.timetable = connections.values.tolist()
      print('timetable lenght: ', len(self.timetable))
      del(connections)
      print("---- I am here: TIMETABLE----------")


  def load_stops(self):
      ####Loading STOPS and create STOPS Dictionary#########################################
      stops = self.path + "stops.txt"
      fields = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']
      # 'stop_lat', 'stop_lon'
      dtype_dic = {'stop_id': str, 'stop_name': str, 'stop_lat': 'float', 'stop_lon': 'float'}
      stp = pd.read_csv(stops, usecols=fields, dtype=dtype_dic)
      stop = stp["stop_id"].tolist()
      stop__name = stp["stop_name"].tolist()
      stop_lat = stp["stop_lat"].tolist()
      stop_lon = stp["stop_lon"].tolist()
      # list of  infinite
      a = [math.inf for x in range(len(stop))]
      # create dictionary for stops
      self.stp_dict = dict(zip(stop, a))
      self.stp_name = dict(zip(stop, stop__name))
      # select two columns
      self.stop_coo = []
      for i in range(len(stop)):
          self.stop_coo.append([stop[i], stop_lat[i], stop_lon[i]])
      del (stp)
      del stop, stop__name, stop_lat, stop_lon
      print("---- I am here: STOPS----------")



  def load_stopsfootpath(self):
       #Loading foot link #########################################
       with open(self.path + self.stopfile, 'r') as file:
           reader = csv.reader(file, delimiter=',')
           next(reader)
           for row in reader:
               if str(row[0]) in self.adjList.keys():
                   new_list = []
                   new_list = self.adjList.get(str(row[0]))
                   new_list.append([str(row[2]), self.lin * float(row[4]) / self.footpathspeed])
                   self.adjList[str(row[0])] = new_list
                   # print("value =", adjList.get(str(row[0])))
               else:
                   alist = []
                   alist.append([str(row[2]), self.lin * float(row[4]) / self.footpathspeed])
                   self.adjList[str(row[0])] = alist
       del (reader)
       print("---- I am here: stops to footpaths -----------")
       ########################################################################################

  def load_walknetstopsfootpath(self):
       #Loading foot link #########################################
       with open(self.path + self.walknetstopfile, 'r') as file:
           reader = csv.reader(file, delimiter=',')
           next(reader)
           for row in reader:
               if str(row[0]) in self.adjList.keys():
                   new_list = []
                   new_list = self.adjList.get(str(row[0]))
                   new_list.append([str(row[2]), self.lin * float(row[4]) / self.footpathspeed])
                   self.adjList[str(row[0])] = new_list
                   # print("value =", adjList.get(str(row[0])))
               else:
                   alist = []
                   alist.append([str(row[2]), self.lin * float(row[4]) / self.footpathspeed])
                   self.adjList[str(row[0])] = alist
       del (reader)
       print("---- I am here: footh paths ----------")
       # print("--- udjusted list of stops consdering footpaths distances---->>>:", self.adjList)
       ########################################################################################

  def load_shapeStopStop(self):
      shdict = dict()
      with open(self.path + self.date + '_shape.json') as json_file:
          self.shdict = json.load(json_file)


  def run(self,stloc, enloc, stime):
      startLocation=stloc
      endLocation=enloc
      s_time=stime
      stop_dict=self.stp_dict
      self.leg = dict()
      endleg = dict()
      routeid = self.timetableCol.index("route_id")
      tripid = self.timetableCol.index("trip_id")
      stopid = self.timetableCol.index("stop_id")
      tostopid = self.timetableCol.index("tostop_id")
      starttime = self.timetableCol.index("start_time")
      endtime = self.timetableCol.index("end_time")
      dist = self.timetableCol.index("dist")
      ##time: from string to second
      start_dt = self.date + ' ' + s_time
      dt_obj = datetime.strptime(start_dt, '%Y%m%d %H:%M:%S')
      self.start_dt_sec = datetime.timestamp(dt_obj)
      #end_dt_sec = self.start_dt_sec + (3600 * 4)
      print('start_time', datetime.fromtimestamp(self.start_dt_sec).strftime("%H:%M:%S"))
      #print('max_time', datetime.fromtimestamp(end_dt_sec).strftime("%H:%M:%S"))
      # create foot link from start location to adj stops and from adj location to end location#######################
      p_stop_id = str(startLocation[0]) + '_' + str(startLocation[1])
      a_stop_id = str(endLocation[0]) + '_' + str(endLocation[1])
      stop_dict[p_stop_id] = self.start_dt_sec
      stop_dict[a_stop_id] = math.inf
      startCounter = 0  # counter of walkpath at the starting point
      endCounter = 0  # counter of walkpath at the ending point
      for i in range(len(self.stop_coo)):

          startfootpathmeter = (
              harvesine.meter_distance(startLocation[0], startLocation[1], self.stop_coo[i][1], self.stop_coo[i][2]))
          # print(startfootpathmeter)
          if startfootpathmeter <= self.maxFootDistance:
              # print("----gotta!!!----")
              startCounter += 1
              walktimeinsec = int(self.lin1st * startfootpathmeter / self.footpathspeed)
              rowstart = ['1fp', 'footpath', p_stop_id, 'start_foot', self.stop_coo[i][0], self.stp_name.get(self.stop_coo[i][0]),
                           datetime.fromtimestamp(self.start_dt_sec).strftime("%H:%M:%S"),
                           datetime.fromtimestamp(self.start_dt_sec + walktimeinsec).strftime("%H:%M:%S"),
                           self.start_dt_sec, self.start_dt_sec + walktimeinsec, int(walktimeinsec * self.footpathspeed / self.lin1st)]

              stop_dict[self.stop_coo[i][0]] = self.start_dt_sec + walktimeinsec
              self.leg[self.stop_coo[i][0]] = rowstart
              #startleg[self.stop_coo[i][0]] = self.start_dt_sec + walktimeinsec
              #  print("leg:", self.leg)
          endfootpathmeter = (harvesine.meter_distance(endLocation[0], endLocation[1], self.stop_coo[i][1], self.stop_coo[i][2]))
          if endfootpathmeter <= self.maxFootDistance:
              # print("----gotta!!!----")
              endCounter += 1
              walktimeinsec = int(self.lin1st * endfootpathmeter / self.footpathspeed)
              endleg[self.stop_coo[i][0]] = walktimeinsec
              # print("endleg.keys():", endleg.keys())


      if (startCounter == 0 or endCounter == 0): print('missing footpath from start or to end')
      if (startCounter == 0 or endCounter == 0):
          self.flag=False
      else:
          self.flag=True
      # print("legga:", self.leg)
      #######################################################################################################

      for idx, val in enumerate(self.timetable):
          # print("endleg keys", endleg.keys())
          # print("val[tostopid]:", val[tostopid])
          # max time before stopping connections scan
          if val[starttime] >= self.start_dt_sec + self.timetablemaxtime:
              break  # algorithm is finished for time limit
          transferT = 0
          if (self.leg.get(val[stopid]) is not None):
              if self.leg.get(val[stopid])[1]==val[tripid]:  #####transfer time penalty
                  transferT = 0
              elif self.leg.get(val[stopid])[1]=='footpath':
                  transferT = 60
              else:
                  transferT = self.transferTime  #####################transfer time penalty

          if (float(stop_dict.get(val[stopid])) + transferT <= (val[starttime])):
              if val[endtime] < stop_dict.get(val[tostopid]):
                  row = [val[routeid], val[tripid], val[stopid], self.stp_name.get(val[stopid]), val[tostopid],
                         self.stp_name.get(val[tostopid]),
                         datetime.fromtimestamp(val[starttime]).strftime("%H:%M:%S"),
                         datetime.fromtimestamp(val[endtime]).strftime("%H:%M:%S"), val[starttime], val[endtime],
                         val[dist]]

                  stop_dict[val[tostopid]] = val[endtime]
                  self.leg[val[tostopid]] = row

                  ####adding footpath to end
                  if val[tostopid] in endleg.keys():  # adj last stop to final coo
                      # print("endleg keys", endleg.keys())
                      # print("val[tostopid]:", val[tostopid])
                      # print("----gotta")
                      lastrow = ['lastfp', 'footpath', val[tostopid], self.stp_name.get(val[tostopid]), a_stop_id,
                                 'end_tripp',
                                 datetime.fromtimestamp(val[endtime]).strftime("%H:%M:%S"),
                                 datetime.fromtimestamp(val[endtime] + endleg.get(val[tostopid])).strftime(
                                     "%H:%M:%S"),
                                 val[endtime], val[endtime] + endleg.get(val[tostopid]),
                                 int((endleg.get(val[tostopid])) * self.footpathspeed / self.lin1st)]
                      # print("---gotta--------", lastrow)
                      if (val[endtime] + endleg.get(val[tostopid])) < stop_dict.get(a_stop_id):
                          stop_dict[a_stop_id] = val[endtime] + endleg.get(val[tostopid])
                          self.leg[a_stop_id] = lastrow
                      # print("---gotta--------", lastrow)

                  else:
                  # adding footpath between tostop and adjacent stops
                      s = []
                      s = self.adjList.get(val[tostopid])
                      if s is not None:
                          for i in range(len(s)):
                              if stop_dict.get(str(s[i][0])) is not None:
                                  if str(s[i][0]) != val[stopid]:
                                      if (val[endtime] + float(s[i][1])) < stop_dict.get(str(s[i][0])):
                                          stop_dict[str(s[i][0])] = val[endtime] + float(s[i][1])
                                          row1 = ['fp', 'footpath', val[tostopid], self.stp_name.get(val[tostopid]),
                                                  str(s[i][0]),
                                                  self.stp_name.get(str(s[i][0])),
                                                  datetime.fromtimestamp(val[endtime]).strftime("%H:%M:%S"),
                                                  datetime.fromtimestamp(val[endtime] + float(s[i][1])).strftime(
                                                      "%H:%M:%S"),
                                                  val[endtime], (val[endtime] + float(s[i][1])),
                                                  int(float(s[i][1]) * self.footpathspeed / self.lin)]
                                          self.leg[str(s[i][0])] = row1




  def showMapPath(self, startLocation, endLocation):
      #### Set up map ##########
      base_map = folium.Map(location=startLocation, tiles='OpenStreetMap', zoom_start=10, opacity=1)
      folium.Marker(startLocation,popup=' Geeksforgeeks.org ', icon=folium.Icon(color='red', icon='flag')).add_to(base_map)
      folium.CircleMarker(location=endLocation, radius=5 ,popup='The Waterfront', color='blue', fill=False).add_to(base_map)
      #########################
      p_stop_id = str(startLocation[0]) + '_' + str(startLocation[1])
      a_stop_id = str(endLocation[0]) + '_' + str(endLocation[1])
      # print("p_stop_id:", p_stop_id)
      # print("a_stop_id:", a_stop_id)
      # print(self.leg)
      i = a_stop_id
      legList = []
      while i != p_stop_id:
          try:
              s = self.leg.get(i)
              i = str(s[2])  ## <<<<<<<<--------------
              legList.append(s)
          except TypeError:
              print("legList:",  legList)
              print("### TPL line NOT AVAILABLE")
              break
      legList.reverse()
      progressive = 0.0
      walking_distance = 0
      change = 0
      waitingTime = 0
      lineid = ' '

      ### initialize an empty dataframe for the final timetable
      timetable = pd.DataFrame([])

      for i in range(len(legList)):
          if str(legList[i][1]) == 'footpath':
              walking_distance += legList[i][10]
              progressive += legList[i][10]
              print(legList[i], "{:.0f}".format(progressive), change, int(waitingTime / 60),
                    int((legList[i][9] - self.start_dt_sec) / 60))

              ######----------->>>> WALKING
              timetable_sub = pd.DataFrame({
                  'line_number': [legList[i][0]],
                  'trip_id': [legList[i][1]],
                  'stop1_code': [legList[i][2]],
                  'start': [legList[i][3]],
                  'stop2_code': [legList[i][4]],
                  'stop': [legList[i][5]],
                  'start_time': [legList[i][6]],
                  'end_time': [legList[i][7]],
                  'distance(m)': [legList[i][10]]
              })
              timetable = pd.concat([timetable, timetable_sub])


          else:
              if i != 0:
                  if lineid != str(legList[i][0]):
                      change += 1
                      if str(legList[i - 1][1]) == 'footpath':
                          waitingTime += (legList[i][8] - legList[i - 1][9])
                      lineid = str(legList[i][0])

                  print(legList[i], change,
                        int(waitingTime / 60), int((legList[i][9] - self.start_dt_sec) / 60))
                  #st.markdown("### I am here----------------------------------------------------------")

                  timetable_sub = pd.DataFrame({
                      'line_number': [legList[i][0]],
                      'trip_id': [legList[i][1]],
                      'stop1_code': [legList[i][2]],
                      'start': [legList[i][3]],
                      'stop2_code': [legList[i][4]],
                      'stop': [legList[i][5]],
                      'start_time': [legList[i][6]],
                      'end_time': [legList[i][7]],
                      'distance(m)': [legList[i][10]]
                  })
                  timetable = pd.concat([timetable, timetable_sub])
      timetable_show = timetable[['line_number', 'start', 'stop', 'start_time', 'end_time', 'distance(m)']]
      timetable.to_csv(path_app + '/static/final_timetable.csv')

      TRAVEL_TIME = round(int((legList[len(legList) - 1][9] - self.start_dt_sec) / 60), 1)
      TRAVEL_SPEED = int(progressive / 1000 / ((legList[len(legList) - 1][9] - legList[0][8]) / 3600))
      WALKING_DISTANCE = round(walking_distance, 2)
      TRANSFERS = change - 1
      WAITING_TIME = waitingTime

      return TRAVEL_TIME , TRAVEL_SPEED , WALKING_DISTANCE, TRANSFERS, WAITING_TIME



################-------------------------------------------------------------------------------------------------####################
#####################################################################################################################################
#####################################################################################################################################



