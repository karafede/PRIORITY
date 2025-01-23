

import os

os.environ["PYTHONIOENCODING"] = "utf-8"
path_app = os.getcwd() + "/"

import pandas as pd
import geopandas as gpd
import folium
import db_connect
import numpy as np
from shapely.geometry import Point, Polygon
from geopandas import GeoDataFrame
from shapely import wkb
from osgeo import ogr
import sqlalchemy as sal
from sqlalchemy.pool import NullPool
import fiona
from shapely.geometry import shape
import re
from flask import request
import osmnx as ox
ox.config(log_console=True, use_cache=True)
import datetime as dt
import pandas as pd
from datetime import datetime
import harvesine
from geopandas import GeoDataFrame
import geopandas as gpd
import streamlit as st
import json
# import preprocessCsa
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
import requests
import datetime
from os import listdir

import pyproj

proj_data_dir = pyproj.datadir.get_data_dir()


# Function to generate WKB hex
def wkb_hexer(line):
    return line.wkb_hex


## function to transform Geometry from text to LINESTRING
def wkb_tranformation(line):
    return wkb.loads(line.geometry, hex=True)


################################################################
################################################################
################################################################
################################################################
################################################################
################################################################


#### use flask to launch the html file##########################
from flask import Flask, render_template, request, render_template_string, make_response, abort, jsonify, redirect, \
    session
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

import uuid
app.config['SECRET_KEY'] = 'karafede75'


# img_dict = {}


## https://www.digitalocean.com/community/tutorials/how-to-handle-errors-in-a-flask-application
## ---- handle ERRORS ------ #####################################################################

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_404_page.html'), 404  # 404.html


@app.route('/')
def root():
    longitude = request.args.get('lng', type=float)
    latitude = request.args.get('latitude', type=float)
    print("latitude--->: ", latitude)
    print("longitude--->: ", longitude)
    markers = [
        {
            'lat': longitude,
            'lon': latitude,
            'popup': 'user input pnt.'
        }
    ]
    print(markers)
    return render_template("index.html", longitude=longitude, latitude=latitude)


@app.route('/my-link/')
def my_link():
    ### generate .geojson file for home locations...
    all_locations_ROMA = pd.read_sql_query('''
                               SELECT *
                                  FROM "idterm_Info_FK"    
                                  limit 1000
                                  ''', conn_HAIG)

    all_locations_ROMA = all_locations_ROMA[all_locations_ROMA['Trans_Confine'] == 0]
    all_locations_ROMA = all_locations_ROMA[all_locations_ROMA['Notti_Out'] == 0]
    # all_locations_ROMA = all_locations_ROMA[all_locations_ROMA['N_Giorni_Pres'] > 7]
    all_locations_ROMA.drop_duplicates(['Id_Term'], inplace=True)
    home_locations = all_locations_ROMA[['Id_Term', 'Coord_1_Casa']]

    lats_home = []
    lons_home = []
    Id_Term = []
    for i in range(len(home_locations)):
        print(i)
        print(home_locations.iloc[i])
        if ((home_locations.iloc[i].Coord_1_Casa != '{0,0}') and (home_locations.iloc[i].Coord_1_Casa != '{-1,-1}')):
            latitude = (re.split('; |, |\{|  \n |\,| \n |\}| ', home_locations.iloc[i].Coord_1_Casa))[2]
            longitude = (re.split('; |, |\{|  \n |\,| \n |\}| ', home_locations.iloc[i].Coord_1_Casa))[1]
            idterm = home_locations.iloc[i].Id_Term
            lats_home.append(latitude)
            lons_home.append(longitude)
            Id_Term.append(idterm)

    df_home_locations = pd.DataFrame({'latitude': lats_home,
                                      'longitude': lons_home,
                                      'Id_Term': Id_Term})

    ## ----->> crop the data out of the inner border (Riquadro interno)
    M = 5  # Fattore Moltiplicativo (per variare il riquadro interno)
    D_lon = 0.0065
    D_lat = 0.0045  # Delta gradi, corrispondenti a 500 m.

    # ________________________________________________Riscontrati
    Lon_Min_Ris = 11.9214
    Lon_Max_Ris = 13.22569
    Lat_Min_Ris = 41.56645
    Lat_Max_Ris = 42.13107
    # ________________________________________________Riquadro interno
    Lon_Min_Int = Lon_Min_Ris + D_lon * 20
    Lon_Max_Int = Lon_Max_Ris - D_lon * M
    Lat_Min_Int = Lat_Min_Ris + D_lat * M
    Lat_Max_Int = Lat_Max_Ris - D_lat * M

    df_home_locations['latitude'] = df_home_locations.latitude.astype('float')
    df_home_locations['longitude'] = df_home_locations.longitude.astype('float')

    df_home_locations = df_home_locations[
        (df_home_locations['latitude'] <= Lat_Max_Int) & (df_home_locations['latitude'] >= Lat_Min_Int) &
        (df_home_locations['longitude'] >= Lon_Min_Int) & (df_home_locations['longitude'] <= Lon_Max_Int)]

    df_home_locations['latitude'] = df_home_locations.latitude.astype('float')
    df_home_locations['longitude'] = df_home_locations.longitude.astype('float')

    ####-----> make a Geodataframe....
    geometry = [Point(xy) for xy in zip(df_home_locations.longitude, df_home_locations.latitude)]
    crs = {'init': 'epsg:4326'}
    gdf_home_locations = GeoDataFrame(df_home_locations, crs=crs, geometry=geometry)
    # save first as geojson file
    gdf_home_locations.to_file(filename=path_app + 'static/gdf_home_locations.geojson',
                               driver='GeoJSON')
    ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
    with open(path_app + "static/gdf_home_locations.geojson", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var home_locations_point = \n" + old)  # assign the "var name" in the .geojson file

    ##--->> return
    return render_template('index.html')
    ## return 'Click.'


## return coordinates from clicking on the map to another form.html page... if clink on the link "here"
@app.route('/form')
def form():
    longitude = request.args.get('longitude', type=float)
    latitude = request.args.get('latitude', type=float)
    print("latitude--->: ", latitude)
    print("longitude--->: ", longitude)
    # return render_template("form.html", longitude=longitude, latitude=latitude)
    return render_template("index.html", longitude=longitude, latitude=latitude)


@app.route('/mob_privata_page/', methods=['GET', 'POST'])
def mob_privata():
    import glob
    session['ZMU_day'] = '2022-10-11'
    session['ZMU_hour'] = 7
    session["ZMU_hourrange"] = 2
    session["ZMU_tod"] = 6
    session["check_ZMU_tod"] = 6
    session["data_type"] = 11
    session["FCD_day"] = '2022-10-15'

    session["ZMU_day_start"] = '2022-10-01'
    session["ZMU_day_end"] = '2022-10-11'
    session['input_data_range'] = "10/12/2022 - 10/13/2022"
    session["id_stay_type"] = 21
    print("stay points ID;", session["id_stay_type"])
    session["indicator_type"] = 102


    #### ----- check for session ----> data type (FCD, SYNTHETIC)
    stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
    stored_data_type_files.sort(key=os.path.getmtime)
    stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]

    with open(stored_data_type_file) as file:
        selected_data_type = file.read()
    print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
    session["data_type"] = selected_data_type

    #### ----- check for session ----> staypoint (H, W)
    stored_staypoint_files = glob.glob(path_app + "static/params/selected_stay_type_*.txt")
    stored_staypoint_files.sort(key=os.path.getmtime)
    stored_staypoint_file = stored_staypoint_files[len(stored_staypoint_files) - 1]

    with open(stored_staypoint_file) as file:
        selected_stay_type = file.read()
    print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)
    session["id_stay_type"] = selected_stay_type

    #### ----- check for session ----> trip indicator (TRIP; trip time, trip distance, stop time)
    stored_indicator_type_files = glob.glob(path_app + "static/params/selected_indicator_type_*.txt")
    stored_indicator_type_files.sort(key=os.path.getmtime)
    stored_indicator_type_file = stored_indicator_type_files[len(stored_indicator_type_files) - 1]

    with open(stored_indicator_type_file) as file:
        selected_indicator_type = file.read()
    print("selected_indicator_type-------I AM HERE-----------: ", selected_indicator_type)
    session["indicator_type"] = selected_indicator_type


    #### ----- check for session ----> time of day (W, P, H)
    stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
    stored_tod_files.sort(key=os.path.getmtime)
    stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]

    with open(stored_tod_file) as file:
        selected_ZMU_tod = file.read()
    print("selected_ZMU_tod-------I AM HERE-----------: ", selected_ZMU_tod)
    session["ZMU_tod"] = selected_ZMU_tod


    return render_template("index_zmu_select_day.html", session=session)


@app.route('/impacts_page/', methods=['GET', 'POST'])
def impacts_page():

    import glob
    session['ZMU_day'] = '2022-10-11'
    session['ZMU_hour'] = 7
    session["ZMU_hourrange"] = 2
    session["ZMU_tod"] = 6
    session["check_ZMU_tod"] = 6
    session["data_type"] = 11
    session["FCD_day"] = '2022-10-15'

    session["ZMU_day_start"] = '2022-10-01'
    session["ZMU_day_end"] = '2022-10-11'
    session['input_data_range'] = "10/12/2022 - 10/13/2022"
    session["id_stay_type"] = 21
    session["emission_type"] = 11
    session["costs_type"] = 113
    session["external_type"] = 211
    session["fleet_type"] = 21
    print("emission_type: ", session["emission_type"] )
    print("costs_type: ", session["costs_type"])
    print("external_type: ", session["external_type"])

    # for stored_fleet_type_file in glob.glob(path_app + "static/params/selected_fleet_type_*.txt"):
    #    print(stored_fleet_type_file)
    stored_fleet_type_files = glob.glob(path_app + "static/params/selected_fleet_type_*.txt")
    stored_fleet_type_files.sort(key=os.path.getmtime)
    stored_fleet_type_file = stored_fleet_type_files[len(stored_fleet_type_files) - 1]
    with open(stored_fleet_type_file) as file:
        selected_fleet_type = file.read()
    print("selected_fleet_type-------I AM HERE-----------: ", selected_fleet_type)
    session["fleet_type"] = selected_fleet_type



    ### EMISSIONS or Pollutants
    stored_emission_type_files = glob.glob(path_app + "static/params/selected_emission_type_*.txt")
    stored_emission_type_files.sort(key=os.path.getmtime)
    stored_emission_type_file = stored_emission_type_files[len(stored_emission_type_files) - 1]
    with open(stored_emission_type_file) as file:
        selected_emission_type = file.read()
    print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)
    session["emission_type"] = selected_emission_type

    #### ----- check for session ----> staypoint (H, W)
    stored_staypoint_files = glob.glob(path_app + "static/params/selected_stay_type_*.txt")
    stored_staypoint_files.sort(key=os.path.getmtime)
    stored_staypoint_file = stored_staypoint_files[len(stored_staypoint_files) - 1]

    with open(stored_staypoint_file) as file:
        selected_stay_type = file.read()
    print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)
    session["id_stay_type"] = selected_stay_type


    stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
    stored_tod_files.sort(key=os.path.getmtime)
    stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]
    with open(stored_tod_file) as file:
        selected_ZMU_tod = file.read()
    print("selected_ZMU_tod-------I AM HERE-----------: ", selected_ZMU_tod)
    session["ZMU_tod"] = selected_ZMU_tod

    return render_template("index_zmu_impacts.html", session=session)





@app.route('/public_transport_page/', methods=['GET', 'POST'])
def public_transport_page():

    import glob

    session["GTFS_type"] = 11
    session['GTFS_hour'] = '7'
    session["GTFS_tod"] = 6
    session["tod"] = "W"
    session['type'] = "bus"
    session["min_n_buses"] = 1
    session["max_n_buses"] = 45
    session["check_ZMU_tod"] = 6

    stored_GTFS_type_name_files = glob.glob(path_app + "static/params/GTFS_name_*.txt")
    stored_GTFS_type_name_files.sort(key=os.path.getmtime)
    stored_GTFS_type_name_file = stored_GTFS_type_name_files[len(stored_GTFS_type_name_files) - 1]
    with open(stored_GTFS_type_name_file) as file:
        selected_GTFS_type_name = file.read()
    print("selected_GTFS_type_name-------I AM HERE-----------: ", selected_GTFS_type_name)
    session['type'] = selected_GTFS_type_name



    stored_GTFS_type_files = glob.glob(path_app + "static/params/GTFS_type_*.txt")
    stored_GTFS_type_files.sort(key=os.path.getmtime)
    stored_GTFS_type_file = stored_GTFS_type_files[len(stored_GTFS_type_files) - 1]
    with open(stored_GTFS_type_file) as file:
        selected_GTFS_type = file.read()
    print("selected_GTFS_type-------I AM HERE-----------: ", selected_GTFS_type)
    session["GTFS_type"] = selected_GTFS_type


    stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
    stored_tod_files.sort(key=os.path.getmtime)
    stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]
    with open(stored_tod_file) as file:
        selected_GTFS_tod = file.read()
    print("selected_GTFS_tod-------I AM HERE-----------: ", selected_GTFS_tod)
    session["GTFS_tod"] = selected_GTFS_tod

    stored_GFTS_hour_files = glob.glob(path_app + "static/params/selected_GTFS_hour_*.txt")
    stored_GFTS_hour_files.sort(key=os.path.getmtime)
    stored_GFTS_hour_file = stored_tod_files[len(stored_GFTS_hour_files) - 1]
    with open(stored_GFTS_hour_file) as file:
        selected_GTFS_hour = file.read()
    print("selected_GTFS_hour-------I AM HERE-----------: ", selected_GTFS_hour)
    session["GTFS_hour"] = selected_GTFS_hour

    return render_template("index_GTFS_select_daytype.html")




########################################################################################
#### ---- BUS TYPE EMISSIONS --- #######################################################

@app.route('/bus_type_selector/', methods=['GET', 'POST'])
def bus_type_selector():

    import glob

    session['GTFS_hour'] = '7'
    session["GTFS_tod"] = 6
    session["tod"] = "W"
    session['type'] = "bus"
    session["min_n_buses"] = 1
    session["max_n_buses"] = 45
    session["check_ZMU_tod"] = 6

    stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
    stored_fuel_files.sort(key=os.path.getmtime)
    stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
    with open(stored_fuel_file) as file:
        selected_fuel_type = file.read()
    print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
    session["fuel_type"] = selected_fuel_type

    stored_euro_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
    stored_euro_files.sort(key=os.path.getmtime)
    stored_euro_file = stored_euro_files[len(stored_euro_files) - 1]
    with open(stored_euro_file) as file:
        selected_euro_type = file.read()
    print("selected_euro_type-------I AM HERE-----------: ", selected_euro_type)
    session["euro_type"] = selected_euro_type

    stored_segment_files = glob.glob(path_app + "static/params/selected_segment_type_*.txt")
    stored_segment_files.sort(key=os.path.getmtime)
    stored_segment_file = stored_segment_files[len(stored_segment_files) - 1]
    with open(stored_segment_file) as file:
        selected_segment_type = file.read()
    print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)
    session["segment_type"] = selected_segment_type


    stored_engine_files = glob.glob(path_app + "static/params/selected_engine_type_*.txt")
    stored_engine_files.sort(key=os.path.getmtime)
    stored_engine_file = stored_engine_files[len(stored_engine_files) - 1]
    with open(stored_engine_file) as file:
        selected_engine_type = file.read()
    print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)
    session["engine_type"] = selected_engine_type



    ### EMISSIONS or Pollutants
    stored_emission_type_files = glob.glob(path_app + "static/params/selected_emission_type_*.txt")
    stored_emission_type_files.sort(key=os.path.getmtime)
    stored_emission_type_file = stored_emission_type_files[len(stored_emission_type_files) - 1]
    with open(stored_emission_type_file) as file:
        selected_emission_type = file.read()
    print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)
    session["emission_type"] = selected_emission_type

    stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
    stored_tod_files.sort(key=os.path.getmtime)
    stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]
    with open(stored_tod_file) as file:
        selected_GTFS_tod = file.read()
    print("selected_GTFS_tod-------I AM HERE-----------: ", selected_GTFS_tod)
    session["GTFS_tod"] = selected_GTFS_tod

    stored_GFTS_hour_files = glob.glob(path_app + "static/params/selected_GTFS_hour_*.txt")
    stored_GFTS_hour_files.sort(key=os.path.getmtime)
    stored_GFTS_hour_file = stored_tod_files[len(stored_GFTS_hour_files) - 1]
    with open(stored_GFTS_hour_file) as file:
        selected_GTFS_hour = file.read()
    print("selected_GTFS_hour-------I AM HERE-----------: ", selected_GTFS_hour)
    session["GTFS_hour"] = selected_GTFS_hour


    stored_bus_fleet_files = glob.glob(path_app + "static/params/selected_bus_fleet_type_*.txt")
    stored_bus_fleet_files.sort(key=os.path.getmtime)
    stored_bus_fleet_file = stored_bus_fleet_files[len(stored_bus_fleet_files) - 1]
    with open(stored_bus_fleet_file) as file:
        selected_bus_fleet_type = file.read()
    print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)
    session["bus_fleet_type"] = selected_bus_fleet_type

    stored_bus_load_files = glob.glob(path_app + "static/params/selected_bus_load_*.txt")
    stored_bus_load_files.sort(key=os.path.getmtime)
    stored_bus_load_file = stored_bus_load_files[len(stored_bus_load_files) - 1]
    with open(stored_bus_load_file) as file:
        selected_bus_load = file.read()
    print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)
    session["bus_load"] = selected_bus_load

    return render_template("index_GTFS_emiss_select_daytype.html")




########################################################################################
########################################################################################



@app.route('/routing_OD/', methods=['GET', 'POST'])
def routing_OD():

    import glob

    session['ZMU_hour'] = 7

    #### ----- check for session ----> data type (FCD, SYNTHETIC)
    stored_routing_indicator_files = glob.glob(path_app + "static/params/selected_routing_indicator_*.txt")
    stored_routing_indicator_files.sort(key=os.path.getmtime)
    stored_routing_indicator_file = stored_routing_indicator_files[len(stored_routing_indicator_files) - 1]

    with open(stored_routing_indicator_file) as file:
        selected_indicator_type = file.read()
    print("selected_indicator_type-------I AM HERE-----------: ", selected_indicator_type)
    session["indicator_type_TPL"] = selected_indicator_type


    return render_template("index_OD_routing_pub_select_indicator.html", session=session)





### select hour (GTFS)...from Database
@app.route('/GTFS_hour_selector/', methods=['GET', 'POST'])
def GTFS_hour_selector():
    if request.method == "POST":

        ## TRY if session exists
        try:
            session["GTFS_hour"] = request.form.get("GTFS_hour")
            selected_GTFS_hour = session["GTFS_hour"]
            print("selected_GTFS_hour within session:", selected_GTFS_hour)
            selected_GTFS_hour = str(selected_GTFS_hour)
        except:
            session["GTFS_hour"] = 7
            selected_GTFS_hour = session["GTFS_hour"]
            print("using stored variable: ", session["GTFS_hour"])

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text
        connection = engine.connect()

        ###---->> STOPS (from GTFS) <<----################################################
        ### ---> get filtered data of GTFS stops from DB  <--- ###########################
        query_filtered_GTFS_stops = text('''SELECT * from odpub.gdf_stop_buses 
                                              WHERE hour = :x ''')

        stmt_GTFS_stops = query_filtered_GTFS_stops.bindparams(x=str(selected_GTFS_hour))

        with engine.connect() as conn:
            res = conn.execute(stmt_GTFS_stops).all()

        gdf_stop_buses = pd.DataFrame(res)

        ##-----> make a geodataframe
        geometry = [Point(xy) for xy in zip(gdf_stop_buses.stop_lon, gdf_stop_buses.stop_lat)]
        crs = {'init': 'epsg:4326'}
        gdf_stop_buses = GeoDataFrame(gdf_stop_buses, crs=crs, geometry=geometry)
        ## save as .geojson file
        gdf_stop_buses.to_file(filename=path_app + 'static/gtfs_stops_by_routes_filtered.geojson',
                               driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + 'static/gtfs_stops_by_routes_filtered.geojson', 'r+', encoding='utf8',
                  errors='ignore') as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var stop_buses = \n" + old)  # assign the "var name" in the .geojson file

        ###---->> TRIPS (from GTFS) <<----################################################
        ### ---> get filtered data of GTFS stops from DB  <--- ###########################
        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geometry, hex=True)

        ### ---> get filtered data of GTFS trips from DB  <--- ###########################
        query_filtered_GTFS_trips = text('''SELECT * from odpub.gtfs_trips_by_routes 
                                                WHERE hour = :x ''')

        stmt_GTFS_trips = query_filtered_GTFS_trips.bindparams(x=str(selected_GTFS_hour))

        with engine.connect() as conn:
            res = conn.execute(stmt_GTFS_trips).all()

        gtfs_trips_by_routes = pd.DataFrame(res)
        ## transform geometry...
        gtfs_trips_by_routes['geometry'] = gtfs_trips_by_routes.apply(wkb_tranformation, axis=1)
        gtfs_trips_by_routes = gpd.GeoDataFrame(gtfs_trips_by_routes)
        ## save as .geojson file
        gtfs_trips_by_routes.to_file(filename=path_app + 'static/gtfs_trips_by_routes_filtered.geojson',
                                     driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/gtfs_trips_by_routes_filtered.geojson", "r+", encoding="utf8",
                  errors='ignore') as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gtfs_hour = \n" + old)  # assign the "var name" in the .geojson file

        data_GTFS = [{
            # 'GTFS_day': selected_GTFS_day,
            'hour': selected_GTFS_hour
        }]

        return render_template("index_public_transport_select_hour.html", data_GTFS=data_GTFS)

###########################################################################################################
######------------------------ OD MATRICES -------- matrici origine-destinazione ##########################


@app.route('/OD_matrix/', methods=['GET', 'POST'])
def OD_matrix():
    session['GTFS_hour'] = 7
    session["day_type"] = 10
    session["daytype"] = 'Feriale'
    return render_template("index_OD_pub_zmu.html")




@app.route('/day_type_selector/', methods=['GET', 'POST'])
def day_type_selector():

    session['GTFS_hour'] = 7
    session["day_type"] = 11

    ## TRY if session exists
    try:
        session["day_type"] = request.form.get("day_type")
        selected_daytpe = session["day_type"]
        print("selected_daytpe within session:", selected_daytpe)
    except:
        session["day_type"] = 11
        selected_daytpe = session["day_type"]
        print("using stored variable selected_daytpe: ", session["day_type"])

    selected_daytpe = int(selected_daytpe)
    if selected_daytpe == 11:  ## 00:00 ---> 07:00
        daytype = "Feriale"
    elif selected_daytpe == 12:  ## 07:00 ----> 10:00
        daytype = "Week_End"
        daytype = "Feriale"


    session["daytype"] = daytype
    selected_day_type = session["daytype"]
    print('session["daytype"]:', session["daytype"])


    return render_template("index_OD_pub_zmu.html")



### select hour (GTFS)...from Database
@app.route('/OD_pub_hour_selector/', methods=['GET', 'POST'])
def OD_pub_hour_selector():

    # selected_GTFS_hour = 11
    # selected_day_type = 'Feriale'

    selected_day_type = session["daytype"]
    print('selected_day_type:', selected_day_type)


    if request.method == "POST":

        ## TRY if session exists
        try:
            session["GTFS_hour"] = request.form.get("GTFS_hour")
            selected_GTFS_hour = session["GTFS_hour"]
            print("selected_GTFS_hour within session:", selected_GTFS_hour)
            selected_GTFS_hour = str(selected_GTFS_hour)
        except:
            session["GTFS_hour"] = 7
            selected_GTFS_hour = session["GTFS_hour"]
            print("using stored variable: ", session["GTFS_hour"])

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text
        connection = engine.connect()

        ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA_with_population['centroid'] = ZMU_ROMA_with_population.apply(wkb_tranformation_centroid, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA_with_population)

        ###---->> STOPS (from GTFS) <<----################################################
        ### ---> get filtered data of GTFS stops from DB  <--- ###########################
        query_filtered_OD_GTFS = text('''SELECT * from odpub.od_matrici_orarie 
                                              WHERE ora = :x AND giorno_tipo =:y ''')

        stmt_OD_GTFS = query_filtered_OD_GTFS.bindparams(x=str(selected_GTFS_hour), y=str(selected_day_type))

        with engine.connect() as conn:
            res = conn.execute(stmt_OD_GTFS).all()

        gdf_OD_GTFS = pd.DataFrame(res)

        print("-----OK OK ------")

        gdf_OD_GTFS = gdf_OD_GTFS[gdf_OD_GTFS['n_spostamenti_res']>0]


        ##### ---->>> Consider 'n_spostamenti_res' from ORIGIN (generation) @ ORIGIN  (highlight ORIGIN (coloured with the number of trips from Origin ---> Destination)
        aggregated_gdf_OD_GTFS = gdf_OD_GTFS[
            ['orig', 'n_spostamenti_res']].groupby(['orig'], sort=False).sum().reset_index().rename(
            columns={0: 'sum_spostamenti'})

        aggregated_gdf_OD_GTFS.rename({'orig': 'zmu'}, axis=1, inplace=True)
        aggregated_gdf_OD_GTFS = pd.merge(aggregated_gdf_OD_GTFS, ZMU_ROMA, on=['zmu'], how='left')
        aggregated_gdf_OD_GTFS = aggregated_gdf_OD_GTFS[aggregated_gdf_OD_GTFS['geometry'].notna()]


        aggregated_gdf_OD_GTFS = aggregated_gdf_OD_GTFS[
            ['n_spostamenti_res', 'index_zmu', 'POP_TOT_ZMU', 'zmu', 'nome_comun', 'quartiere', 'geometry', 'pgtu', 'municipio']]


        #####----->>> save csv file ---- ##################################################
        aggregated_gdf_OD_GTFS['n_spostamenti_res'] = round(aggregated_gdf_OD_GTFS['n_spostamenti_res'], 0)

        try:
            aggregated_gdf_OD_GTFS = gpd.GeoDataFrame(aggregated_gdf_OD_GTFS)
        except IndexError:
            abort(404)

        ## save as .geojson file
        aggregated_gdf_OD_GTFS.to_file(filename=path_app + 'static/aggregated_gdf_OD_GTFS.geojson',
                                            driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/aggregated_gdf_OD_GTFS.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregated_OD_zmu = \n" + old)  # assign the "var name" in the .geojson file

        #### make AGGREGATION BY DAY and by ORIGIN zone to find HOURLY PROFILE from all ORIGIN ZMUs
        query_origin_OD_hourly_profile = text('''SELECT orig, ora,giorno_tipo, 
                                                  sum(n_spostamenti_res) 
                                                from odpub.od_matrici_orarie
                                              WHERE giorno_tipo =:y
                                               group by orig, ora, giorno_tipo ''')

        stmt = query_origin_OD_hourly_profile.bindparams(y=str(selected_day_type))

        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        origin_OD_hourly_profile = pd.DataFrame(res)



        origin_OD_hourly_profile.rename({'orig': 'zmu'}, axis=1, inplace=True)
        origin_OD_hourly_profile = pd.merge(origin_OD_hourly_profile, ZMU_ROMA, on=['zmu'], how='left')
        origin_OD_hourly_profile = origin_OD_hourly_profile[origin_OD_hourly_profile['geometry'].notna()]

        origin_OD_hourly_profile = origin_OD_hourly_profile[
            ['sum', 'index_zmu', 'POP_TOT_ZMU', 'zmu', 'ora', 'nome_comun', 'quartiere', 'pgtu', 'municipio']]

        origin_OD_hourly_profile['index_zmu'] = origin_OD_hourly_profile.index_zmu.astype('int')
        origin_OD_hourly_profile['sum'] = round(origin_OD_hourly_profile['sum'], 2)


        origin_OD_hourly_profile.to_csv(
            path_app + 'static/origin_OD_hourly_profile_' + session.sid + '.csv')


        ### convert Geodataframe into .geojson...
        session["aggregated_gdf_OD_GTFS"] = aggregated_gdf_OD_GTFS.to_json()

        # print(session['id'])
    return render_template("index_OD_pub_zmu_select_hour.html", session_aggregated_gdf_OD_GTFS=session["aggregated_gdf_OD_GTFS"])


######################################################################################################################
###### ---------------------------------------------------------------------------------- ############################
######################################################################################################################
######------------------------ OD ROUTING -------- routing from CSA (public transport) ###############################



### select TRIP INDICATOR  -------- #################################
@app.route('/trip_indicator_routing/', methods=['GET', 'POST'])
def trip_indicator_routing():
    import glob

    if request.method == "POST":

        session["indicator_type_TPL"] = request.form.get("indicator_type_TPL")
        selected_indicator_type = session["indicator_type_TPL"]
        print("selected_indicator_type:", selected_indicator_type)
        selected_indicator_type = str(selected_indicator_type)

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_indicator_type = int(selected_indicator_type)
        if selected_indicator_type == 102:  ## TRIP COUNTS
            indicator = 'trip_counts'
            print("trip_counts")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)


        elif selected_indicator_type == 103:  ## TRANSFER
            indicator = 'transfers'
            print("transfers")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 104:  ## TRAVEL DISTANCE
            indicator = 'travel_distance'
            print("travel_distance")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 105:  ## TRAVEL TIME
            indicator = 'travel_time'
            print("travel_time")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 106:  ## TRAVEL SPEED
            indicator = 'travel_speed'
            print("travel_speed")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 107:  ## WALKING DISTANCE
            indicator = 'walking_distance'
            print("walking_distance")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 108:  ## WALKING DISTANCE
            indicator = 'walking_time'
            print("walking_time")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 109:  ## ON-BOARD TIME
            indicator = 'onboard_time'
            print("onboard_time")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 110:  ## WAITING TIME
            indicator = 'waiting_time'
            print("waiting_time")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)


        with open(path_app + "static/params/selected_routing_indicator_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_indicator_type))

        return render_template("index_OD_routing_pub_select_indicator.html")




@app.route('/hour_selector_routing/', methods=['GET', 'POST'])
def hour_selector_routing():

    # selected_ZMU_hour = 7

    import glob
    if request.method == "POST":


        try:
            with open(path_app + "static/params/selected_routing_indicator_" + session.sid + ".txt", "r") as file:
                selected_indicator_type = file.read()
            print("selected_indicator_type-------I AM HERE-----------: ", selected_indicator_type)
        except:
            stored_routing_indicator_files = glob.glob(path_app + "static/params/selected_routing_indicator_*.txt")
            stored_routing_indicator_files.sort(key=os.path.getmtime)
            stored_routing_indicator_file = stored_routing_indicator_files[len(stored_routing_indicator_files) - 1]

            with open(stored_routing_indicator_file) as file:
                selected_indicator_type = file.read()
            print("selected_indicator_type-------I AM HERE-----------: ", selected_indicator_type)

        session["indicator_type_TPL"] = selected_indicator_type


        ## TRY if session exists
        try:
            session["ZMU_hour"] = request.form.get("ZMU_hour")
            selected_ZMU_hour = session["ZMU_hour"]
            print("selected_ZMU_hour within session:", selected_ZMU_hour)
            selected_ZMU_hour = str(selected_ZMU_hour)
        except:
            session["ZMU_hour"] = 7
            selected_ZMU_hour = session["ZMU_hour"]
            print("using stored variable: ", session["ZMU_hour"])

        with open(path_app + "static/params/selected_ZMU_hour_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_ZMU_hour))



        ## ----- query data ----------------------------------------####################
        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        ##### ----- query roting OD data from TPL  (CSA outputs from Gaetano V)------- #################################
        query_routing_od = text('''SELECT *
                                     /*FROM gaetano.routing_od*/
                                     FROM gtfs.routing_od_20201002
                                     WHERE EXTRACT(HOUR FROM daytime)= :x
                                     AND distance_m  != -1
                                     AND travel_time_min != -1
                                     AND travel_speed_km_h != -1
                                     AND walking_distance_m != -1
                                     AND transfers_number != -1
                                     AND waiting_time_min != -1
                                     AND on_board_time_min != -1
                                     AND walking_time_min != -1
                                  ''')
        stmt = query_routing_od.bindparams(x=str(selected_ZMU_hour))



        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        od_routes = pd.DataFrame(res)



        ## -----  get ZMU zones  -------- ################################
        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        # ZMU_ROMA_with_population['centroid'] = ZMU_ROMA_with_population.apply(wkb_tranformation_centroid, axis=1)
        # ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA_with_population)



        ##### -------->>>> from ORIGIN ----- ################################################################
        print("length od_routes", len(od_routes))

        od_routes.rename({'from_zone': 'zmu'}, axis=1, inplace=True)
        od_routes = pd.merge(od_routes, ZMU_ROMA_with_population, on=['zmu'],
                                         how='left')
        od_routes = od_routes[['zmu', 'to_zone', 'daytime', 'distance_m', 'travel_time_min',
           'travel_speed_km_h', 'walking_distance_m', 'transfers_number',
           'waiting_time_min', 'on_board_time_min', 'walking_time_min',
           'index_zmu',]]


        od_routes.replace([np.inf, -np.inf], np.nan, inplace=True)
        od_routes.dropna(inplace=True)
        od_routes['index_zmu'] = od_routes.index_zmu.astype('int')
        # od_routes.drop_duplicates(subset=['index_zmu'])

        od_routes.rename({'distance_m': 'distance_km'}, axis=1, inplace=True)
        od_routes['distance_km'] = round(od_routes['distance_km']/1000, 2)
        # od_routes['distance_km'] = od_routes.distance_km.astype('int')

        od_routes.rename({'walking_distance_m': 'walking_distance_km'}, axis=1, inplace=True)
        od_routes['walking_distance_km'] = round(od_routes['walking_distance_km'] / 1000, 2)

        ##### ---->>> aggregation @ ORIGIN
        ## grouby + counts....only if you want to estimate the NUMBER of vehicles
        aggregated_zmu_origin = od_routes[['zmu']].groupby(['zmu'],
            sort=False).size().reset_index().rename(columns={0: 'counts'})

        mean_aggregated_zmu_origin = od_routes[
            ['zmu', 'transfers_number', 'distance_km', 'travel_time_min',
       'travel_speed_km_h', 'walking_distance_km',
       'waiting_time_min', 'on_board_time_min', 'walking_time_min']].groupby(['zmu'],
            sort=False).mean().reset_index().rename(
            columns={0: 'means'})



        ## merge data together ------########################################################
        aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, mean_aggregated_zmu_origin,
                                         on=['zmu'], how='left')


        # aggregated_zmu_origin.rename({'zmu_origin': 'zmu'}, axis=1, inplace=True)
        aggregated_zmu_origin['zmu'] = aggregated_zmu_origin.zmu.astype('int')
        aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, ZMU_ROMA_with_population, on=['zmu'],
                                         how='left')

        aggregated_zmu_origin.replace([np.inf, -np.inf], np.nan, inplace=True)
        aggregated_zmu_origin['distance_km'] = round(aggregated_zmu_origin['distance_km'], 2)
        aggregated_zmu_origin['travel_time_min'] = round(aggregated_zmu_origin['travel_time_min'], 2)
        aggregated_zmu_origin['travel_speed_km_h'] = round(aggregated_zmu_origin['travel_speed_km_h'], 2)
        aggregated_zmu_origin['walking_distance_km'] = round(aggregated_zmu_origin['walking_distance_km'], 2)
        aggregated_zmu_origin['waiting_time_min'] = round(aggregated_zmu_origin['waiting_time_min'], 2)
        aggregated_zmu_origin['on_board_time_min'] = round(aggregated_zmu_origin['on_board_time_min'], 2)
        aggregated_zmu_origin['walking_time_min'] = round(aggregated_zmu_origin['walking_time_min'], 2)
        aggregated_zmu_origin['transfers_number'] = round(aggregated_zmu_origin['transfers_number'], 0)

        aggregated_zmu_origin['transfers_number'] = aggregated_zmu_origin.transfers_number.astype('int')


        aggregated_zmu_origin['index_zmu'] = aggregated_zmu_origin['index_zmu'].astype(int)
        aggregated_zmu_origin.drop(['centroid'], axis=1, inplace=True)

        aggregated_zmu_origin.to_csv(path_app + 'static/aggregated_zmu_origin.csv')


        ## save data
        od_routes.to_csv(path_app + 'static/od_zmu_routing_' + session.sid + '.csv')


        try:
            aggregated_zmu_origin = gpd.GeoDataFrame(aggregated_zmu_origin)
        except IndexError:
            abort(404)

        ## save as .geojson file
        aggregated_zmu_origin.to_file(filename=path_app + 'static/aggregated_zmu_routing_od.geojson',
                                      driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/aggregated_zmu_routing_od.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregated_zmu_routing_od = \n" + old)  # assign the "var name" in the .geojson file

        ### convert Geodataframe into .geojson...
        session["aggregated_zmu_routing_od_origin"] = aggregated_zmu_origin.to_json()
        print("------ I am here----- SESSION Colored ZMUs--------------------------")
        return render_template("index_OD_routing_pub_select_hour.html",
                               session_aggregated_zmu_routing_od_origin=session["aggregated_zmu_routing_od_origin"])



@app.route('/choose_zmu_index_routing_static', methods=['POST'])
def choose_zmu_index_routing_static():
    data = request.json['data']
    session["ZMU_index"] = data
    print("I am here...selected_index_zmu is: ", session["ZMU_index"])
    print("-------------- I am here...selected_index_zmu is:---------------------- ", session["ZMU_index"])
    return jsonify({'result': session["ZMU_index"]})



@app.route('/choose_zmu_index_routing', methods=['POST'])
def choose_zmu_index_routing():
    data = request.json['data']
    session["ZMU_index"] = data
    print("I am here...selected_index_zmu is: ", session["ZMU_index"])

    #### ----- relaod ORIGIN ----> DESTINATION matrix
    od_routes = pd.read_csv(path_app + 'static/od_zmu_routing_' + session.sid + '.csv')
    # od_routes = pd.read_csv(path_app + 'static/od_zmu_routing_14c7fd3e-6cce-4626-b096-f26578a523ae.csv')

    od_routes['index_zmu'] = od_routes.index_zmu.astype('int')

    ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")

    selected_index_zmu = session["ZMU_index"]
    selected_index_zmu = int(float(selected_index_zmu))
    # selected_index_zmu = 52
    print("--------------------selected_index_zmu;--------------------------", selected_index_zmu)
    ## select ORIGIN zone ZMU .......
    filtered_od_routing = od_routes[
        od_routes.index_zmu == selected_index_zmu]  ## this will be selected by the user.....flask + web interface.....
    
    print("----------------------length filtered_od_routing:---------------------------------------------------------------->>>>>>>>", len(filtered_od_routing))
    filtered_od_routing.reset_index(inplace=True)
    input_zmu = int(filtered_od_routing.zmu[0])
    # input_index_zmu = filtered_od_routing.index_zmu[1]
    print("----------------------input_zmu:---------------------------------------------------------------->>>>>>>>",input_zmu)


    filtered_od_routing = filtered_od_routing[['to_zone', 'daytime', 'distance_km',
                                               'travel_time_min', 'travel_speed_km_h', 'walking_distance_km',
                                               'transfers_number', 'waiting_time_min', 'on_board_time_min',
                                               'walking_time_min']]
    filtered_od_routing.rename({'to_zone': 'zmu'}, axis=1, inplace=True)
    # AAA = filtered_od_routing[filtered_od_routing.zmu == '1002019']

    starting_zone = pd.DataFrame({'zmu': [input_zmu],
                                  'daytime': 0,
                                  'distance_km': 999,
                                  'travel_time_min': 999,
                                  'travel_speed_km_h': 999,
                                  'walking_distance_km': 999,
                                  'transfers_number': 100,
                                  'waiting_time_min': 999,
                                  'on_board_time_min': 999,
                                  'walking_time_min': 999
                                  #'index_zmu': input_index_zmu
                                  })

    filtered_od_routing = pd.concat([starting_zone, filtered_od_routing])

    print("----------------------length filtered_od_routing:---------------------------------------------------------------->>>>>>>>", len(filtered_od_routing))
    ### merge with zmu and build a .json file
    filtered_od_routing = pd.merge(filtered_od_routing, ZMU_ROMA, on=['zmu'], how='left')
    # filtered_od_routing.to_csv(path_app + 'static/grouped_zmu_paths_' + session.sid + '.csv')
    filtered_od_routing.replace([np.inf, -np.inf], np.nan, inplace=True)
    # filtered_od_routing.dropna(inplace=True)
    # AAA = pd.DataFrame(filtered_od_routing)
    filtered_od_routing.replace(to_replace=[None], value=np.nan, inplace=True)
    filtered_od_routing.drop(columns=['centroid'], inplace=True)
    # filtered_od_routing['index_zmu'] = filtered_od_routing.index_zmu.astype('int')


    ## save as .geojson file
    try:
        filtered_od_routing = gpd.GeoDataFrame(filtered_od_routing)
    except IndexError:
        abort(404)

    filtered_od_routing.to_file(filename=path_app + 'static/filtered_od_routing_' + session.sid + '.geojson',
                              driver='GeoJSON')

    filtered_od_routing.to_file(filename=path_app + 'static/filtered_od_routing.geojson',
                              driver='GeoJSON')
    ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
    with open(path_app + "static/filtered_od_routing.geojson", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var filtered_od_routing = \n" + old)  # assign the "var name" in the .geojson file

    print("-------------- I am here...selected_index_zmu is:---------------------- ", session["ZMU_index"])

    return jsonify({'result': session["ZMU_index"]})


#### ---->>> this is to refresh the page....with the FINAL LAYER
@app.route('/redirect_zmu_paths_routing/', methods=['GET', 'POST'])
def redirect_zmu_paths_routing():
    import os
    ### open .geojson file in the form of dictionary.....

    filtered_od_routing = open(path_app + "static/filtered_od_routing_" + session.sid + ".geojson",)
    filtered_od_routing = json.load(filtered_od_routing)

    session["filtered_od_routing"] = filtered_od_routing
    # print("session_filtered_od_routing", session["filtered_od_routing"])
    print("-------------- I am here...------------redirect.....")

    return render_template("index_showing_zmu_routing_redirect.html",
                           session_filtered_od_routing =session["filtered_od_routing"])



@app.route('/layer_ZMU_routing/', methods=['GET', 'POST'])
def layer_ZMU_routing():
    return render_template("index_showing_zmu_routing.html")







##################### ------------------------------------------- ###############################################
##################### ------------------------------------------- ###############################################
##################### ------------------------------------------- ###############################################




@app.route('/home_page/', methods=['GET', 'POST'])
def mob_home():
    longitude = request.args.get('lng', type=float)
    latitude = request.args.get('latitude', type=float)
    print("latitude--->: ", latitude)
    print("longitude--->: ", longitude)
    markers = [
        {
            'lat': longitude,
            'lon': latitude,
            'popup': 'user input pnt.'
        }
    ]
    print(markers)

    ######### ----------------------------------- #################
    ### ---->>>> initialize session variables (create a dictionary)
    ###############################################################

    session['ZMU_day'] = '2022-10-11'
    session['ZMU_hour'] = 7
    session["ZMU_hourrange"] = 2
    session["ZMU_tod"] = 6
    session["data_type"] = 10
    session["id_stay_type"] = 21

    session["ZMU_day_start"] = '2022-10-01'
    session["ZMU_day_end"] = '2022-10-11'
    session['input_data_range'] = "10/12/2022 - 10/13/2022"

    return render_template("index.html", longitude=longitude, latitude=latitude)


@app.route('/coords/', methods=['GET', 'POST'])
def coords():
    if request.method == 'POST':
        # Then get the data from the form
        tag = request.form['tag']
        lat = request.form['lat']
        lng = request.form['lng']
        print("input:", tag)
        print("lat, lon---->:", lat, lng)
        markers = [
            {
                'lat': lng,
                'lon': lat,
                'popup': tag
            }
        ]
        print(markers)
        # return(lat, lng)
        return render_template("index_public_transport_select_hour.html", longitude=lng, latitude=lat)


#############################################################################################
#### ---- DRAW a CUSTOM POLYGON delimiting a given areas of ZMUs ----- ######################
@app.route('/custom_polygon', methods=['POST'])
def process():
    data = request.get_json()  # retrieve the data sent from JavaScript
    # process the data using Python code
    poligon = data['value']
    print("Custom_Coords:", poligon)
    # polygon = [[{'lat': 42.114523952464275, 'lng': 12.286834716796875, 'distanceToNextPoint': 17557.05361355438},
    #                 {'lat': 42.00338672135351, 'lng': 12.437896728515625, 'distanceToNextPoint': 21446.84893686627},
    #                 {'lat': 41.86649282301996, 'lng': 12.2552490234375}]]

    lat_point_list = []
    lon_point_list = []
    ## build a list of LATITUDES and LONGITUDES
    for element in poligon[0]:
        # print(element)
        print(element['lat'])
        print(element['lng'])
        lat_point_list.append(element['lat'])
        lon_point_list.append(element['lng'])

    ## ------>> build a POLYGON using these points <<<---------- ###############
    import geopandas as gpd
    from shapely.geometry import Polygon

    polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
    custom_polygon = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[polygon_geom])

    ## draw and save a quick map
    custom_polygon.to_file(filename=path_app + 'static/custom_polygon_ZMU.geojson', driver='GeoJSON')

    import folium
    ave_LAT = 41.90368331095105
    ave_LON = 12.487932714627279
    my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                        tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
    folium.GeoJson(custom_polygon).add_to(my_map)
    folium.LatLngPopup().add_to(my_map)
    my_map.save(path_app + 'static/test_polygon.html')

    #### -------------------------------------------- ######################
    #### ---- Intersect CUSTOM POLYGON with ZMUs----- ######################
    ## get zmu from DB (new linux machine)

    from sqlalchemy import create_engine
    from sqlalchemy import exc
    import sqlalchemy as sal
    from sqlalchemy.pool import NullPool

    engine_lnx = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/rds_22-24")
    from sqlalchemy.sql import text
    connection = engine_lnx.connect()

    zmu_zones = text('''SELECT * from zones.zones''')

    with engine_lnx.connect() as conn:
        res = conn.execute(zmu_zones).all()

    ## function to transform Geometry from text to LINESTRING
    def wkb_tranformation(line):
        return wkb.loads(line.geom, hex=True)

    ZMU_ROMA = pd.DataFrame(res)
    ## transform geom into linestring....
    ZMU_ROMA['geom'] = ZMU_ROMA.apply(wkb_tranformation, axis=1)
    ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA)
    ZMU_ROMA.rename({'geom': 'geometry'}, axis=1, inplace=True)

    ## reference system = 6875 (in meters)
    # ZMU_ROMA = GeoDataFrame.set_crs(ZMU_ROMA, crs="EPSG:6875", allow_override=True)
    ZMU_ROMA = ZMU_ROMA.set_geometry("geometry")
    ZMU_ROMA = ZMU_ROMA.set_crs('epsg:6875', allow_override=True)
    # ZMU_ROMA = gpd.read_file(path_app + "static/zmu_roma_index.geojson")

    ## convert into lat , lon
    ZMU_ROMA = ZMU_ROMA.to_crs({'init': 'epsg:4326'})
    ZMU_ROMA = ZMU_ROMA[['area', 'zmu', 'comune', 'nome_comun', 'quartiere', 'pgtu', 'municipio', 'geometry']]
    ## make a column with the index of the ZMU_ROMA
    ZMU_ROMA['index_zmu'] = ZMU_ROMA.index
    ZMU_ROMA = ZMU_ROMA.set_crs('epsg:4326', allow_override=True)

    # get ZMU containing the DESTINATION locations (gdf_tdf)
    ZMU_intersection = gpd.sjoin(ZMU_ROMA, custom_polygon, how='right', predicate='intersects')  ### <---- OK
    ZMU_intersection = pd.DataFrame(ZMU_intersection)

    ## merge with zmu to get geometries.....
    ## get geometry from "ZMU_ROMA"
    ZMUs_custom_selected = pd.merge(ZMU_intersection[['index_zmu']], ZMU_ROMA, on=['index_zmu'], how='left')
    ZMUs_custom_selected = gpd.GeoDataFrame(ZMUs_custom_selected)
    ave_LAT = 41.90368331095105
    ave_LON = 12.487932714627279
    my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                        tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
    folium.GeoJson(ZMUs_custom_selected[['geometry']]).add_to(my_map)
    folium.LatLngPopup().add_to(my_map)
    my_map.save(path_app + 'static/custom_selected_ZMUs.html')

    ZMUs_custom_selected = ZMUs_custom_selected[
        ['index_zmu', 'zmu', 'comune', 'nome_comun', 'quartiere', 'pgtu', 'geometry']]
    ## make a list of unique 'nome_comun' and 'quartiere'
    aggregated_names_comune = list(ZMUs_custom_selected.nome_comun.unique())
    aggregated_names_quartiere = list(ZMUs_custom_selected.quartiere.unique())
    ## --->> save lists into txt files
    with open(path_app + 'static/aggregated_names_comune.txt', "w") as file:
        file.write(str(aggregated_names_comune))
    ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
    with open(path_app + "static/aggregated_names_comune.txt", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var aggregated_names_comune = \n" + old)  # assign the "var name" in the .geojson file
    with open(path_app + 'static/aggregated_names_quartiere.txt', "w") as file:
        file.write(str(aggregated_names_quartiere))
    with open(path_app + "static/aggregated_names_quartiere.txt", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var aggregated_names_quartiere = \n" + old)  # assign the "var name" in the .geojson file

    session['aggregated_names_comune'] = aggregated_names_comune
    session['aggregated_names_quartiere'] = aggregated_names_quartiere

    ## save geojson file......OF the ZMUs zones intersecting the CUSTOM POLYGON
    # save first as geojson file
    with open(path_app + 'static/ZMUs_custom_selected.geojson', 'w') as f:
        f.write(ZMUs_custom_selected.to_json())
    ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
    with open(path_app + "static/ZMUs_custom_selected.geojson", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var ZMUs_custom_selected = \n" + old)  # assign the "var name" in the .geojson file

    ## --- compute the external boundary of the slected ZMUs
    # --->> ,erge all geometries
    border_polygon = ZMUs_custom_selected.geometry.unary_union
    border = gpd.GeoDataFrame(geometry=[border_polygon], crs=ZMUs_custom_selected.crs)
    my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                        tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
    folium.GeoJson(border[['geometry']]).add_to(my_map)
    folium.LatLngPopup().add_to(my_map)
    my_map.save(path_app + 'static/BORDER_selected_ZMUs.html')

    ## save geojson file......OF the ZMUs zones intersecting the CUSTOM POLYGON
    # save first as geojson file
    with open(path_app + 'static/BORDER_selected_ZMUs.geojson', 'w') as f:
        f.write(border.to_json())
    # print("------BORDER------", border.to_json())
    with open(path_app + 'static/BORDER_selected_ZMUs_aggr_' + session.sid + '.geojson', 'w') as f:
        f.write(border.to_json())
    ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
    with open(path_app + "static/BORDER_selected_ZMUs.geojson", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var BORDER_selected_ZMUs = \n" + old)  # assign the "var name" in the .geojson file

    return render_template("index_zmu_select_hour.html",
                           session_aggregated_names_comune=session['aggregated_names_comune'],
                           session_aggregated_names_quartiere=session['aggregated_names_quartiere']
                           )  # session_BORDER_selected_ZMUs = session['BORDER_selected_ZMUs']


@app.route('/points_interest/', methods=['GET', 'POST'])
def pois():
    lat = request.form['lat']
    lng = request.form['lng']
    tag = request.form['tag']  ## buffer distance in meters
    print("lat, lon---->:", lat, lng, tag)

    tags = {'amenity': True}

    ### read geojson file of traffic zone (ZMU)
    ZMU_ROMA = gpd.read_file(path_app + "static/zmu_roma_index.geojson")
    ## Points of interests starting from central point in Rome
    pois_gdf = ox.geometries_from_point((float(lat), float(lng)), dist=float(tag), tags=tags)
    if len(pois_gdf) > 0:
        POIS = pd.DataFrame(pois_gdf)
        POIS.reset_index(inplace=True)
        POIS_parking = POIS[POIS.amenity == 'parking']

        POIS_parking = gpd.GeoDataFrame(POIS_parking)
        POIS_parking = POIS_parking.set_crs('epsg:4326')
        POIS_parking = POIS_parking[POIS_parking.geom_type != 'Point']

        # save first as geojson file
        with open(path_app + 'static/POIS_parking.geojson', 'w') as f:
            f.write(POIS_parking.to_json())
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/POIS_parking.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var POIS_parking = \n" + old)  # assign the "var name" in the .geojson file
    else:
        print("enter valid location coordinates")

    ############################################################################
    ############# -------------------------------------- #######################
    ############# -------------------------------------- #######################
    ############################################################################
    ### get all possible AMENITIES  ------- ####################################
    tags = {'amenity': True}
    pois_amenities_gdf = ox.geometries_from_point((float(lat), float(lng)), dist=float(tag), tags=tags)
    ## Drop rows containings specific type of amenitiy.....
    if len(pois_amenities_gdf) > 0:
        pois_amenities_gdf = pois_amenities_gdf[pois_amenities_gdf['amenity'].str.contains(
            "drinking_water|waste_basket|ice_cream|atm|toilets|vending_machine|archive|clock|telephone|animal_shelter|"
            "studio|waste_transfer_station|bicycle_repair_station|canteen|waiting_room|baptistery|parcel_locker|recycling|"
            "internet_cafe|physiokinesitherapy|public_bookcase|club|fire_station|watering_place|money_transfer|denstist|piano|"
            "photo_booth|reception_desk|prison|left_luggage|police_booth|car_wash|letter_box|bicycle_rental|boat_rental|planetarium|"
            "water_point|hunting_stand|newsagent|mortuary|shelter|funeral_hall|biergarten|gambling:vending_machine|dispenser|"
            "toy_library|fablab|recording_studio|grave_yard|shower|Lasergame|ranger_station|photobooth|bench|fountain|bank|post_box|music_school"
            "veterinary|seminary|payment_terminal|bureau_de_change|driving_school|monastery|luggage_storage|waste_disposal|post_depot|art_gallery") == False]  ## charging_station ??

        ## remove geometry "POINT"..
        layer_pois_amenities = pois_amenities_gdf[pois_amenities_gdf.geom_type != 'Point']
        layer_POIS_amenities = pd.DataFrame(layer_pois_amenities)
        layer_POIS_amenities.reset_index(inplace=True)
        layer_POIS_amenities = gpd.GeoDataFrame(layer_POIS_amenities)
        layer_POIS_amenities = layer_POIS_amenities.set_crs('epsg:4326')
        layer_POIS_amenities = layer_POIS_amenities[['amenity', 'geometry']]

        POIS_amenities = pd.DataFrame(pois_amenities_gdf)
        POIS_amenities.reset_index(inplace=True)
        AAA = POIS_amenities[POIS_amenities.amenity == 'hospital']

        POIS_amenities = gpd.GeoDataFrame(POIS_amenities)
        POIS_amenities = POIS_amenities.set_crs('epsg:4326')
        # POIS_amenities = POIS_amenities[['amenity', 'name', 'geometry']]
        POIS_amenities = POIS_amenities[['amenity', 'geometry']]
        ## ---->>> make intersection with ZMUs
        # get ZMU containing the all AMENITY locations
        ZMU_ROMA = gpd.read_file(path_app + "static/zmu_roma_index.geojson")
        POIS_amenities = gpd.sjoin(ZMU_ROMA, POIS_amenities, how='inner',
                                   predicate='intersects')
        POIS_amenities = pd.DataFrame(POIS_amenities)
        ##---> group by AMENITIES and ZMUs
        aggr_AMENITIES_ZMU = POIS_amenities.groupby(['zmu', 'amenity']).size()
        aggr_AMENITIES_ZMU = pd.DataFrame(aggr_AMENITIES_ZMU)
        aggr_AMENITIES_ZMU.reset_index(inplace=True)
        aggr_AMENITIES_ZMU['zmu'] = aggr_AMENITIES_ZMU.zmu.astype('int')
        aggr_AMENITIES_ZMU.rename({0: 'amenity_counts'}, axis=1, inplace=True)
        amenities = aggr_AMENITIES_ZMU['amenity'].drop_duplicates()
        ##----->>> spread dataframe on column "amenity"
        aggr_AMENITIES_ZMU = aggr_AMENITIES_ZMU.pivot(index='zmu', columns='amenity', values='amenity_counts')
        aggr_AMENITIES_ZMU.reset_index(inplace=True)

        # save layer to plot on the map as geojson file
        with open(path_app + 'static/layer_POIS_amenities.geojson', 'w') as f:
            f.write(layer_POIS_amenities.to_json())
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/layer_POIS_amenities.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var POIS_amenities = \n" + old)  # assign the "var name" in the .geojson file
    else:
        print("enter valid location coordinates")

    ### ---- RESIDENTIAL ---#####################################################
    tags_residential = {'amenity': True,
                        'building': ['apartments', 'detached', 'hotel', 'house', 'residential', 'semidetached_house',
                                     'commercial', 'dormitory'
                                                   'industrial', 'dormitory', 'office', 'supermarket', 'warehouse',
                                     'mosque', 'train_station', 'transportation',
                                     'sports_hall', 'stadium']}
    pois_gdf_residential = ox.geometries_from_point((float(lat), float(lng)), dist=float(tag),
                                                    tags=tags_residential)
    ## Drop rows containings specific type of amenitiy.....
    if len(pois_gdf_residential) > 0:
        pois_gdf_residential = pois_gdf_residential[pois_gdf_residential['building'].str.contains(
            "yes|chapel|baptistery|kiosk|water_dispenser|no|terrace|hall|toilets|parking|cinema|hospital|"
            "monastery|nursing_home|place_of_worship|restaurant|school|theatre|temple|dormitory|university") == False]

    if len(pois_gdf_residential) > 0:
        ## remove geometry "POINT"..
        layer_pois_residential = pois_gdf_residential[pois_gdf_residential.geom_type != 'Point']
        layer_pois_residential = pd.DataFrame(layer_pois_residential)
        layer_pois_residential.reset_index(inplace=True)
        layer_pois_residential = gpd.GeoDataFrame(layer_pois_residential)
        layer_pois_residential = layer_pois_residential.set_crs('epsg:4326')
        layer_pois_residential = layer_pois_residential[['building', 'geometry']]
        ## remove NA values
        layer_pois_residential = layer_pois_residential[layer_pois_residential['building'].notna()]

        POIS_residential = pd.DataFrame(pois_gdf_residential)
        POIS_residential.reset_index(inplace=True)
        POIS_residential = gpd.GeoDataFrame(POIS_residential)
        POIS_residential = POIS_residential.set_crs('epsg:4326')
        POIS_residential = POIS_residential[['building', 'geometry']]
        ## remove NA values
        POIS_residential = POIS_residential[POIS_residential['building'].notna()]
        ## ---->>> make intersection with ZMUs
        # get ZMU containing the all RESIDENTIAL locations
        POIS_residential = gpd.sjoin(ZMU_ROMA, POIS_residential, how='inner',
                                     predicate='intersects')
        POIS_residential = pd.DataFrame(POIS_residential)
        ##---> group by AMENITIES and ZMUs
        aggr_RESIDENTIAL_ZMU = POIS_residential.groupby(['zmu', 'building']).size()
        aggr_RESIDENTIAL_ZMU = pd.DataFrame(aggr_RESIDENTIAL_ZMU)
        aggr_RESIDENTIAL_ZMU.reset_index(inplace=True)
        aggr_RESIDENTIAL_ZMU['zmu'] = aggr_RESIDENTIAL_ZMU.zmu.astype('int')
        aggr_RESIDENTIAL_ZMU.rename({0: 'residential_counts'}, axis=1, inplace=True)
        residentials = aggr_RESIDENTIAL_ZMU['building'].drop_duplicates()
        ##----->>> spread dataframe on column "building"
        aggr_RESIDENTIAL_ZMU = aggr_RESIDENTIAL_ZMU.pivot(index='zmu', columns='building', values='residential_counts')
        aggr_RESIDENTIAL_ZMU.reset_index(inplace=True)

        ##  ---->>> merge "aggr_RESIDENTIAL_ZMU" with "aggr_AMENITIES_ZMU"  ---#####
        aggr_POIS_ZMU = pd.merge(aggr_RESIDENTIAL_ZMU, aggr_AMENITIES_ZMU, on=['zmu'], how='right')

        ## merge with ZMU_ROMA
        aggr_POIS_ZMU = pd.merge(aggr_POIS_ZMU, ZMU_ROMA, on=['zmu'], how='left')
        ## save to .geojson file
        aggr_POIS_ZMU = gpd.GeoDataFrame(aggr_POIS_ZMU)
        aggr_POIS_ZMU.to_file(filename=path_app + 'static/zmu_POIS_ROMA_2011.geojson',
                              driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/zmu_POIS_ROMA_2011.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var zmu_POIS_counts = \n" + old)  # assign the "var name" in the .geojson file

        # save first as geojson file
        with open(path_app + 'static/layer_POIS_residential.geojson', 'w') as f:
            f.write(layer_pois_residential.to_json())
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/layer_POIS_residential.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var POIS_residential = \n" + old)  # assign the "var name" in the .geojson file

        ### ---- CHARGING_STATION ---#####################################################
        tags_residential = {'amenity': True,
                            'building': ['charging_station']}

    else:
        print("enter valid location coordinates")

    return render_template("index_zmu_select_day.html", longitude=lng, latitude=lat)


@app.route('/animation_TPL/', methods=['GET', 'POST'])
def animation_TPL():
    session["gtfs"] = '2023_04_05'
    return render_template("index_animated_TPL_GTFS_selection.html", session_GTFS=session["gtfs"])


@app.route('/GTFS_selector/', methods=['GET', 'POST'])
def GTFS_selector():
    if request.method == "POST":
        ## declare a global variable

        session["gtfs"] = '2023_04_05'
        ## TRY if session exists
        try:
            session["gtfs"] = request.form.get("gtfs")
            selected_GTFS_data = session["gtfs"]
            print("selected_GTFS_data within session:", selected_GTFS_data)
            selected_GTFS_data = str(selected_GTFS_data)
        except:
            session["gtfs"] = '2023_04_05'
            selected_GTFS_data = session["gtfs"]
            print("using stored variable: ", session["gtfs"])

        print("selected_GTFS_data:", selected_GTFS_data)
        datum_GTFS = [{
            'GTFS_file': selected_GTFS_data,
            'TPL_line': 'choose TPL line',
            'hour': 'choose hour',
            'viaggio': 'choose trip'
        }]

        ## load timetable:
        path = path_app + "static/GTFS"
        ## list all files in the directory
        list_GTFS_files = listdir(path)

        readable_day_GTFS = []
        for element in list_GTFS_files:
            # print(element)
            year_GTFS = element[:4]
            month_GTFS = element[4:6]
            day_GTFS = element[6:9]
            full_day_GTFS = year_GTFS + "_" + month_GTFS + "_" + day_GTFS
            # print(full_day_GTFS)
            readable_day_GTFS.append(full_day_GTFS)

            ## ----->> make a dictionary (for each id GTFS file associate a date):
            GTFS_dict = {}
            keys = list(readable_day_GTFS)

            for idx, u in enumerate(keys):
                # print(idx, u)
                GTFS_dict[u] = list_GTFS_files[idx]

        ## add empty element in front of the list
        readable_day_GTFS.insert(0, 'select day (GTFS)')

        ## save the list into a .txt file
        with open(path_app + "static/GTFS_files.txt", "w") as file:
            file.write(str(readable_day_GTFS))
        with open(path_app + "static/GTFS_files.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var list_GTFS_files = \n" + old)  # assign the "var name" in the .geojson file
        try:
            day = GTFS_dict[selected_GTFS_data]
        except KeyError:
            day = "20230123"

        print("GTFS day:", selected_GTFS_data)
        print("day:", day)
        routes = pd.read_csv(path + '/' + day + '/' + 'routes.txt')  ## "route_id" is the "line"

        ## list of all routes or trip_IDs
        list_lines_routes = routes.route_short_name.values.tolist()
        list_lines_routes.sort()
        ## add empty element in front of the list
        list_lines_routes.insert(0, 'select TPL line')

        with open(path_app + "static/list_lines_routes_TPL.txt", "w") as file:
            file.write(str(list_lines_routes))
        with open(path_app + "static/list_lines_routes_TPL.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var list_lines_routes = \n" + old)  # assign the "var name" in the .geojson file
        return render_template("index_animated_TPL_GTFS_selection.html", datum_GTFS=datum_GTFS)


@app.route('/TPL_selector/', methods=['GET', 'POST'])
def TPL_selector():
    if request.method == "POST":

        try:
            selected_GTFS_data = session["gtfs"]
            print("selected_GTFS_data:", selected_GTFS_data)
        except AttributeError:
            abort(404)

        ## TRY if session exists
        try:
            session["line"] = request.form.get("line")
            selected_TPL_line = session["line"]
            print("selected_TPL_line within session:", selected_GTFS_data)
            selected_TPL_line = str(selected_TPL_line)
        except:
            session["line"] = '628'
            selected_TPL_line = session["line"]
            print("using stored variable: ", session["line"])

        print("selected_TPL_line:", selected_TPL_line)
        datum = [{
            'GTFS_file': selected_GTFS_data,
            'TPL_line': selected_TPL_line,
            'hour': 'choose hour',
            'viaggio': 'choose trip'
        }]

        return render_template("index_animated_TPL_line_selection.html", datum=datum)


@app.route('/TPL_hour_selector/', methods=['GET', 'POST'])
def TPL_hour_selector():
    if request.method == "POST":

        try:
            selected_GTFS_data = session["gtfs"]
            print("selected_GTFS_data:", selected_GTFS_data)
        except AttributeError:
            abort(404)

        try:
            selected_TPL_line = session["line"]
            print("selected_TPL_line:", selected_TPL_line)
        except AttributeError:
            abort(404)

        ## TRY if session exists
        try:
            session["TPL_hour"] = request.form.get("TPL_hour")
            selected_TPL_hour = session["TPL_hour"]
            print("selected_TPL_line within session:", selected_TPL_hour)
            selected_TPL_hour = str(selected_TPL_hour)
        except:
            session["TPL_hour"] = 8
            selected_TPL_hour = session["TPL_hour"]
            print("using stored variable: ", session["TPL_hour"])

        path = path_app + "static/GTFS"
        ## list all files in the directory
        list_GTFS_files = listdir(path)

        readable_day_GTFS = []
        for element in list_GTFS_files:
            # print(element)
            year_GTFS = element[:4]
            month_GTFS = element[4:6]
            day_GTFS = element[6:9]
            full_day_GTFS = year_GTFS + "_" + month_GTFS + "_" + day_GTFS
            # print(full_day_GTFS)
            readable_day_GTFS.append(full_day_GTFS)

            ## ----->> make a dictionary (for each id GTFS file associate a date):
            GTFS_dict = {}
            keys = list(readable_day_GTFS)

            for idx, u in enumerate(keys):
                # print(idx, u)
                GTFS_dict[u] = list_GTFS_files[idx]

        ## add empty element in front of the list
        readable_day_GTFS.insert(0, 'select day (GTFS)')

        ## save the list into a .txt file
        with open(path_app + "static/GTFS_files.txt", "w") as file:
            file.write(str(readable_day_GTFS))
        with open(path_app + "static/GTFS_files.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var list_GTFS_files = \n" + old)  # assign the "var name" in the .geojson file

        print("GTFS day:", selected_GTFS_data)
        day = GTFS_dict[selected_GTFS_data]
        print("GTFS day:", day)
        stop_times = pd.read_csv(
            path + '/' + day + '/' + 'stop_times.txt')  ## to get the name of the line --->route_id and name
        trips = pd.read_csv(
            path + '/' + day + '/' + 'trips.txt')  ## to get "trip_id" and "shape_id" and "route_id" ("line")
        shapes = pd.read_csv(
            path + '/' + day + '/' + 'shapes.txt')  ## to get "shape_id" and "lat", "lon" of each stop and "shape_pt_sequence"
        routes = pd.read_csv(path + '/' + day + '/' + 'routes.txt')  ## "route_id" is the "line"
        stops = pd.read_csv(path + '/' + day + '/' + 'stops.txt')  ## "stop_lat" and "stop_lon"

        ## list of all routes or trip_IDs
        list_lines_routes = routes.route_short_name.values.tolist()
        list_lines_routes.sort()
        ## add empty element in front of the list
        list_lines_routes.insert(0, 'select TPL line')

        # list_lines_routes = listToStringWithoutBrackets(list_lines_routes)
        with open(path_app + "static/list_lines_routes_TPL.txt", "w") as file:
            file.write(str(list_lines_routes))
        with open(path_app + "static/list_lines_routes_TPL.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var list_lines_routes = \n" + old)  # assign the "var name" in the .geojson file

        ### # format all hours to 0:24 format
        # format all hours to 0:24 format
        hour = (stop_times["arrival_time"].str.split(":", n=1, expand=True)[0]).astype(int)
        hour[hour > 24] = hour - 24

        stop_times['hour'] = hour
        stop_times = stop_times[['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence',
                                 'shape_dist_traveled', 'hour']]
        trips = trips[['route_id', 'service_id', 'trip_id', 'trip_headsign', 'shape_id']]

        stop_times['stop_id'] = stop_times.stop_id.astype('str')
        stop_times = pd.merge(stop_times, stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']], on=['stop_id'],
                              how='left')

        timetable = pd.merge(stop_times, trips, on=['trip_id'], how='left')
        timetable = pd.merge(timetable, routes[['route_id', 'route_short_name']], on=['route_id'], how='left')
        timetable_animation = timetable[
            ['trip_id', 'arrival_time', 'stop_id', 'stop_sequence', 'hour', 'stop_lat', 'stop_lon', 'shape_id',
             'route_short_name', 'trip_headsign']]
        # route_id = '628'
        # hour = 12
        route_id = str(selected_TPL_line)
        hour = int(selected_TPL_hour)

        ## build the sequence of stops following the timetable schedule....
        full_trip = timetable_animation[timetable_animation.route_short_name == route_id]
        ## choose a time range that can COVER the fULL TRIP. Therefore, get trip within previous-current- next HOUR
        trip = full_trip[(full_trip['hour'] >= hour - 1) & (full_trip['hour'] <= hour + 1)]

        ##-->>> only consider trips with full "stop_sequence" starting from "1"
        trip_full_sequence = trip[trip['stop_sequence'] == 1]
        all_trips_IDS = list(trip_full_sequence.trip_id.unique())
        ## save trip
        trip.to_csv(path_app + 'static/selected_trips_hour_TPL.csv')
        ##-->> list all possible trips in thst hour
        # all_trips_IDS = list(trip.trip_id.unique())
        ##----> rename trips..MAKE a dictionary...
        trip_dict = {}
        keys = list(range(len(all_trips_IDS)))

        key_start_trip_time = []
        for u in keys:
            trip_dict[u] = all_trips_IDS[u]
            sub_trip = pd.DataFrame(trip[trip['trip_id'] == trip_dict[u]]['arrival_time'])
            sub_trip.reset_index(inplace=True)
            key_time = sub_trip['arrival_time'][0]
            key_start_trip_time.append(key_time)
            ## sort list
            key_start_trip_time.sort(reverse=False)

        ## save all trip keys into a list
        with open(path_app + "static/list_trip_keys_TPL.txt", "w") as file:
            file.write(str(key_start_trip_time))
        with open(path_app + "static/list_trip_keys_time_TPL.txt", "w") as file:
            file.write(str(key_start_trip_time))

        with open(path_app + "static/list_trip_keys_TPL.txt", "r+") as f:
            old = f.read()  # read everything in the file
            # partial_old = old[2:len(old)]
            # old = str("['', ") + partial_old
            f.seek(0)  # rewind
            f.write("var list_trips = \n" + old)  # assign the "var name" in the .geojson file

        data = [{
            'GTFS_file': selected_GTFS_data,
            'TPL_line': selected_TPL_line,
            'hour': selected_TPL_hour,
            'viaggio': 'choose trip'
        }]
        return render_template("index_animated_TPL_hour_selection.html", data=data)  # params=selected_TPL_params


@app.route('/TPL_trip_selector/', methods=['GET', 'POST'])
def TPL_trip_selector():
    if request.method == "POST":

        try:
            selected_GTFS_data = session["gtfs"]
            print("selected_GTFS_data:", selected_GTFS_data)
        except AttributeError:
            abort(404)

        try:
            selected_TPL_line = session["line"]
            print("selected_TPL_line:", selected_TPL_line)
        except AttributeError:
            abort(404)

        try:
            selected_TPL_hour = session["TPL_hour"]
            print("selected_TPL_hour:", selected_TPL_hour)
        except AttributeError:
            abort(404)

        ## declare a global variable
        # global slected_trip_ID
        hour = int(selected_TPL_hour)
        route_id = str(selected_TPL_line)

        path = path_app + "static/GTFS"
        list_GTFS_files = listdir(path)

        readable_day_GTFS = []
        for element in list_GTFS_files:
            # print(element)
            year_GTFS = element[:4]
            month_GTFS = element[4:6]
            day_GTFS = element[6:9]
            full_day_GTFS = year_GTFS + "_" + month_GTFS + "_" + day_GTFS
            # print(full_day_GTFS)
            readable_day_GTFS.append(full_day_GTFS)

            ## ----->> make a dictionary (for each id GTFS file associate a date):
            GTFS_dict = {}
            keys = list(readable_day_GTFS)

            for idx, u in enumerate(keys):
                # print(idx, u)
                GTFS_dict[u] = list_GTFS_files[idx]

        # day = selected_GTFS_data
        print("GTFS day:", selected_GTFS_data)
        # day = "20230123"
        # day = selected_GTFS_data
        day = GTFS_dict[selected_GTFS_data]
        print("GTFS day:", day)

        path = path_app + "static/GTFS"
        shapes = pd.read_csv(
            path + '/' + day + '/' + 'shapes.txt')  ## to get "shape_id" and "lat", "lon" of each stop and "shape_pt_sequence"
        stops = pd.read_csv(path + '/' + day + '/' + 'stops.txt')  ## "stop_lat" and "stop_lon"
        selected_trip_ID = request.form["viaggio"]
        print("selected_trip_ID:", selected_trip_ID)
        ## re-load" selected trip by hour
        trip = pd.read_csv(path_app + 'static/selected_trips_hour_TPL.csv')
        ##--->> only consider trips with full "stop_sequence" starting from "1"
        trip_full_sequence = trip[trip['stop_sequence'] == 1]
        all_trips_IDS = list(trip_full_sequence.trip_id.unique())
        # all_trips_IDS = list(trip.trip_id.unique())
        ##----> rename trips..MAKE a dictionary...
        trip_dict = {}
        keys = list(range(len(all_trips_IDS)))
        for u in keys:
            trip_dict[u] = all_trips_IDS[u]

        ## reload 'key_start_trip_time' as list
        with open(path_app + "static/list_trip_keys_time_TPL.txt", "r") as file:
            key_start_trip_time = eval(file.readline())
        # selected_trip_ID = '13:40:00'  # 59
        trip_dict_starttime = {}
        for idx_v, v in enumerate(key_start_trip_time):
            print(idx_v, v)
            trip_dict_starttime[v] = all_trips_IDS[idx_v]
        selected_trip_id = trip_dict_starttime[selected_trip_ID]

        print("selected TRIP:", selected_trip_id)
        selected_trip = trip[trip['trip_id'] == selected_trip_id]
        if len(trip) > 0:
            selected_trip.reset_index(inplace=True)
            ##---> get all lat lon....
            shape_ID = selected_trip['shape_id'][0]
            headsign = selected_trip['trip_headsign'][0]
            shape_path = shapes[shapes['shape_id'] == str(shape_ID)]
            ## sort by sequence
            shape_path = shape_path.sort_values(['shape_pt_sequence'])

            ## ----> make a dictionary with ID "shape_pt_sequence" for each "shape_pt_lat" and "shape_pt_lon"
            # https://stackoverflow.com/questions/69988283/nearest-latitude-and-longitude-points-in-python
            from geopy import distance
            shape_dict = {}
            keys_shapes = shape_path.shape_pt_sequence.to_list()
            for u in keys_shapes:
                shape_dict[u] = shape_path[['shape_pt_lat', 'shape_pt_lon']][
                    shape_path['shape_pt_sequence'] == u].values.tolist()

            ##--->>> make a dictionary with first and last coords of stops
            start_stop = selected_trip[(selected_trip['stop_sequence'] == 1)]
            end_stop = selected_trip[(selected_trip['stop_sequence'] == max(selected_trip.stop_sequence))]
            start_end_stop = pd.concat([start_stop, end_stop])
            shape_start_stop = {}
            keys_shape_start_stop = start_end_stop.stop_sequence.to_list()
            for v in keys_shape_start_stop:
                shape_start_stop[v] = start_end_stop[['stop_lat', 'stop_lon']][
                    start_end_stop['stop_sequence'] == v].values.tolist()

            start_stop.reset_index(inplace=True)
            end_stop.reset_index(inplace=True)
            start_stop_id = start_stop.stop_sequence[0]
            end_stop_id = end_stop.stop_sequence[0]

            ### find coordinates of the shapes that are closer to the first and last stop of the "selected_trip"
            DISTANZA_start_stop = []
            for (ss, a) in shape_dict.items():
                a = tuple([item for sublist in a for item in sublist])
                # print(ss, a)
                best = None
                dist = None
                for (dd, b) in shape_start_stop.items():
                    if dd == start_stop_id:
                        b = tuple([item for sublist in b for item in sublist])
                        # print(dd, b)
                        km = distance.distance(a, b).km
                        if dist is None or km < dist:
                            best = dd
                            dist = km
                DISTANZA_start_stop.append(dist)

            ### find coordinates of the shapes that are closer to the first and last stop of the "selected_trip"
            DISTANZA_end_stop = []
            for (ss, a) in shape_dict.items():
                a = tuple([item for sublist in a for item in sublist])
                # print(ss, a)
                best = None
                dist = None
                for (dd, b) in shape_start_stop.items():
                    if dd == end_stop_id:
                        b = tuple([item for sublist in b for item in sublist])
                        # print(dd, b)
                        km = distance.distance(a, b).km
                        if dist is None or km < dist:
                            best = dd
                            dist = km
                DISTANZA_end_stop.append(dist)
                # print(f'{ss} is nearest {best}: {dist} km')
                # min(DISTANZA_end_stop)

            full_dist_list = sorted([[ss, dd, distance.distance(a, b).km] for (ss, a) in shape_dict.items()
                                     for (dd, b) in shape_start_stop.items()])

            ## find sublist in "full_dist_list" containing min(DISTANZA)
            ## --->> return ID of "shape_pt_sequence" where to cut the "shape_path"
            for sublist in full_dist_list:
                # print(sublist)
                if min(DISTANZA_start_stop) in sublist:
                    # print("gottah!!!", sublist, sublist[0])
                    start_stop_sequence_ID = sublist[0]

            for sublist in full_dist_list:
                # print(sublist)
                if min(DISTANZA_end_stop) in sublist:
                    # print("gottah!!!", sublist, sublist[0])
                    end_stop_sequence_ID = sublist[0]

            try:
                ## --->> return ID of "shape_pt_sequence" where to cut the "shape_path"
                # selected_shape_path = shape_path[(shape_path['shape_pt_sequence'] >= start_stop_sequence_ID) & (shape_path['shape_pt_sequence'] <= end_stop_sequence_ID) ]
                selected_shape_path = shape_path[
                    (shape_path['shape_pt_sequence'] >= 1) & (shape_path['shape_pt_sequence'] <= end_stop_sequence_ID)]
                ##-->>> sort by sequence
                trip_poline_stop = [[x, y] for (x, y) in
                                    zip(selected_shape_path.shape_pt_lat, selected_shape_path.shape_pt_lon)]
                ## append last stop to list...
                # get all the timing
                timeline_poline = [[x] for (x) in selected_trip['arrival_time']]
                ## build a L.polyline for the leaflet layer to put in the java script for the html page.
                trip_poline_stop = "L.polyline(" + str(trip_poline_stop) + ")"
                df_ROUTE = pd.DataFrame({'route_ID': [route_id],
                                         'trip_headsign': [headsign],
                                         'trip_ID': [selected_trip_id],
                                         'hour': [hour],
                                         'trip': [trip_poline_stop],
                                         'timeline': [timeline_poline]})
                # route_TPL.append(df_ROUTE)
                ## convert list into dataframe
                try:
                    # route_TPL_all = pd.concat(route_TPL)
                    route_TPL_all = df_ROUTE
                    ##--->> save data
                    route_TPL_all.to_csv(path_app + 'static/selected_route_TPL.csv')
                    import os
                    if os.path.exists(path_app + "static/selected_trip_path_TPL.txt"):
                        os.remove(path_app + "static/selected_trip_path_TPL.txt")
                    else:
                        print("The file does not exist")
                    with open(path_app + "static/selected_trip_path_TPL.txt", "w") as file:
                        for i in range(len(route_TPL_all)):
                            route_trip = (route_TPL_all[['trip']].iloc[i])[0]
                            if i < len(route_TPL_all) - 1:
                                file.write(str(route_trip) + ",\n")
                            else:
                                file.write(str(route_trip))

                    ## add "var name" in front of the .txt file, in order to properly loat it into the index.html file
                    with open(path_app + "static/selected_trip_path_TPL.txt", "r+") as f:
                        old = f.read()  # read everything in the file
                        f.seek(0)  # rewind
                        f.write("var routeLines_GTFS =[ \n" + old + "]")  # assign the "var name" in the .geojson file

                    ## get all the routes
                    routes_animation = [[x, y] for (x, y) in zip(route_TPL_all.route_ID, route_TPL_all.trip_headsign)]
                    with open(path_app + "static/selected_routes_and_trips_TPL.txt", "w") as file:
                        file.write(str(routes_animation))
                    with open(path_app + "static/selected_routes_and_trips_TPL.txt", "r+") as f:
                        old = f.read()  # read everything in the file
                        f.seek(0)  # rewind
                        f.write("var routes_and_trips = \n" + old)  # assign the "var name" in the .geojson file
                    ##---->> find all stops and time_stops ----###############################################
                    ## get only one stop sequence....for now.....as example....
                    stops_lat_lon = selected_trip.groupby(['stop_lat', 'stop_lon']).count().reset_index()
                    stops_lat_lon = stops_lat_lon[['stop_lat', 'stop_lon']]
                    selected_stops_trip = pd.merge(stops_lat_lon, selected_trip, on=['stop_lat', 'stop_lon'],
                                                   how='left')
                    ## drop duplicated and keep the first
                    selected_stops_trip = selected_stops_trip.drop_duplicates(subset=['stop_lat', 'stop_lon'],
                                                                              keep='first')
                    selected_stops_trip = selected_stops_trip[
                        ['stop_lon', 'stop_lat', 'route_short_name', 'trip_headsign', 'stop_id']]

                    all_stops_and_times = selected_trip.sort_values(['arrival_time'])
                    ## remove none values
                    all_stops_and_times = all_stops_and_times[all_stops_and_times['stop_lat'].notna()]
                    all_stops_and_times = all_stops_and_times[
                        ['arrival_time', 'stop_lat', 'stop_lon', 'route_short_name', 'trip_headsign', 'stop_id',
                         'stop_sequence', 'trip_id']]
                    ## merge with "stops" ti find the name of each stop
                    all_stops_and_times['stop_id'] = all_stops_and_times['stop_id'].astype(str)
                    all_stops_and_times = pd.merge(all_stops_and_times, stops[['stop_id', 'stop_name']], on=['stop_id'],
                                                   how='left')
                    df_stops_and_times = all_stops_and_times[
                        ['arrival_time', 'route_short_name', 'stop_name', 'trip_headsign', 'stop_sequence', 'trip_id']]
                    ##--->>> build a timetable for the chosen line within a given time.
                    df_stops_and_times = df_stops_and_times.sort_values(['trip_id', 'stop_sequence'])
                    ## save into csv file....
                    df_stops_and_times.to_csv(path_app + "static/selected_stops_and_times.csv")

                    selected_stops_trip['stop_id'] = selected_stops_trip['stop_id'].astype(str)
                    selected_stops_trip = pd.merge(selected_stops_trip, stops[['stop_id', 'stop_name']], on=['stop_id'],
                                                   how='left')
                    ## make a list of lists
                    lists_stops_route_times = all_stops_and_times.values.tolist()
                    lists_stops_route = selected_stops_trip.values.tolist()

                    with open(path_app + "static/selected_stops_TPL.txt", "w") as file:
                        file.write(str(lists_stops_route))
                    with open(path_app + "static/selected_stops_TPL.txt", "r+") as f:
                        old = f.read()  # read everything in the file
                        f.seek(0)  # rewind
                        f.write("var stop_names = \n" + old)  # assign the "var name" in the .geojson file

                    with open(path_app + "static/selected_timelines_TPL.txt", "w") as file:
                        file.write(str(lists_stops_route_times))
                    with open(path_app + "static/selected_timelines_TPL.txt", "r+") as f:
                        old = f.read()  # read everything in the file
                        f.seek(0)  # rewind
                        f.write("var timelines = \n" + old)  # assign the "var name" in the .geojson file

                except ValueError:
                    print("empty dataframe.....")
            except UnboundLocalError:
                print("empty dataframe.....")

            datum_hour = [{
                'GTFS_file': selected_GTFS_data,
                'TPL_line': selected_TPL_line,
                'hour': selected_TPL_hour,
                'viaggio': selected_trip_ID
            }]

            return render_template("index_animated_TPL_trip_selection.html", datum_hour=datum_hour)


@app.route('/stop_timelines/', methods=['GET', 'POST'])
def stop_timelines():
    df_stops_and_times = pd.read_csv(path_app + "static/selected_stops_and_times.csv")
    df_stops_and_times.reset_index(inplace=True)
    df_stops_and_times = df_stops_and_times[
        ['arrival_time', 'route_short_name', 'stop_name', 'trip_headsign', 'stop_sequence', 'trip_id']]

    ## convert to html with the vanilla structure
    df_stops_and_times_html = df_stops_and_times.to_html()
    #### render directly from string:
    resp = make_response(render_template_string(df_stops_and_times_html))
    return resp
    # return render_template("index_animated_TPL_selected.html")



#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
########### --- ZMU data ---------------------- #####################################

#############################################################
## ----- using "tod" type of day.............................

### select DATA TYPE  -------- #################################
@app.route('/data_type_selector/', methods=['GET', 'POST'])
def data_type_selector():

    if request.method == "POST":

        session["data_type"] = request.form.get("data_type")
        selected_data_type = session["data_type"]
        print("selected_data_type:", selected_data_type)
        selected_data_type = str(selected_data_type)

        with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_data_type))

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_data_type = int(selected_data_type)
        if selected_data_type == 11:  ## FCD data
            print("FCD data")
            print("selected_data_type:--------selector", selected_data_type)
            ## switch to table.........render....
            return render_template("index_zmu_select_day.html")

        elif selected_data_type == 12:  ## SYNTHETIC DATA
            print("SYNTHETIC DATA")
            print("selected_data_type:--------selector", selected_data_type)
            ## switch to table Synthetic data.....render.....
            return render_template("index_zmu_select_day.html")

        return render_template("index_zmu_select_day.html")




### select day (ZMU)...from Database
@app.route('/ZMU_day_selector/', methods=['GET', 'POST'])
def ZMU_day_selector():

    import glob
    # session["data_type"] = 11
    # selected_ZMU_day_start = '2022-10-04'
    # selected_ZMU_day_end = '2022-10-14'
    if request.method == "POST":
        # session["ZMU_tod"] = 6
        ###--->> record the ZMU_day in into the Flask Session
        ## TRY if session exists

        try:
            with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "r") as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
        except:
            stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
            stored_data_type_files.sort(key=os.path.getmtime)
            stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]
            with open(stored_data_type_file) as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)

        session["data_type"] = selected_data_type

        ##### ------ daterangepicker ----- ############################################
        ###############################################################################

        try:
            data = request.form["daterange"]
            session['input_data_range'] = data
            print("-------------data-------------:", data)
        except:
            data = "10/12/2022 - 10/13/2022"

        try:
            start_date = data.split(" - ")[0]
            start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            session["ZMU_day_start"] = str(start_date.date())
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("gotta!!!----->> selected_ZMU_day_start:", session["ZMU_day_start"])  ##--->> only get date
            selected_ZMU_day_start = str(selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            end_date = data.split(" - ")[1]
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            session["ZMU_day_end"] = str(end_date.date())
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("gotta!!!----->> selected_ZMU_day_end:", session["ZMU_day_end"])  ##--->> only get date
            selected_ZMU_day_end = str(selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable selected_ZMU_day_end: ", session["ZMU_day_end"])

        ##########################################################################################################

        user = session.sid
        print("user:", user)

        data_ZMU = [{
            'ZMU_day': selected_ZMU_day_start,
            'hour': 'choose hour'
        }]

        print("session user ID:", session.sid)
        # print("full session:", session)
        return render_template("index_zmu_select_day.html", data_ZMU=data_ZMU, var_ZMU_day=selected_ZMU_day_start,
                               user=user)





### select TRIP INDICATOR  -------- #################################
@app.route('/trip_indicator_selector/', methods=['GET', 'POST'])
def trip_indicator_selector():
    import glob

    if request.method == "POST":

        session["indicator_type"] = request.form.get("indicator_type")
        selected_indicator_type = session["indicator_type"]
        print("selected_indicator_type:", selected_indicator_type)
        selected_indicator_type = str(selected_indicator_type)

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_indicator_type = int(selected_indicator_type)
        if selected_indicator_type == 102:  ## TRIP COUNTS
            indicator = 'trip_counts'
            print("trip_counts")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)


        elif selected_indicator_type == 103:  ## TRIP TIME
            indicator = 'trip_time'
            print("trip_time")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 104:  ## TRIP DISTANCE
            indicator = 'trip_distance'
            print("trip_distance")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)

        elif selected_indicator_type == 105:  ## STOP TIME
            indicator = 'stop_time'
            print("stop_time")
            print("selected_indicator_type:--------selector", selected_indicator_type, indicator)


        with open(path_app + "static/params/selected_indicator_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_indicator_type))

        return render_template("index_zmu_select_day.html")




### select Time of DAY (TOD) -------- #################################
@app.route('/ZMU_tod_selector/', methods=['GET', 'POST'])
def ZMU_tod_selector():

    import glob

    if request.method == "POST":
        session["ZMU_tod"] = request.form.get("ZMU_tod")
        selected_ZMU_tod = session["ZMU_tod"]
        print("selected_ZMU_tod:", selected_ZMU_tod)
        selected_ZMU_tod = str(selected_ZMU_tod)

        session["check_ZMU_tod"] = session["ZMU_tod"]

        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_ZMU_tod))

        return render_template("index_zmu_select_day.html")




### select type of STAYPOINT -------- #################################
@app.route('/staypoints_type/', methods=['GET', 'POST'])
def staypoints_type():

    import glob

    if request.method == "POST":

        session["id_stay_type"] = request.form.get("id_stay_type")
        selected_stay_type = session["id_stay_type"]
        print("--------------selected_stay_type--------------------:", selected_stay_type)
        selected_stay_type = str(selected_stay_type)

        with open(path_app + "static/params/selected_stay_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_stay_type))

        with open(path_app + "static/params/selected_stay_type_" + session.sid + ".txt", "r") as file:
            selected_stay_type = file.read()
        print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)

        return render_template("index_zmu_select_day.html")



#############################################################
## ----- using "hourrange" ..................................

### select hour range and (ZMU) from Database
@app.route('/ZMU_hourrange_selector/', methods=['GET', 'POST'])
def ZMU_hourrange_selector():

    import pandas as pd
    import glob
    if request.method == "POST":

        # session["ZMU_tod"] = 6
        # selected_ZMU_hourrange = "1"
        # selected_ZMU_day_start = '2022-10-10'
        # selected_ZMU_day_end = '2022-10-11'
        # session["ZMU_tod"] = 6
        # tod = "W"
        # selected_ZMU_tod = 6
        # selected_stay_type = 21

        try:
            # selected_ZMU_day_start = session["ZMU_day_start"].strftime('%Y-%m-%d')
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("day from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("day from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])



        try:
            with open(path_app + "static/params/selected_indicator_type_" + session.sid + ".txt", "r") as file:
                selected_indicator_type = file.read()
            print("selected_indicator_type-------I AM HERE-----------: ", selected_indicator_type)
        except:
            stored_indicator_type_files = glob.glob(path_app + "static/params/selected_indicator_type_*.txt")
            stored_indicator_type_files.sort(key=os.path.getmtime)
            stored_indicator_type_file = stored_indicator_type_files[len(stored_indicator_type_files) - 1]
            with open(stored_indicator_type_file) as file:
                selected_indicator_type = file.read()
            print("selected_indicator_type-------I AM HERE-----------: ", selected_indicator_type)

        session["indicator_type"] = selected_indicator_type

        try:
            with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "r") as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
        except:
            stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
            stored_data_type_files.sort(key=os.path.getmtime)
            stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]
            with open(stored_data_type_file) as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)

        session["data_type"] = selected_data_type



        try:
            with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "r") as file:
                selected_ZMU_tod = file.read()
            print("selected_ZMU_tod-------I AM HERE-----------: ", selected_ZMU_tod)
        except:
            stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
            stored_tod_files.sort(key=os.path.getmtime)
            stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]
            with open(stored_tod_file) as file:
                selected_ZMU_tod = file.read()
            print("stored_tod_file-------I AM HERE-----------: ", selected_ZMU_tod)


        try:
            with open(path_app + "static/params/selected_stay_type_" + session.sid + ".txt", "r") as file:
                selected_stay_type = file.read()
            print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)
        except:
            stored_staypoint_files = glob.glob(path_app + "static/params/selected_stay_type_*.txt")
            stored_staypoint_files.sort(key=os.path.getmtime)
            stored_staypoint_file = stored_staypoint_files[len(stored_staypoint_files) - 1]
            with open(stored_staypoint_file) as file:
                selected_stay_type = file.read()
            print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)

        session["data_type"] = selected_data_type
        session["ZMU_tod"] = selected_ZMU_tod
        session["id_stay_type"] = selected_stay_type
        session["check_ZMU_tod"] = session["ZMU_tod"]



        ## --------- SELECT TOD -------- ##############
        selected_ZMU_tod = int(selected_ZMU_tod)
        if selected_ZMU_tod == 6:  ## WORKING day
            tod = "W"
        elif selected_ZMU_tod == 7:  ## PRE holiday
            tod = "P"
        elif selected_ZMU_tod == 8:  ## HOLIDAY
            tod = "H"
        elif selected_ZMU_tod == 9:  ## WORKING + PREHOLIDAYS + HOLIDAY
            tod = "WPH"

        ## --------- SELECT STAYPOINT -------- ##############
        selected_stay_type = int(selected_stay_type)
        if selected_stay_type == 21:  ## HOME
            stay_type = "H"
        elif selected_stay_type == 22:  ## WORK
            stay_type = "W"
        elif selected_stay_type == 23:  ## OTHER
            stay_type = "Home + Work"

        print("-----stay_type------------------------------------:", stay_type)
        print("-----selected_stay_type------------------------------------:", selected_stay_type)


        ## TRY if session exists
        try:
            session["ZMU_hourrange"] = request.form.get("ZMU_hourrange")
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
            selected_ZMU_hourrange = str(selected_ZMU_hourrange)
        except:
            session["ZMU_hourrange"] = 2
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])

        ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")


        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_hourrange = int(selected_ZMU_hourrange)
        if selected_ZMU_hourrange == 0:     ## 00:00 ---> 07:00
            hourrange_id = "N1"
        elif selected_ZMU_hourrange == 1:    ## 07:00 ----> 10:00
            hourrange_id = "M1"
        elif selected_ZMU_hourrange == 2:    ## 10:00 ---> 14:00
            hourrange_id = "M2"
        elif selected_ZMU_hourrange == 3:    ##  14:00 ---> 16:00
            hourrange_id = "A1"
        elif selected_ZMU_hourrange == 4:   ## 16:00 ---> 20:00
            hourrange_id = "A2"
        elif selected_ZMU_hourrange == 5:  ## 20:00 ---> 24:00
            hourrange_id = "A3"

        session["hourrange_id"] = hourrange_id
        print("------hourrange_id------------>>>:", hourrange_id)
        print("selected data type...........................................", selected_data_type)

        session["tod"] = tod
        print("----- tod------:", session["tod"])

        ######################################################################################
        #####----- make selection between FCD data and Synthetic data ------ #################
        ######################################################################################

        selected_data_type = int(selected_data_type)
        if selected_data_type == 11:  ## FCD data ##
            print("--------------------------------------------------------FCD data")
            ## switch to table.........TRIP----FCD data
            from sqlalchemy import create_engine
            from sqlalchemy import exc
            import sqlalchemy as sal
            from sqlalchemy.pool import NullPool

            engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
            from sqlalchemy.sql import text


            ####----- query all staypoints ----- #######################
            if (selected_stay_type == 21 or selected_stay_type == 22):
                query_all_staypoints = text('''SELECT count(id_staypoint),
                                                      id_zone
                                                      FROM fcd.staypoints
                                                                 WHERE
                                                                 fcd.staypoints.id_stay_type = :s
                                                                 AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                 GROUP BY
                                                                  id_zone''')

                stmt = query_all_staypoints.bindparams(s=str(stay_type))

            elif (selected_stay_type==23):
                query_all_staypoints = text('''SELECT count(id_staypoint),
                                                                 id_zone
                                                                 FROM fcd.staypoints
                                                                            WHERE  
                                                                            fcd.staypoints.id_stay_type != 'O'
                                                                            AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                            GROUP BY
                                                                             id_zone''')

                stmt = query_all_staypoints



            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            all_staypoints = pd.DataFrame(res)
            all_staypoints.rename({'id_zone': 'zmu'}, axis=1, inplace=True)
            all_staypoints.rename({'count': 'count_staypoints'}, axis=1, inplace=True)   ### all staypoints by zone
            all_staypoints.replace([np.inf, -np.inf], np.nan, inplace=True)
            all_staypoints = all_staypoints[
                all_staypoints['zmu'].notna()]
            all_staypoints['zmu'] = all_staypoints.zmu.astype('int')

            ##### ----- make geojson for staypoints --------- ###############################
            if (selected_stay_type == 21 or selected_stay_type == 22):
                query_staypoints = text('''SELECT id_staypoint, id_veh, n_points, name,
                                                          id_stay_type, lon, lat, id_zone
                                                             FROM fcd.staypoints 
                                                              WHERE (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                            AND id_stay_type=:s ''')
                stmt = query_staypoints.bindparams(s=str(stay_type))


            elif (selected_stay_type == 23):
                query_staypoints = text('''SELECT id_staypoint, id_veh, n_points, name,
                                                                       id_stay_type, lon, lat, id_zone
                                                                          FROM fcd.staypoints 
                                                                           WHERE (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                           AMD id_stay_type !='O' ''')
                stmt = query_staypoints
            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            df_staypoints = pd.DataFrame(res)

            ##-----> make a geodataframe with lat, lon, coordinates
            geometry = [Point(xy) for xy in zip(df_staypoints.lon, df_staypoints.lat)]
            crs = {'init': 'epsg:4326'}
            gdf_staypoints = GeoDataFrame(df_staypoints, crs=crs, geometry=geometry)
            ## save as .geojson file
            gdf_staypoints.to_file(filename=path_app + 'static/staypoints_tod.geojson',
                                   driver='GeoJSON')
            ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
            with open(path_app + 'static/staypoints_tod.geojson', 'r+', encoding='utf8',
                      errors='ignore') as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var points_staypoints = \n" + old)  # assign the "var name" in the .geojson file

            #################################################################################


            #### ---- query all trips having a staypoint ------#########
            ### staypoint = Home or WORK
            if (selected_stay_type == 21 or selected_stay_type == 22) and (selected_ZMU_tod != 9):
                query_trip_staypoints = text(''' SELECT fcd.trips.id_veh,
                                                        fcd.trips.geom,
                                                        fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                        fcd.trips.tod_o,fcd.trips.tod_d,
                                                        fcd.trips.dt_o,fcd.trips.dt_d,
                                                        fcd.trips.tt,fcd.trips.dist,
                                                        fcd.trips.p_after,  fcd.trips.p_before,
                                                        fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                        fcd.staypoints.id_stay_type
                
                                                        FROM fcd.staypoints
                                                        INNER JOIN 
                                                        fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                        WHERE 
                                                          date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                          AND fcd.trips.hour_range_o = :y
                                                          AND fcd.trips.tod_o = :z 
                                                          AND fcd.staypoints.id_stay_type = :s 
                                                        AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                 ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                                y=str(hourrange_id), z=str(tod), s=str(stay_type))

            ###### staypoint: home or work and all Time of days (W, P, H)
            elif (selected_stay_type == 21 or selected_stay_type == 22) and (selected_ZMU_tod == 9):
                query_trip_staypoints = text(''' SELECT fcd.trips.id_veh,
                                                                 fcd.trips.geom,
                                                                 fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                 fcd.trips.tod_o,fcd.trips.tod_d,
                                                                 fcd.trips.dt_o,fcd.trips.dt_d,
                                                                 fcd.trips.tt,fcd.trips.dist,
                                                                 fcd.trips.p_after,  fcd.trips.p_before,
                                                                 fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                 fcd.staypoints.id_stay_type

                                                                 FROM fcd.staypoints
                                                                 INNER JOIN 
                                                                 fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                 WHERE 
                                                                   date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                   AND fcd.trips.hour_range_o = :y
                                                                   AND fcd.staypoints.id_stay_type = :s 
                                                                 AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                          ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        y=str(hourrange_id), s=str(stay_type))
            ### staypoint = Home + WORK
            elif (selected_stay_type == 23) and  (selected_ZMU_tod != 9):
                query_trip_staypoints = text(''' SELECT fcd.trips.id_veh,
                                                                        fcd.trips.geom,
                                                                        fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                        fcd.trips.tod_o,fcd.trips.tod_d,
                                                                        fcd.trips.dt_o,fcd.trips.dt_d,
                                                                        fcd.trips.tt,fcd.trips.dist,
                                                                        fcd.trips.p_after,  fcd.trips.p_before,
                                                                        fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                        fcd.staypoints.id_stay_type

                                                                        FROM fcd.staypoints
                                                                        INNER JOIN 
                                                                        fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                        WHERE 
                                                                          date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                          AND fcd.trips.hour_range_o = :y
                                                                          AND fcd.trips.tod_o = :z 
                                                                        AND fcd.staypoints.id_stay_type != 'O' 
                                                                        AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                 ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        y=str(hourrange_id), z=str(tod))

            ### staypoint = Home + WORK and all Time of days (W, P, H)
            elif (selected_stay_type == 23) and (selected_ZMU_tod == 9):
                query_trip_staypoints = text(''' SELECT fcd.trips.id_veh,
                                                                                 fcd.trips.geom,
                                                                                 fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                                 fcd.trips.tod_o,fcd.trips.tod_d,
                                                                                 fcd.trips.dt_o,fcd.trips.dt_d,
                                                                                 fcd.trips.tt,fcd.trips.dist,
                                                                                 fcd.trips.p_after,  fcd.trips.p_before,
                                                                                 fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                                 fcd.staypoints.id_stay_type

                                                                                 FROM fcd.staypoints
                                                                                 INNER JOIN 
                                                                                 fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                                 WHERE 
                                                                                   date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                                   AND fcd.trips.hour_range_o = :y
                                                                                 AND fcd.staypoints.id_stay_type != 'O' 
                                                                                 AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                          ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        y=str(hourrange_id))

            print(selected_stay_type)
            print(selected_ZMU_tod)

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_destination_routes_day = pd.DataFrame(res)

            ## -----  get ZMU zones  -------- ################################
            ## function to transform Geometry from text to LINESTRING
            def wkb_tranformation(line):
                return wkb.loads(line.geom, hex=True)

            def wkb_tranformation_centroid(line):
                return wkb.loads(line.centroid, hex=True)

            ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
            ZMU_ROMA_with_population['centroid'] = ZMU_ROMA_with_population.apply(wkb_tranformation_centroid, axis=1)
            ZMU_ROMA_with_population = gpd.GeoDataFrame(ZMU_ROMA_with_population)

            ##### -------->>>> ORIGIN ----- ################################################################
            print( "origin_destination_routes_day"  , len(origin_destination_routes_day))
            print(selected_stay_type)
            print(selected_ZMU_tod)
            print(len(origin_destination_routes_day))

            origin_destination_routes_day.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
            ## merge with zmu zones
            try:
                routes_origin_destination = pd.merge(origin_destination_routes_day,
                                                     ZMU_ROMA_with_population[
                                                         ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                     on=['zmu'], how='left')
            except (KeyError, UnboundLocalError):
                print("----- I am here at abort -404----------")
                session["check_ZMU_tod"] = 1
                print(session["check_ZMU_tod"])
                return render_template("index_zmu_select_day.html")
                session["check_ZMU_tod"] = session["ZMU_tod"]
                print(session["check_ZMU_tod"])
                # abort(404)

            routes_origin_destination.rename({'zmu': 'zmu_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'index_zmu': 'index_zmu_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'area': 'area_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'nome_comun': 'nome_comun_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'quartiere': 'quartiere_origin'}, axis=1, inplace=True)

            ##### ------>>>>> DESTINATION
            routes_origin_destination.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
            ##merge with zmu zones
            routes_origin_destination = pd.merge(routes_origin_destination,
                                                 ZMU_ROMA_with_population[
                                                     ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                 on=['zmu'], how='left')
            routes_origin_destination.rename({'zmu': 'zmu_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'index_zmu': 'index_zmu_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'area': 'area_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'nome_comun': 'nome_comun_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'quartiere': 'quartiere_destination'}, axis=1, inplace=True)

            ## merge ORIGIN and DESTINATION routes by 'idtrajectory'
            routes = routes_origin_destination
            routes.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
            routes.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
            routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)

            ## transform geom into linestring....projection is in meters epsg:6875
            routes['geom'] = routes.apply(wkb_tranformation, axis=1)
            routes = gpd.GeoDataFrame(routes)
            routes.rename({'geom': 'geometry'}, axis=1, inplace=True)

            ## reference system = 6875 (in meters)
            routes = routes.set_geometry("geometry")
            routes = routes.set_crs('epsg:6875', allow_override=True)

            ## convert into lat , lon
            routes = routes.to_crs({'init': 'epsg:4326'})
            routes = routes.set_crs('epsg:4326', allow_override=True)

            ## transfor hours as integer
            routes['triptime_s'] = routes['triptime_s'].astype(int)

            ##### ---->>> aggregation @ ORIGIN
            ## grouby + counts....only if you want to estimate the NUMBER of vehicles
            aggregated_zmu_origin = routes[['index_zmu_origin', 'zmu_origin']].groupby(
                ['index_zmu_origin', 'zmu_origin'],
                sort=False).size().reset_index().rename(columns={0: 'counts'})



            mean_aggregated_zmu_origin = routes[['index_zmu_origin', 'zmu_origin', 'triptime_s', 'breaktime_s', 'dist']].groupby(['index_zmu_origin', 'zmu_origin'],
                                    sort=False).mean().reset_index().rename(
                columns={0: 'means'})
            mean_aggregated_zmu_origin.rename({'triptime_s': 'mean_triptime_m'}, axis=1, inplace=True)
            mean_aggregated_zmu_origin['mean_triptime_m'] = (mean_aggregated_zmu_origin['mean_triptime_m']) / 60
            mean_aggregated_zmu_origin.rename({'breaktime_s': 'mean_breaktime_m'}, axis=1, inplace=True)
            mean_aggregated_zmu_origin['mean_breaktime_m'] = (mean_aggregated_zmu_origin['mean_breaktime_m']) / 60
            mean_aggregated_zmu_origin.rename({'dist': 'mean_tripdistance_m'}, axis=1, inplace=True)



            ## merge data together ------########################################################
            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, mean_aggregated_zmu_origin, on=['zmu_origin', 'index_zmu_origin'],
                                                   how='left')
            ## merge trip counts @destination with total staypoints in each traffic ZONE ZMU
            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, all_staypoints,
                                                   left_on='zmu_origin', right_on='zmu')

            ### NORMALIZE each cont @destination with the number of staypoints in each traffic zone
            aggregated_zmu_origin['counts_norm'] = aggregated_zmu_origin.counts / 1

            aggregated_zmu_origin = aggregated_zmu_origin[
                              ['index_zmu_origin','zmu', 'counts_norm', 'mean_triptime_m', 'mean_breaktime_m',
                               'mean_tripdistance_m', 'count_staypoints']]

            aggregated_zmu_origin['zmu'] = aggregated_zmu_origin.zmu.astype('int')
            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, ZMU_ROMA_with_population, on=['zmu'],
                                                   how='left')

            aggregated_zmu_origin.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_zmu_origin['counts_norm'] = round(aggregated_zmu_origin['counts_norm'], 2)

            print(
                "-------- I am HERE .....FCD-------------------------------------------------------------------------------")



            ################################################################################################
            #######--------------------------------------------- ###########################################
            ###--->>> get aggregation by DAY <<---------------------########################################



            #### ---- query all trips having a staypoint ------#########
            ### staypoint = Home or WORK
            if (selected_stay_type == 21 or selected_stay_type == 22) and  (selected_ZMU_tod != 9):
                query_origin_destination_routes_day = text(''' SELECT fcd.trips.id_veh,
                                                                  /*fcd.trips.geom,*/
                                                                  fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                  fcd.trips.tod_o,fcd.trips.tod_d,
                                                                  fcd.trips.dt_o,fcd.trips.dt_d,
                                                                  fcd.trips.tt,fcd.trips.dist,
                                                                  fcd.trips.p_after,  fcd.trips.p_before,
                                                                  fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                  fcd.staypoints.id_stay_type,
                                                                  fcd.trips.geom,
                                                                   date_part('hour', dt_o) as hr, 
                                                                   TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
    
                                                                  FROM fcd.staypoints
                                                                  INNER JOIN 
                                                                  fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                  WHERE 
                                                                    date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                    AND fcd.trips.tod_o = :z 
                                                                    AND fcd.staypoints.id_stay_type = :s 
                                                                  AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                           ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        z=str(tod), s=str(stay_type))

            ### staypoint = Home or WORK and all Time of days (W, P, H)
            elif (selected_stay_type == 21 or selected_stay_type == 22) and  (selected_ZMU_tod == 9):
                query_origin_destination_routes_day = text(''' SELECT fcd.trips.id_veh,
                                                                         /*fcd.trips.geom,*/
                                                                         fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                         fcd.trips.tod_o,fcd.trips.tod_d,
                                                                         fcd.trips.dt_o,fcd.trips.dt_d,
                                                                         fcd.trips.tt,fcd.trips.dist,
                                                                         fcd.trips.p_after,  fcd.trips.p_before,
                                                                         fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                         fcd.staypoints.id_stay_type,
                                                                         fcd.trips.geom,
                                                                          date_part('hour', dt_o) as hr, 
                                                                          TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day

                                                                         FROM fcd.staypoints
                                                                         INNER JOIN 
                                                                         fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                         WHERE 
                                                                           date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                           AND fcd.staypoints.id_stay_type = :s 
                                                                         AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                  ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start),
                                                                      xx=str(selected_ZMU_day_end),
                                                                      s=str(stay_type))


            ### staypoint = Home + WORK
            elif (selected_stay_type == 23) and  (selected_ZMU_tod != 9):
                query_origin_destination_routes_day = text(''' SELECT fcd.trips.id_veh,
                                                                             /*fcd.trips.geom,*/
                                                                             fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                             fcd.trips.tod_o,fcd.trips.tod_d,
                                                                             fcd.trips.dt_o,fcd.trips.dt_d,
                                                                             fcd.trips.tt,fcd.trips.dist,
                                                                             fcd.trips.p_after,  fcd.trips.p_before,
                                                                             fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                             fcd.staypoints.id_stay_type,
                                                                             fcd.trips.geom,
                                                                              date_part('hour', dt_o) as hr, 
                                                                              TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
    
                                                                             FROM fcd.staypoints
                                                                             INNER JOIN 
                                                                             fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                             WHERE 
                                                                               date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                               AND fcd.trips.tod_o = :z 
                                                                              AND fcd.staypoints.id_stay_type != 'O'
                                                                             AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                      ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start),
                                                                      xx=str(selected_ZMU_day_end),
                                                                      z=str(tod))

            ### staypoint = Home + WORK and all Time of day (W, P, H)
            elif (selected_stay_type == 23) and  (selected_ZMU_tod == 9):
                query_origin_destination_routes_day = text(''' SELECT fcd.trips.id_veh,
                                                                                            /*fcd.trips.geom,*/
                                                                                            fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                                            fcd.trips.tod_o,fcd.trips.tod_d,
                                                                                            fcd.trips.dt_o,fcd.trips.dt_d,
                                                                                            fcd.trips.tt,fcd.trips.dist,
                                                                                            fcd.trips.p_after,  fcd.trips.p_before,
                                                                                            fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                                            fcd.staypoints.id_stay_type,
                                                                                            fcd.trips.geom,
                                                                                             date_part('hour', dt_o) as hr, 
                                                                                             TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day

                                                                                            FROM fcd.staypoints
                                                                                            INNER JOIN 
                                                                                            fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                                            WHERE 
                                                                                              date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                                             AND fcd.staypoints.id_stay_type != 'O'
                                                                                            AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                                     ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start),
                                                                      xx=str(selected_ZMU_day_end))

            print(selected_stay_type)
            print(selected_ZMU_tod)


            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_destination_routes_day = pd.DataFrame(res)


            ##### -------->>>> ORIGIN
            origin_destination_routes_day.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
            ##merge with zmu zones
            origin_destination_routes_day = pd.merge(origin_destination_routes_day,
                                                     ZMU_ROMA_with_population[
                                                         ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                     on=['zmu'], how='left')
            origin_destination_routes_day.rename({'zmu': 'zmu_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'index_zmu': 'index_zmu_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'area': 'area_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'nome_comun': 'nome_comun_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'quartiere': 'quartiere_origin'}, axis=1, inplace=True)

            ##### ------>>>>> DESTINATION
            origin_destination_routes_day.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
            ##merge with zmu zones
            origin_destination_routes_day = pd.merge(origin_destination_routes_day,
                                                     ZMU_ROMA_with_population[
                                                         ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                     on=['zmu'], how='left')
            origin_destination_routes_day.rename({'zmu': 'zmu_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'index_zmu': 'index_zmu_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'area': 'area_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'nome_comun': 'nome_comun_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'quartiere': 'quartiere_destination'}, axis=1, inplace=True)

            ## merge ORIGIN and DESTINATION routes by 'idtrajectory'
            origin_destination_routes_day.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['triptime_s'] > 0]
            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['breaktime_s'] > 0]
            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['tripdistance_m'] > 0]

            ### ----- @ ORIGINS ---------------------------------- ##################################################

            aggregated_zmu_origin_day = origin_destination_routes_day[['hr', 'zmu_origin']].groupby(
                ['hr', 'zmu_origin'], sort=False).size().reset_index().rename(columns={0: 'counts'})


            ## merge trip counts @destination with total staypoints in each traffic ZONE ZMU
            aggregated_zmu_origin_day = pd.merge(aggregated_zmu_origin_day, all_staypoints,
                                                   left_on='zmu_origin', right_on='zmu')

            aggregated_zmu_origin_day[
                'counts_norm'] = aggregated_zmu_origin_day.counts / 1


            aggregated_zmu_origin_day.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_zmu_origin_day['counts_norm'] = round(aggregated_zmu_origin_day['counts_norm'], 2)

            ## remove none values
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[
                aggregated_zmu_origin_day['zmu_origin'].notna()]
            aggregated_zmu_origin_day['zmu_origin'] = aggregated_zmu_origin_day.zmu_origin.astype(
                'int')

            ## merge with zmu to get geometries.....
            ## get geometry from "ZMU_ROMA"
            aggregated_zmu_origin_day['zmu'] = aggregated_zmu_origin_day.zmu.astype('int')
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[['hr', 'zmu', 'counts', 'count_staypoints', 'counts_norm']]
            aggregated_zmu_origin_day = pd.merge(aggregated_zmu_origin_day, ZMU_ROMA_with_population,
                                                       on=['zmu'], how='left')
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[
                aggregated_zmu_origin_day['index_zmu'].notna()]
            aggregated_zmu_origin_day['index_zmu'] = aggregated_zmu_origin_day.index_zmu.astype('int')

            aggregated_zmu_origin_day = aggregated_zmu_origin_day[
                ['counts_norm', 'index_zmu', 'POP_TOT_ZMU', 'zmu', 'hr', 'nome_comun', 'quartiere']]

            #### ------->>>> groupby + mean triptime, tripdistance, breaktime <<<-----------###########################################

            origin_destination_routes_day.rename({'zmu_origin': 'zmu'}, axis=1, inplace=True)
            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['zmu'].notna()]
            origin_destination_routes_day['zmu'] = origin_destination_routes_day.zmu.astype('int')

            aggregated_means_zmu_origin = origin_destination_routes_day[
                ['zmu', 'hr', 'triptime_s', 'breaktime_s', 'tripdistance_m']].groupby(['hr', 'zmu'],
                                                                                             sort=False).mean().reset_index().rename(
                columns={0: 'means'})
            ## convert triptime_s into minutes
            aggregated_means_zmu_origin['triptime_m'] = (aggregated_means_zmu_origin['triptime_s']) / 60
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['triptime_s'].notna()]
            aggregated_means_zmu_origin['triptime_m'] = aggregated_means_zmu_origin.triptime_m.astype('int')
            ## convert breaktime_s into minutes
            aggregated_means_zmu_origin['breaktime_m'] = (aggregated_means_zmu_origin['breaktime_s']) / 60
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['breaktime_m'].notna()]
            aggregated_means_zmu_origin['breaktime_m'] = aggregated_means_zmu_origin.breaktime_m.astype('int')
            ## convert tripdistance_m
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['tripdistance_m'].notna()]
            aggregated_means_zmu_origin['tripdistance_m'] = aggregated_means_zmu_origin.tripdistance_m.astype(
                'int')

            aggregated_means_zmu_origin = pd.merge(aggregated_means_zmu_origin, aggregated_zmu_origin_day,
                                                      on=['zmu', 'hr'], how='left')

            aggregated_means_zmu_origin.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['counts_norm'].notna()]


            ##############################################################################################################################
            ## compute total counts over ALL ZONES for a given hour-range, and compute total mean FOR ALL ZONEs for a given hour-range
            aggregated_zmu_origin_day.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[aggregated_zmu_origin_day['counts_norm'].notna()]
            #aggregated_zmu_destinations = aggregated_zmu_destinations[aggregated_zmu_destinations['counts'].notna()]

            #### make the means ove the 24hours
            aggregated_24h_mean = aggregated_means_zmu_origin[
                ['zmu', 'triptime_m', 'breaktime_m', 'tripdistance_m']].groupby(['zmu'],
                                                                                sort=False).mean().reset_index().rename(
                columns={0: 'means'})

            aggragated_24h_counts = aggregated_means_zmu_origin[['counts_norm', 'zmu']].groupby(
                ['zmu'],  sort=False).size().reset_index().rename(columns={0: 'counts'})    ### over 1000 inhabitants

            aggregated_24h_mean = pd.merge(aggregated_24h_mean, aggragated_24h_counts,
                                                        on=['zmu'], how='left')

            aggregated_24h_mean.rename({'triptime_m': 'mean_triptime_m'}, axis=1, inplace=True)
            aggregated_24h_mean.rename({'breaktime_m': 'mean_breaktime_m'}, axis=1, inplace=True)
            aggregated_24h_mean.rename({'tripdistance_m': 'mean_tripdistance_m'}, axis=1, inplace=True)
            aggregated_24h_mean.rename({'counts': 'counts24'}, axis=1, inplace=True)

            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin[[ 'index_zmu_origin', 'zmu', 'index_zmu', 'POP_TOT_ZMU', 'counts_norm',
                            'area', 'comune', 'nome_comun', 'quartiere', 'pgtu', 'municipio', 'lon',
                              'lat', 'centroid', 'geometry']], aggregated_24h_mean,
                                           on=['zmu'], how='left')

            aggregated_zmu_origin['mean_triptime_m'] = round(aggregated_zmu_origin.mean_triptime_m, ndigits=2)
            aggregated_zmu_origin['mean_tripdistance_m'] = round(aggregated_zmu_origin.mean_tripdistance_m,
                                                                   ndigits=2)
            aggregated_zmu_origin['mean_breaktime_m'] = round(aggregated_zmu_origin.mean_breaktime_m,
                                                                   ndigits=2)


            TOTAL_TRIPS_COUNTS = max(aggregated_zmu_origin.counts24)    ## per 1000 inhabitants
            TOTAL_MAX_TRIPTIME = np.max(aggregated_zmu_origin.mean_triptime_m)
            TOTAL_MAX_BREAKTIME = np.max(aggregated_zmu_origin.mean_breaktime_m)
            TOTAL_MAX_TRIPDISTANCE = np.max(aggregated_zmu_origin.mean_tripdistance_m)

            ## INDICATORs for RADAR of POLAR CHARTS (compute PERCENTAGES within the chosen hourrange compared to the total OVER ALL ZONES)
            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['counts24'].notna()]
            aggregated_zmu_origin['radial_counts'] = aggregated_zmu_origin['counts24'] * 100 / TOTAL_TRIPS_COUNTS

            aggregated_zmu_origin['radial_counts'] = round(aggregated_zmu_origin.radial_counts, ndigits=4)

            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['mean_triptime_m'].notna()]
            aggregated_zmu_origin['radial_mean_triptime'] = (aggregated_zmu_origin['mean_triptime_m']) * 100 / TOTAL_MAX_TRIPTIME
            aggregated_zmu_origin['radial_mean_triptime'] = round(aggregated_zmu_origin.radial_mean_triptime, ndigits=2)

            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['mean_breaktime_m'].notna()]
            aggregated_zmu_origin['radial_mean_breaktime'] = (aggregated_zmu_origin['mean_breaktime_m']) * 100 / TOTAL_MAX_BREAKTIME
            aggregated_zmu_origin['radial_mean_breaktime'] = round(aggregated_zmu_origin.radial_mean_breaktime, ndigits=2)

            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['mean_tripdistance_m'].notna()]
            aggregated_zmu_origin['radial_mean_tripdistance'] = (aggregated_zmu_origin['mean_tripdistance_m']) * 100 / TOTAL_MAX_TRIPDISTANCE
            aggregated_zmu_origin['radial_mean_tripdistance'] = round(aggregated_zmu_origin.radial_mean_tripdistance, ndigits=2)

            ####################################################################################
            ## radar chart over a single ZMU for a given hour range ###########################


            ## classify by scores...
            aggregated_zmu_origin['score_trip_counts'] = 0
            aggregated_zmu_origin['score_trip_time'] = 0
            aggregated_zmu_origin['score_breaktime'] = 0
            aggregated_zmu_origin['score_trip_distance'] = 0
            aggregated_zmu_origin['mark_trip_counts'] = 0
            aggregated_zmu_origin['mark_trip_time'] = 0
            aggregated_zmu_origin['mark_breaktime'] = 0
            aggregated_zmu_origin['mark_trip_distance'] = 0

            ### number of trips
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_counts.iloc[i] >= 0) and (aggregated_zmu_origin.radial_counts.iloc[i] <= 30):
                    aggregated_zmu_origin.score_trip_counts.iloc[i]=1
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_counts.iloc[i] > 30) and (aggregated_zmu_origin.radial_counts.iloc[i] <= 60):
                    aggregated_zmu_origin.score_trip_counts.iloc[i] = 2
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_counts.iloc[i] > 60) and (
                                aggregated_zmu_origin.radial_counts.iloc[i] <= 80):
                    aggregated_zmu_origin.score_trip_counts.iloc[i] = 3
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_counts.iloc[i] > 80) and (
                            aggregated_zmu_origin.radial_counts.iloc[i] <= max(aggregated_zmu_origin.radial_counts)):
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Relevant"
                    aggregated_zmu_origin.score_trip_counts.iloc[i] = 4


            #### mean trip time
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_mean_triptime.iloc[i] >= 0) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= 15):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 1
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_mean_triptime.iloc[i] > 15) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= 20):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 2
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_mean_triptime.iloc[i] > 20) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= 30):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 3
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_mean_triptime.iloc[i] > 30) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= max(aggregated_zmu_origin.radial_mean_triptime)):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 4
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Relevant"

            #### mean stop time or breaktime
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] >= 0) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= 5):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 1
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] > 5) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= 15):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 2
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] > 15) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= 25):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 3
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] > 25) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= max(
                    aggregated_zmu_origin.radial_mean_breaktime)):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 4
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Relevant"


            #### mean trip_distance
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] >= 0) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= 5):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 1
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] > 5) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= 15):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 2
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] > 15) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= 25):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 3
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] > 25) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= max(
                    aggregated_zmu_origin.radial_mean_tripdistance)):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 4
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Relevant"


            #### save data into .csv format ###################################################
            #####----->>> save csv file ---- ##################################################
            csv_aggregated_zmu_origin = aggregated_zmu_origin[[ 'index_zmu_origin', 'zmu','score_trip_counts', 'score_trip_time', 'score_breaktime',
              'score_trip_distance', 'mark_trip_counts', 'mark_trip_time',
                'mark_breaktime', 'mark_trip_distance']]
            csv_aggregated_zmu_origin.to_csv(
                path_app + 'static/csv_aggregated_zmu_origin_' + session.sid + '.csv')

            ##########################################################################################################
            ##########################################################################################################

            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                ['counts_norm', 'hr', 'zmu', 'triptime_s', 'breaktime_s', 'tripdistance_m',
                 'triptime_m', 'breaktime_m']]

            ## merge with zmu to get geometries.....
            ## get geometry from "ZMU_ROMA"
            aggregated_means_zmu_origin = pd.merge(aggregated_means_zmu_origin, ZMU_ROMA_with_population,
                                                        on=['zmu'], how='left')
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                ['index_zmu', 'zmu', 'hr', 'tripdistance_m',
                 'triptime_m', 'breaktime_m', 'nome_comun', 'quartiere']]

            ### -----> merge all data together ---- ###################################################################
            aggregated_zmu_origin_day = pd.merge(aggregated_zmu_origin_day,
                                                       aggregated_means_zmu_origin,
                                                       on=['index_zmu', 'zmu', 'hr', 'nome_comun', 'quartiere'],
                                                       how='left')

            #####----->>> save csv file ---- ##################################################
            aggregated_means_zmu_origin['counts_norm'] = round(aggregated_zmu_origin_day['counts_norm'], 2)
            aggregated_zmu_origin_day.to_csv(
                path_app + 'static/aggregated_zmu_origin_day_' + session.sid + '.csv')

            ### add field color-hex.....
            color_values = ['#00e31c48', '#09f60065', '#09f60052', '#00e31c37', '#00ee116b', '#00926d42', '#009e6154',
                            '#06f9006f']
            from itertools import islice, cycle
            aggregated_zmu_origin['color_hex'] = list(
                islice(cycle(color_values), len(aggregated_zmu_origin)))

            ## remove "centroid" column
            aggregated_zmu_origin.drop(['centroid'], axis=1, inplace=True)

            try:
                aggregated_zmu_origin = gpd.GeoDataFrame(aggregated_zmu_origin)
            except IndexError:
                abort(404)

            ## save as .geojson file
            aggregated_zmu_origin.to_file(filename=path_app + 'static/aggregated_zmu_filtered.geojson',
                                                driver='GeoJSON')
            ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
            with open(path_app + "static/aggregated_zmu_filtered.geojson", "r+") as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var aggregated_matched_routes_zmu = \n" + old)  # assign the "var name" in the .geojson file

            ### convert Geodataframe into .geojson...
            session["aggregated_zmu_origin"] = aggregated_zmu_origin.to_json()
            print("------ I am here----- SESSION Colored ZMUs--------------------------")
            return render_template("index_zmu_select_hour.html",
                                   var_ZMU_day=selected_ZMU_day_start, session_aggregated_zmu_origin = session["aggregated_zmu_origin"])



        elif selected_data_type == 12:  ## SYNTHETIC DATA ##
            print("---------------------------------------------------SYNTHETIC DATA")
            ## switch to table SYNTHETIC data.....

            ### ---> get filtered data of ZMU 'test' table  <--- ####################################
            #########################################################################################
            #########################################################################################

            ########################### ----------------------------------- ###########
            ########################### ----------------------------------- ###########
            ########################### ----------------------------------- ###########
            ########################### ----------------------------------- ###########
            ########################### ----------------------------------- ###########
            ########################### ----------------------------------- ###########

            print("-----------NEW SYNTHETIC data from CARLO--------------------------")
            
            from sqlalchemy import create_engine
            from sqlalchemy import exc
            import sqlalchemy as sal
            from sqlalchemy.pool import NullPool

            engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
            from sqlalchemy.sql import text


            ####----- query all staypoints ----- #######################
            if (selected_stay_type == 21 or selected_stay_type == 22):
                query_all_staypoints = text('''SELECT count(id_staypoint),
                                                      id_zone
                                                      FROM fcd.staypoints
                                                                 WHERE
                                                                 fcd.staypoints.id_stay_type = :s
                                                                 AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                 GROUP BY
                                                                  id_zone''')

                stmt = query_all_staypoints.bindparams(s=str(stay_type))

            elif (selected_stay_type==23):
                query_all_staypoints = text('''SELECT count(id_staypoint),
                                                                 id_zone
                                                                 FROM fcd.staypoints
                                                                            WHERE  
                                                                            fcd.staypoints.id_stay_type != 'O'
                                                                            AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                            GROUP BY
                                                                             id_zone''')

                stmt = query_all_staypoints



            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            all_staypoints = pd.DataFrame(res)
            all_staypoints.rename({'id_zone': 'zmu'}, axis=1, inplace=True)
            all_staypoints.rename({'count': 'count_staypoints'}, axis=1, inplace=True)   ### all staypoints by zone
            all_staypoints.replace([np.inf, -np.inf], np.nan, inplace=True)
            all_staypoints = all_staypoints[
                all_staypoints['zmu'].notna()]
            all_staypoints['zmu'] = all_staypoints.zmu.astype('int')

            ##### ----- make geojson for staypoints --------- ###############################
            if (selected_stay_type == 21 or selected_stay_type == 22):
                query_staypoints = text('''SELECT id_staypoint, id_veh, n_points, name,
                                                          id_stay_type, lon, lat, id_zone
                                                             FROM fcd.staypoints 
                                                              WHERE (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                            AND id_stay_type=:s ''')
                stmt = query_staypoints.bindparams(s=str(stay_type))


            elif (selected_stay_type == 23):
                query_staypoints = text('''SELECT id_staypoint, id_veh, n_points, name,
                                                                       id_stay_type, lon, lat, id_zone
                                                                          FROM fcd.staypoints 
                                                                           WHERE (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                           AMD id_stay_type !='O' ''')
                stmt = query_staypoints
            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            df_staypoints = pd.DataFrame(res)

            ##-----> make a geodataframe with lat, lon, coordinates
            geometry = [Point(xy) for xy in zip(df_staypoints.lon, df_staypoints.lat)]
            crs = {'init': 'epsg:4326'}
            gdf_staypoints = GeoDataFrame(df_staypoints, crs=crs, geometry=geometry)
            ## save as .geojson file
            gdf_staypoints.to_file(filename=path_app + 'static/staypoints_tod.geojson',
                                   driver='GeoJSON')
            ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
            with open(path_app + 'static/staypoints_tod.geojson', 'r+', encoding='utf8',
                      errors='ignore') as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var points_staypoints = \n" + old)  # assign the "var name" in the .geojson file

            #################################################################################

            #### ---- query all trips having a staypoint ------#########
            # selected_ZMU_day_start = '2022-10-06'
            # selected_ZMU_day_end = '2022-10-07'
           
            ### staypoint = Home or WORK
            if (selected_stay_type == 21 or selected_stay_type == 22) and (selected_ZMU_tod != 9):
                query_trip_staypoints = text(''' SELECT synt.trips.id_veh,
                                                        synt.trips.geom,
                                                        synt.trips.id_zone_o, synt.trips.id_zone_d,
                                                        synt.trips.tod_o,synt.trips.tod_d,
                                                        synt.trips.dt_o,synt.trips.dt_d,
                                                        synt.trips.tt,synt.trips.dist,
                                                        synt.trips.p_after,  synt.trips.p_before,
                                                        synt.trips.hour_range_o,synt.trips.hour_range_d               
                                                        FROM synt.trips
                                                        WHERE 
                                                          date(synt.trips.dt_o) BETWEEN :x AND :xx 
                                                          AND synt.trips.hour_range_o = :y
                                                          AND synt.trips.tod_o = :z      ''')

                
                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                                y=str(hourrange_id), z=str(tod))                                                                
                                                                
            ###### staypoint: home or work and all Time of days (W, P, H)
            elif (selected_stay_type == 21 or selected_stay_type == 22) and (selected_ZMU_tod == 9):
                query_trip_staypoints = text(''' SELECT synt.trips.id_veh,
                                                                 synt.trips.geom,
                                                                 synt.trips.id_zone_o, synt.trips.id_zone_d,
                                                                 synt.trips.tod_o,synt.trips.tod_d,
                                                                 synt.trips.dt_o,synt.trips.dt_d,
                                                                 synt.trips.tt,synt.trips.dist,
                                                                 synt.trips.p_after,  synt.trips.p_before,
                                                                 synt.trips.hour_range_o,synt.trips.hour_range_d
                                                                 FROM synt.trips
                                                                 WHERE 
                                                                   date(synt.trips.dt_o) BETWEEN :x AND :xx 
                                                                   AND synt.trips.hour_range_o = :y   ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        y=str(hourrange_id))

            ### staypoint = Home + WORK
            elif (selected_stay_type == 23) and  (selected_ZMU_tod != 9):
                query_trip_staypoints = text(''' SELECT synt.trips.id_veh,
                                                                        synt.trips.geom,
                                                                        synt.trips.id_zone_o, synt.trips.id_zone_d,
                                                                        synt.trips.tod_o,synt.trips.tod_d,
                                                                        synt.trips.dt_o,synt.trips.dt_d,
                                                                        synt.trips.tt,synt.trips.dist,
                                                                        synt.trips.p_after,  synt.trips.p_before,
                                                                        synt.trips.hour_range_o,synt.trips.hour_range_d
                                                                
                                                                        FROM synt.trips
                                                                        WHERE 
                                                                          date(synt.trips.dt_o) BETWEEN :x AND :xx 
                                                                          AND synt.trips.hour_range_o = :y
                                                                          AND synt.trips.tod_o = :z    ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        y=str(hourrange_id), z=str(tod))


            ### staypoint = Home + WORK and all Time of days (W, P, H)
            elif (selected_stay_type == 23) and (selected_ZMU_tod == 9):
                query_trip_staypoints = text(''' SELECT synt.trips.id_veh,
                                                                     synt.trips.geom,
                                                                     synt.trips.id_zone_o, synt.trips.id_zone_d,
                                                                     synt.trips.tod_o,synt.trips.tod_d,
                                                                     synt.trips.dt_o,synt.trips.dt_d,
                                                                     synt.trips.tt,synt.trips.dist,
                                                                     synt.trips.p_after,  synt.trips.p_before,
                                                                     synt.trips.hour_range_o,synt.trips.hour_range_d
                                                                
                                                                     FROM synt.trips
                                                                     WHERE 
                                                                       date(synt.trips.dt_o) BETWEEN :x AND :xx 
                                                                       AND synt.trips.hour_range_o = :y
                                                                          ''')

                stmt = query_trip_staypoints.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        y=str(hourrange_id))

            print(selected_stay_type)
            print(selected_ZMU_tod)

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_destination_routes_day = pd.DataFrame(res)



            ## -----  get ZMU zones  -------- ################################
            ## function to transform Geometry from text to LINESTRING
            def wkb_tranformation(line):
                return wkb.loads(line.geom, hex=True)

            def wkb_tranformation_centroid(line):
                return wkb.loads(line.centroid, hex=True)

            ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
            ZMU_ROMA_with_population['centroid'] = ZMU_ROMA_with_population.apply(wkb_tranformation_centroid, axis=1)
            ZMU_ROMA_with_population = gpd.GeoDataFrame(ZMU_ROMA_with_population)

            ##### -------->>>> ORIGIN ----- ################################################################
            print( "origin_destination_routes_day"  , len(origin_destination_routes_day))
            print(selected_stay_type)
            print(selected_ZMU_tod)

            origin_destination_routes_day.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)


            ## merge with zmu zones
            try:
                routes_origin_destination = pd.merge(origin_destination_routes_day,
                                                     ZMU_ROMA_with_population[
                                                         ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                     on=['zmu'], how='left')
            except (KeyError, UnboundLocalError):
                print("----- I am here at abort -404----------")
                session["check_ZMU_tod"] = 1
                print(session["check_ZMU_tod"])
                return render_template("index_zmu_select_day.html")
                session["check_ZMU_tod"] = session["ZMU_tod"]
                print(session["check_ZMU_tod"])
                # abort(404)

            routes_origin_destination.rename({'zmu': 'zmu_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'index_zmu': 'index_zmu_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'area': 'area_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'nome_comun': 'nome_comun_origin'}, axis=1, inplace=True)
            routes_origin_destination.rename({'quartiere': 'quartiere_origin'}, axis=1, inplace=True)





            ##### ------>>>>> DESTINATION
            routes_origin_destination.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
            ##merge with zmu zones
            routes_origin_destination = pd.merge(routes_origin_destination,
                                                 ZMU_ROMA_with_population[
                                                     ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                 on=['zmu'], how='left')
            routes_origin_destination.rename({'zmu': 'zmu_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'index_zmu': 'index_zmu_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'area': 'area_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'nome_comun': 'nome_comun_destination'}, axis=1, inplace=True)
            routes_origin_destination.rename({'quartiere': 'quartiere_destination'}, axis=1, inplace=True)

            AAA = routes_origin_destination.zmu_origin
            AAA.drop_duplicates(inplace=True)

            ## merge ORIGIN and DESTINATION routes by 'idtrajectory'
            routes = routes_origin_destination
            routes.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
            routes.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
            routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)

            ## transform geom into linestring....projection is in meters epsg:6875
            routes['geom'] = routes.apply(wkb_tranformation, axis=1)
            routes = gpd.GeoDataFrame(routes)
            routes.rename({'geom': 'geometry'}, axis=1, inplace=True)

            ## reference system = 6875 (in meters)
            routes = routes.set_geometry("geometry")
            routes = routes.set_crs('epsg:6875', allow_override=True)

            ## convert into lat , lon
            routes = routes.to_crs({'init': 'epsg:4326'})
            routes = routes.set_crs('epsg:4326', allow_override=True)

            AAA = routes.zmu_origin
            AAA.drop_duplicates(inplace=True)
            # AAAA = pd.DataFrame(routes)

            routes = routes[routes['triptime_s'].notna()]
            routes['triptime_s'] = routes.triptime_s.astype('int')



            ##### ---->>> aggregation @ ORIGIN
            ## grouby + counts....only if you want to estimate the NUMBER of vehicles
            aggregated_zmu_origin = routes[['index_zmu_origin', 'zmu_origin']].groupby(
                ['index_zmu_origin', 'zmu_origin'],
                sort=False).size().reset_index().rename(columns={0: 'counts'})

            mean_aggregated_zmu_origin = routes[['index_zmu_origin', 'zmu_origin', 'triptime_s', 'breaktime_s', 'dist']].groupby(['index_zmu_origin', 'zmu_origin'],
                                    sort=False).mean().reset_index().rename(
                columns={0: 'means'})
            mean_aggregated_zmu_origin.rename({'triptime_s': 'mean_triptime_m'}, axis=1, inplace=True)
            mean_aggregated_zmu_origin['mean_triptime_m'] = (mean_aggregated_zmu_origin['mean_triptime_m']) / 60
            mean_aggregated_zmu_origin.rename({'breaktime_s': 'mean_breaktime_m'}, axis=1, inplace=True)
            mean_aggregated_zmu_origin['mean_breaktime_m'] = (mean_aggregated_zmu_origin['mean_breaktime_m']) / 60
            mean_aggregated_zmu_origin.rename({'dist': 'mean_tripdistance_m'}, axis=1, inplace=True)



            ## merge data together ------########################################################
            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, mean_aggregated_zmu_origin, on=['zmu_origin', 'index_zmu_origin'],
                                                   how='left')
            ## merge trip counts @destination with total staypoints in each traffic ZONE ZMU
            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, all_staypoints,
                                                   left_on='zmu_origin', right_on='zmu')

            ### NORMALIZE each cont @destination with the number of staypoints in each traffic zone
            aggregated_zmu_origin['counts_norm'] = aggregated_zmu_origin.counts / 1

            aggregated_zmu_origin = aggregated_zmu_origin[
                              ['index_zmu_origin','zmu', 'counts_norm', 'mean_triptime_m', 'mean_breaktime_m',
                               'mean_tripdistance_m', 'count_staypoints']]

            aggregated_zmu_origin['zmu'] = aggregated_zmu_origin.zmu.astype('int')
            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin, ZMU_ROMA_with_population, on=['zmu'],
                                                   how='left')
            aggregated_zmu_origin.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_zmu_origin['counts_norm'] = round(aggregated_zmu_origin['counts_norm'], 2)


            ################################################################################################
            #######--------------------------------------------- ###########################################
            ###--->>> get aggregation by DAY <<---------------------########################################



            #### ---- query all trips having a staypoint ------#########
            ### staypoint = Home or WORK
            if (selected_stay_type == 21 or selected_stay_type == 22) and  (selected_ZMU_tod != 9):
                query_origin_destination_routes_day = text(''' SELECT synt.trips.id_veh,
                                                                  /*fcd.trips.geom,*/
                                                                  synt.trips.id_zone_o, synt.trips.id_zone_d,
                                                                  synt.trips.tod_o,synt.trips.tod_d,
                                                                  synt.trips.dt_o,synt.trips.dt_d,
                                                                  synt.trips.tt,synt.trips.dist,
                                                                  synt.trips.p_after,  synt.trips.p_before,
                                                                  synt.trips.hour_range_o,synt.trips.hour_range_d,
                                                                  synt.trips.geom,
                                                                   date_part('hour', dt_o) as hr, 
                                                                   TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
    
                                                                  FROM synt.trips
                                                                  WHERE 
                                                                    date(synt.trips.dt_o) BETWEEN :x AND :xx 
                                                                    AND synt.trips.tod_o = :z  ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                        z=str(tod))

            ### staypoint = Home or WORK and all Time of days (W, P, H)
            elif (selected_stay_type == 21 or selected_stay_type == 22) and  (selected_ZMU_tod == 9):
                query_origin_destination_routes_day = text(''' SELECT synt.trips.id_veh,
                                                                         /*fcd.trips.geom,*/
                                                                         synt.trips.id_zone_o, synt.trips.id_zone_d,
                                                                         synt.trips.tod_o,synt.trips.tod_d,
                                                                         synt.trips.dt_o,synt.trips.dt_d,
                                                                         synt.trips.tt,synt.trips.dist,
                                                                         synt.trips.p_after,  synt.trips.p_before,
                                                                         synt.trips.hour_range_o,synt.trips.hour_range_d,
                                                                         synt.trips.geom,
                                                                          date_part('hour', dt_o) as hr, 
                                                                          TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day

                                                                         FROM synt.trips
                                                                         WHERE 
                                                                           date(synt.trips.dt_o) BETWEEN :x AND :xx ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start),
                                                                      xx=str(selected_ZMU_day_end))


            ### staypoint = Home + WORK
            elif (selected_stay_type == 23) and  (selected_ZMU_tod != 9):
                query_origin_destination_routes_day = text(''' SELECT fcd.trips.id_veh,
                                                                             /*fcd.trips.geom,*/
                                                                             fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                             fcd.trips.tod_o,fcd.trips.tod_d,
                                                                             fcd.trips.dt_o,fcd.trips.dt_d,
                                                                             fcd.trips.tt,fcd.trips.dist,
                                                                             fcd.trips.p_after,  fcd.trips.p_before,
                                                                             fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                             fcd.staypoints.id_stay_type,
                                                                             fcd.trips.geom,
                                                                              date_part('hour', dt_o) as hr, 
                                                                              TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
    
                                                                             FROM fcd.staypoints
                                                                             INNER JOIN 
                                                                             fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                             WHERE 
                                                                               date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                               AND fcd.trips.tod_o = :z 
                                                                              AND fcd.staypoints.id_stay_type != 'O'
                                                                             AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                      ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start),
                                                                      xx=str(selected_ZMU_day_end),
                                                                      z=str(tod))

            ### staypoint = Home + WORK and all Time of day (W, P, H)
            elif (selected_stay_type == 23) and  (selected_ZMU_tod == 9):
                query_origin_destination_routes_day = text(''' SELECT fcd.trips.id_veh,
                                                                                            /*fcd.trips.geom,*/
                                                                                            fcd.trips.id_zone_o, fcd.trips.id_zone_d,
                                                                                            fcd.trips.tod_o,fcd.trips.tod_d,
                                                                                            fcd.trips.dt_o,fcd.trips.dt_d,
                                                                                            fcd.trips.tt,fcd.trips.dist,
                                                                                            fcd.trips.p_after,  fcd.trips.p_before,
                                                                                            fcd.trips.hour_range_o,fcd.trips.hour_range_d,
                                                                                            fcd.staypoints.id_stay_type,
                                                                                            fcd.trips.geom,
                                                                                             date_part('hour', dt_o) as hr, 
                                                                                             TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day

                                                                                            FROM fcd.staypoints
                                                                                            INNER JOIN 
                                                                                            fcd.trips ON fcd.trips.id_veh = fcd.staypoints.id_veh
                                                                                            WHERE 
                                                                                              date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                                                             AND fcd.staypoints.id_stay_type != 'O'
                                                                                            AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                                     ''')

                stmt = query_origin_destination_routes_day.bindparams(x=str(selected_ZMU_day_start),
                                                                      xx=str(selected_ZMU_day_end))

            print(selected_stay_type)
            print(selected_ZMU_tod)


            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_destination_routes_day = pd.DataFrame(res)


            ##### -------->>>> ORIGIN
            origin_destination_routes_day.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
            ##merge with zmu zones
            origin_destination_routes_day = pd.merge(origin_destination_routes_day,
                                                     ZMU_ROMA_with_population[
                                                         ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                     on=['zmu'], how='left')
            origin_destination_routes_day.rename({'zmu': 'zmu_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'index_zmu': 'index_zmu_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'area': 'area_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'nome_comun': 'nome_comun_origin'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'quartiere': 'quartiere_origin'}, axis=1, inplace=True)

            ##### ------>>>>> DESTINATION
            origin_destination_routes_day.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
            ##merge with zmu zones
            origin_destination_routes_day = pd.merge(origin_destination_routes_day,
                                                     ZMU_ROMA_with_population[
                                                         ['zmu', 'index_zmu', 'area', 'nome_comun', 'quartiere']],
                                                     on=['zmu'], how='left')
            origin_destination_routes_day.rename({'zmu': 'zmu_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'index_zmu': 'index_zmu_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'area': 'area_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'nome_comun': 'nome_comun_destination'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'quartiere': 'quartiere_destination'}, axis=1, inplace=True)

            ## merge ORIGIN and DESTINATION routes by 'idtrajectory'
            origin_destination_routes_day.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
            origin_destination_routes_day.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['triptime_s'] > 0]
            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['breaktime_s'] > 0]
            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['tripdistance_m'] > 0]

            ### ----- @ ORIGINS ---------------------------------- ##################################################

            ## grouby + counts....only if you want to estimate the NUMBER of vehicles
            aggregated_zmu_origin_day = origin_destination_routes_day[['hr', 'zmu_origin']].groupby(
                ['hr', 'zmu_origin'], sort=False).size().reset_index().rename(columns={0: 'counts'})


            ## merge trip counts @destination with total staypoints in each traffic ZONE ZMU
            aggregated_zmu_origin_day = pd.merge(aggregated_zmu_origin_day, all_staypoints,
                                                   left_on='zmu_origin', right_on='zmu')

            ### NORMALIZE each cont @destination with the number of staypoints in each traffic zone

            aggregated_zmu_origin_day[
                'counts_norm'] = aggregated_zmu_origin_day.counts / 1


            aggregated_zmu_origin_day.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_zmu_origin_day['counts_norm'] = round(aggregated_zmu_origin_day['counts_norm'], 2)


            ## remove none values
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[
                aggregated_zmu_origin_day['zmu_origin'].notna()]
            aggregated_zmu_origin_day['zmu_origin'] = aggregated_zmu_origin_day.zmu_origin.astype(
                'int')

            ## merge with zmu to get geometries.....
            ## get geometry from "ZMU_ROMA"

            # aggregated_zmu_destinations_day.rename({'zmu_destination': 'zmu'}, axis=1, inplace=True)
            aggregated_zmu_origin_day['zmu'] = aggregated_zmu_origin_day.zmu.astype('int')
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[['hr', 'zmu', 'counts', 'count_staypoints', 'counts_norm']]
            aggregated_zmu_origin_day = pd.merge(aggregated_zmu_origin_day, ZMU_ROMA_with_population,
                                                       on=['zmu'], how='left')
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[
                aggregated_zmu_origin_day['index_zmu'].notna()]
            aggregated_zmu_origin_day['index_zmu'] = aggregated_zmu_origin_day.index_zmu.astype('int')

            aggregated_zmu_origin_day = aggregated_zmu_origin_day[
                ['counts_norm', 'index_zmu', 'POP_TOT_ZMU', 'zmu', 'hr', 'nome_comun', 'quartiere']]
            # aggregated_zmu_destinations_day['counts'] = (aggregated_zmu_destinations_day['counts'] /
            #                                             aggregated_zmu_destinations_day['POP_TOT_ZMU']) * 1000


            #### ------->>>> groupby + mean triptime, tripdistance, breaktime <<<-----------###########################################

            origin_destination_routes_day.rename({'zmu_origin': 'zmu'}, axis=1, inplace=True)
            origin_destination_routes_day = origin_destination_routes_day[
                origin_destination_routes_day['zmu'].notna()]
            origin_destination_routes_day['zmu'] = origin_destination_routes_day.zmu.astype('int')

            aggregated_means_zmu_origin = origin_destination_routes_day[
                ['zmu', 'hr', 'triptime_s', 'breaktime_s', 'tripdistance_m']].groupby(['hr', 'zmu'],
                                                                                             sort=False).mean().reset_index().rename(
                columns={0: 'means'})
            ## convert triptime_s into minutes
            aggregated_means_zmu_origin['triptime_m'] = (aggregated_means_zmu_origin['triptime_s']) / 60
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['triptime_s'].notna()]
            aggregated_means_zmu_origin['triptime_m'] = aggregated_means_zmu_origin.triptime_m.astype('int')
            ## convert breaktime_s into minutes
            aggregated_means_zmu_origin['breaktime_m'] = (aggregated_means_zmu_origin['breaktime_s']) / 60
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['breaktime_m'].notna()]
            aggregated_means_zmu_origin['breaktime_m'] = aggregated_means_zmu_origin.breaktime_m.astype('int')
            ## convert tripdistance_m
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['tripdistance_m'].notna()]
            aggregated_means_zmu_origin['tripdistance_m'] = aggregated_means_zmu_origin.tripdistance_m.astype(
                'int')

            aggregated_means_zmu_origin = pd.merge(aggregated_means_zmu_origin, aggregated_zmu_origin_day,
                                                      on=['zmu', 'hr'], how='left')

            aggregated_means_zmu_origin.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                aggregated_means_zmu_origin['counts_norm'].notna()]


            ##############################################################################################################################
            ## compute total counts over ALL ZONES for a given hour-range, and compute total mean FOR ALL ZONEs for a given hour-range
            aggregated_zmu_origin_day.replace([np.inf, -np.inf], np.nan, inplace=True)
            aggregated_zmu_origin_day = aggregated_zmu_origin_day[aggregated_zmu_origin_day['counts_norm'].notna()]
            #aggregated_zmu_destinations = aggregated_zmu_destinations[aggregated_zmu_destinations['counts'].notna()]

            #### make the means ove the 24hours
            aggregated_24h_mean = aggregated_means_zmu_origin[
                ['zmu', 'triptime_m', 'breaktime_m', 'tripdistance_m']].groupby(['zmu'],
                                                                                sort=False).mean().reset_index().rename(
                columns={0: 'means'})

            aggragated_24h_counts = aggregated_means_zmu_origin[['counts_norm', 'zmu']].groupby(
                ['zmu'],  sort=False).size().reset_index().rename(columns={0: 'counts'})    ### over 1000 inhabitants

            aggregated_24h_mean = pd.merge(aggregated_24h_mean, aggragated_24h_counts,
                                                        on=['zmu'], how='left')

            aggregated_24h_mean.rename({'triptime_m': 'mean_triptime_m'}, axis=1, inplace=True)
            aggregated_24h_mean.rename({'breaktime_m': 'mean_breaktime_m'}, axis=1, inplace=True)
            aggregated_24h_mean.rename({'tripdistance_m': 'mean_tripdistance_m'}, axis=1, inplace=True)
            aggregated_24h_mean.rename({'counts': 'counts24'}, axis=1, inplace=True)

            aggregated_zmu_origin = pd.merge(aggregated_zmu_origin[[ 'index_zmu_origin', 'zmu', 'index_zmu', 'POP_TOT_ZMU', 'counts_norm',
                            'area', 'comune', 'nome_comun', 'quartiere', 'pgtu', 'municipio', 'lon',
                              'lat', 'centroid', 'geometry']], aggregated_24h_mean,
                                           on=['zmu'], how='left')

            aggregated_zmu_origin['mean_triptime_m'] = round(aggregated_zmu_origin.mean_triptime_m, ndigits=2)
            aggregated_zmu_origin['mean_tripdistance_m'] = round(aggregated_zmu_origin.mean_tripdistance_m,
                                                                   ndigits=2)
            aggregated_zmu_origin['mean_breaktime_m'] = round(aggregated_zmu_origin.mean_breaktime_m,
                                                                   ndigits=2)


            TOTAL_TRIPS_COUNTS = max(aggregated_zmu_origin.counts24)    ## per 1000 inhabitants
            TOTAL_MAX_TRIPTIME = np.max(aggregated_zmu_origin.mean_triptime_m)
            TOTAL_MAX_BREAKTIME = np.max(aggregated_zmu_origin.mean_breaktime_m)
            TOTAL_MAX_TRIPDISTANCE = np.max(aggregated_zmu_origin.mean_tripdistance_m)

            ## INDICATORs for RADAR of POLAR CHARTS (compute PERCENTAGES within the chosen hourrange compared to the total OVER ALL ZONES)
            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['counts24'].notna()]
            aggregated_zmu_origin['radial_counts'] = aggregated_zmu_origin['counts24'] * 100 / TOTAL_TRIPS_COUNTS

            aggregated_zmu_origin['radial_counts'] = round(aggregated_zmu_origin.radial_counts, ndigits=4)

            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['mean_triptime_m'].notna()]
            aggregated_zmu_origin['radial_mean_triptime'] = (aggregated_zmu_origin['mean_triptime_m']) * 100 / TOTAL_MAX_TRIPTIME
            aggregated_zmu_origin['radial_mean_triptime'] = round(aggregated_zmu_origin.radial_mean_triptime, ndigits=2)

            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['mean_breaktime_m'].notna()]
            aggregated_zmu_origin['radial_mean_breaktime'] = (aggregated_zmu_origin['mean_breaktime_m']) * 100 / TOTAL_MAX_BREAKTIME
            aggregated_zmu_origin['radial_mean_breaktime'] = round(aggregated_zmu_origin.radial_mean_breaktime, ndigits=2)

            aggregated_zmu_origin = aggregated_zmu_origin[
                aggregated_zmu_origin['mean_tripdistance_m'].notna()]
            aggregated_zmu_origin['radial_mean_tripdistance'] = (aggregated_zmu_origin['mean_tripdistance_m']) * 100 / TOTAL_MAX_TRIPDISTANCE
            aggregated_zmu_origin['radial_mean_tripdistance'] = round(aggregated_zmu_origin.radial_mean_tripdistance, ndigits=2)

            ####################################################################################
            ## radar chart over a single ZMU for a given hour range ###########################


            ## classify by scores...
            aggregated_zmu_origin['score_trip_counts'] = 0
            aggregated_zmu_origin['score_trip_time'] = 0
            aggregated_zmu_origin['score_breaktime'] = 0
            aggregated_zmu_origin['score_trip_distance'] = 0
            aggregated_zmu_origin['mark_trip_counts'] = 0
            aggregated_zmu_origin['mark_trip_time'] = 0
            aggregated_zmu_origin['mark_breaktime'] = 0
            aggregated_zmu_origin['mark_trip_distance'] = 0

            ### number of trips
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_counts.iloc[i] >= 0) and (aggregated_zmu_origin.radial_counts.iloc[i] <= 30):
                    aggregated_zmu_origin.score_trip_counts.iloc[i]=1
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_counts.iloc[i] > 30) and (aggregated_zmu_origin.radial_counts.iloc[i] <= 60):
                    aggregated_zmu_origin.score_trip_counts.iloc[i] = 2
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_counts.iloc[i] > 60) and (
                                aggregated_zmu_origin.radial_counts.iloc[i] <= 80):
                    aggregated_zmu_origin.score_trip_counts.iloc[i] = 3
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_counts.iloc[i] > 80) and (
                            aggregated_zmu_origin.radial_counts.iloc[i] <= max(aggregated_zmu_origin.radial_counts)):
                    aggregated_zmu_origin.mark_trip_counts.iloc[i] = "Relevant"
                    aggregated_zmu_origin.score_trip_counts.iloc[i] = 4


            #### mean trip time
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_mean_triptime.iloc[i] >= 0) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= 15):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 1
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_mean_triptime.iloc[i] > 15) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= 20):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 2
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_mean_triptime.iloc[i] > 20) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= 30):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 3
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_mean_triptime.iloc[i] > 30) and (
                        aggregated_zmu_origin.radial_mean_triptime.iloc[i] <= max(aggregated_zmu_origin.radial_mean_triptime)):
                    aggregated_zmu_origin.score_trip_time.iloc[i] = 4
                    aggregated_zmu_origin.mark_trip_time.iloc[i] = "Relevant"

            #### mean stop time or breaktime
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] >= 0) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= 5):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 1
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] > 5) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= 15):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 2
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] > 15) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= 25):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 3
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_mean_breaktime.iloc[i] > 25) and (
                        aggregated_zmu_origin.radial_mean_breaktime.iloc[i] <= max(
                    aggregated_zmu_origin.radial_mean_breaktime)):
                    aggregated_zmu_origin.score_breaktime.iloc[i] = 4
                    aggregated_zmu_origin.mark_breaktime.iloc[i] = "Relevant"


            #### mean trip_distance
            for i in range(len(aggregated_zmu_origin)):
                if (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] >= 0) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= 5):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 1
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Low"
                elif (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] > 5) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= 15):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 2
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Average"
                elif (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] > 15) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= 25):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 3
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Important"
                elif (aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] > 25) and (
                        aggregated_zmu_origin.radial_mean_tripdistance.iloc[i] <= max(
                    aggregated_zmu_origin.radial_mean_tripdistance)):
                    aggregated_zmu_origin.score_trip_distance.iloc[i] = 4
                    aggregated_zmu_origin.mark_trip_distance.iloc[i] = "Relevant"


         #### save data into .csv format ###################################################
            #####----->>> save csv file ---- ##################################################
            csv_aggregated_zmu_origin = aggregated_zmu_origin[[ 'index_zmu_origin', 'zmu','score_trip_counts', 'score_trip_time', 'score_breaktime',
              'score_trip_distance', 'mark_trip_counts', 'mark_trip_time',
                'mark_breaktime', 'mark_trip_distance']]
            csv_aggregated_zmu_origin.to_csv(
                path_app + 'static/csv_aggregated_zmu_origin_' + session.sid + '.csv')



            ##########################################################################################################
            ##########################################################################################################

            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                ['counts_norm', 'hr', 'zmu', 'triptime_s', 'breaktime_s', 'tripdistance_m',
                 'triptime_m', 'breaktime_m']]

            ## merge with zmu to get geometries.....
            ## get geometry from "ZMU_ROMA"
            aggregated_means_zmu_origin = pd.merge(aggregated_means_zmu_origin, ZMU_ROMA_with_population,
                                                        on=['zmu'], how='left')
            aggregated_means_zmu_origin = aggregated_means_zmu_origin[
                ['index_zmu', 'zmu', 'hr', 'tripdistance_m',
                 'triptime_m', 'breaktime_m', 'nome_comun', 'quartiere']]

            ### -----> merge all data together ---- ###################################################################
            aggregated_zmu_origin_day = pd.merge(aggregated_zmu_origin_day,
                                                       aggregated_means_zmu_origin,
                                                       on=['index_zmu', 'zmu', 'hr', 'nome_comun', 'quartiere'],
                                                       how='left')

            #####----->>> save csv file ---- ##################################################
            aggregated_means_zmu_origin['counts_norm'] = round(aggregated_zmu_origin_day['counts_norm'], 2)
            aggregated_zmu_origin_day.to_csv(
                path_app + 'static/aggregated_zmu_origin_day_' + session.sid + '.csv')
            ## remove "centroid" column
            aggregated_zmu_origin.drop(['centroid'], axis=1, inplace=True)

            try:
                aggregated_zmu_origin = gpd.GeoDataFrame(aggregated_zmu_origin)
            except IndexError:
                abort(404)

            ## save as .geojson file
            aggregated_zmu_origin.to_file(filename=path_app + 'static/aggregated_zmu_filtered.geojson',
                                                driver='GeoJSON')
            ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
            with open(path_app + "static/aggregated_zmu_filtered.geojson", "r+") as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var aggregated_matched_routes_zmu = \n" + old)  # assign the "var name" in the .geojson file

            ### convert Geodataframe into .geojson...
            session["aggregated_zmu_origin"] = aggregated_zmu_origin.to_json()

            return render_template("index_zmu_select_hour.html",
                                   var_ZMU_day=selected_ZMU_day_start, session_aggregated_zmu_origin = session["aggregated_zmu_origin"])

        return render_template("index_zmu_select_hour.html")

###############################################################################################################
###############################################################################################################







################################################################################################################
################################################################################################################
############# ------- EMISSIONS from ZMUs zones -------------------------------------- #########################
################################################################################################################


### select day (ZMU)...from Database
@app.route('/ZMU_day_emiss_selector/', methods=['GET', 'POST'])
def ZMU_day_emiss_selector():

    # session["data_type"] = 11
    # selected_ZMU_day_start = '2022-10-04'
    # selected_ZMU_day_end = '2022-10-14'
    if request.method == "POST":
        ##### ------ daterangepicker ----- ############################################
        ###############################################################################

        try:
            data = request.form["daterange"]
            session['input_data_range'] = data
            print("-------------data-------------:", data)
        except:
            data = "10/12/2022 - 10/13/2022"

        try:
            start_date = data.split(" - ")[0]
            start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            session["ZMU_day_start"] = str(start_date.date())
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("gotta!!!----->> selected_ZMU_day_start:", session["ZMU_day_start"])  ##--->> only get date
            selected_ZMU_day_start = str(selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            end_date = data.split(" - ")[1]
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            session["ZMU_day_end"] = str(end_date.date())
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("gotta!!!----->> selected_ZMU_day_end:", session["ZMU_day_end"])  ##--->> only get date
            selected_ZMU_day_end = str(selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable selected_ZMU_day_end: ", session["ZMU_day_end"])

        ##########################################################################################################

        user = session.sid
        print("user:", user)

        data_ZMU = [{
            'ZMU_day': selected_ZMU_day_start,
            'hour': 'choose hour'
        }]

        print("session user ID:", session.sid)
        print("--- I am HERE ------")
        # print("full session:", session)
        return render_template("index_zmu_emiss_select_day.html", data_ZMU=data_ZMU, var_ZMU_day=selected_ZMU_day_start,
                               user=user)




### select EMISSION TYPE or POLLUTANT TYPE  -------- #################################
@app.route('/emission_type_selector/', methods=['GET', 'POST'])
def emission_type_selector():
    import glob

    if request.method == "POST":

        session["emission_type"] = request.form.get("emission_type")
        selected_emission_type = session["emission_type"]
        print("selected_emission_type:", selected_emission_type)
        selected_emission_type = str(selected_emission_type)

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_emission_type = int(selected_emission_type)
        if selected_emission_type == 11:  ## EC
            pollutant = 'EC'
            print("EC")
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)
            ## switch to table.........render....
            # return render_template("index_zmu_emiss_select_day.html")

        elif selected_emission_type == 12:  ## EC wtt
            print("EC_wtt")
            pollutant = 'EC_wtt'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 13:  ## NOx
            print("NOx")
            pollutant = 'NOx'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 14:  ## NMVOC
            print("nmvoc")
            pollutant = 'nmvoc'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 15:  ## PM
            print("PM")
            pollutant = 'PM'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 16:  ## PM_nexh
            print("PM_nexh")
            pollutant = 'PM_nexh'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 17:  ## CO2 eq
            print("CO2eq")
            pollutant = 'CO2_eq'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 18:  ## CO2 eq wtt
            print("CO2eq_wtt")
            pollutant = 'CO2_eq_wtt'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)


        with open(path_app + "static/params/selected_emission_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_emission_type))

        return render_template("index_zmu_emiss_select_day.html")


### select FLEET TYPE  -------- #################################
@app.route('/fleet_type_selector/', methods=['GET', 'POST'])
def fleet_type_selector():

    import glob

    if request.method == "POST":

        with open(path_app + "static/params/selected_emission_type_" + session.sid + ".txt", "r") as file:
            selected_emission_type = file.read()
        print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)
        session["emission_type"] = selected_emission_type

        session["fleet_type"] = request.form.get("fleet_type")
        selected_fleet_type = session["fleet_type"]
        print("selected_fleet_type:", selected_fleet_type)
        selected_fleet_type = str(selected_fleet_type)

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_fleet_type = int(selected_fleet_type)
        if selected_fleet_type == 21:  ## trditional / circulating
            print("rm1")
            print("selected_fleet_type:--------electric", selected_fleet_type)
            ## switch to table.........render....
            # return render_template("index_zmu_emiss_select_day.html")

        elif selected_fleet_type == 22:  ## el1
            print("el1")
            print("selected_fleet_type:--------electric1", selected_fleet_type)

        elif selected_fleet_type == 23:  ## el2
            print("el2")
            print("selected_fleet_type:--------electric2", selected_fleet_type)


        with open(path_app + "static/params/selected_fleet_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_fleet_type))

        return render_template("index_zmu_emiss_select_day.html")




### select Time of DAY (TOD) -------- #################################
@app.route('/tod_emiss_selector/', methods=['GET', 'POST'])
def tod_emiss_selector():

    import glob

    if request.method == "POST":

        with open(path_app + "static/params/selected_emission_type_" + session.sid + ".txt", "r") as file:
            selected_emission_type = file.read()
        print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)
        session["emission_type"] = selected_emission_type
        with open(path_app + "static/params/selected_fleet_type_" + session.sid + ".txt", "r") as file:
            selected_fleet_type = file.read()
        print("selected_fleet_type-------I AM HERE-----------: ", selected_fleet_type)
        session["fleet_type"] = selected_fleet_type


        session["ZMU_tod"] = request.form.get("ZMU_tod")
        selected_ZMU_tod = session["ZMU_tod"]
        print("selected_ZMU_tod:", selected_ZMU_tod)
        selected_ZMU_tod = str(selected_ZMU_tod)

        session["check_ZMU_tod"] = session["ZMU_tod"]


        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_ZMU_tod))

        return render_template("index_zmu_emiss_select_day.html")



### select type of STAYPOINT -------- #################################
@app.route('/staypoints_type_impacts/', methods=['GET', 'POST'])
def staypoints_type_impacts():

    import glob

    if request.method == "POST":

        session["id_stay_type"] = request.form.get("id_stay_type")
        selected_stay_type = session["id_stay_type"]
        print("--------------selected_stay_type--------------------:", selected_stay_type)
        selected_stay_type = str(selected_stay_type)

        with open(path_app + "static/params/selected_stay_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_stay_type))

        with open(path_app + "static/params/selected_stay_type_" + session.sid + ".txt", "r") as file:
            selected_stay_type = file.read()
        print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)

        return render_template("index_zmu_emiss_select_day.html")



### select hour range and (ZMU) from Database
@app.route('/ZMU_emiss_hourrange_selector/', methods=['GET', 'POST'])
def ZMU_emiss_hourrange_selector():
    import glob
    if request.method == "POST":

        # session["ZMU_tod"] = 6
        # selected_ZMU_hourrange = "1"
        # selected_ZMU_day_start = '2022-10-21'
        # selected_ZMU_day_end = '2022-10-22'
        # selected_fleet_type = 21
        # session["ZMU_tod"] = 6
        # tod = "W"
        # selected_ZMU_tod = 6
        # selected_stay_type = 21
        # selected_emission_type = 11

        try:
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("day from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("day from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])

        selected_emission_type_files = glob.glob(path_app + "static/params/selected_emission_type_*.txt")
        selected_emission_type_files.sort(key=os.path.getmtime)
        selected_emission_type_file = selected_emission_type_files[len(selected_emission_type_files) - 1]
        with open(selected_emission_type_file) as file:
            selected_emission_type = file.read()
        print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)

        stored_fleet_type_files = glob.glob(path_app + "static/params/selected_fleet_type_*.txt")
        stored_fleet_type_files.sort(key=os.path.getmtime)
        stored_fleet_type_file = stored_fleet_type_files[len(stored_fleet_type_files) - 1]
        with open(stored_fleet_type_file) as file:
            selected_fleet_type = file.read()
        print("selected_fleet_type-------I AM HERE-----------: ", selected_fleet_type)

        try:
            with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "r") as file:
                selected_ZMU_tod = file.read()
            print("selected_ZMU_tod-------I AM HERE-----------: ", selected_ZMU_tod)
        except:
            for stored_tod_file in glob.glob(path_app + "static/params/selected_tod_zmu_*.txt"):
                print(stored_tod_file)
            with open(stored_tod_file) as file:
                selected_ZMU_tod = file.read()
            print("stored_tod_file-------I AM HERE-----------: ", selected_ZMU_tod)


        try:
            with open(path_app + "static/params/selected_stay_type_" + session.sid + ".txt", "r") as file:
                selected_stay_type = file.read()
            print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)
        except:
            stored_staypoint_files = glob.glob(path_app + "static/params/selected_stay_type_*.txt")
            stored_staypoint_files.sort(key=os.path.getmtime)
            stored_staypoint_file = stored_staypoint_files[len(stored_staypoint_files) - 1]
            with open(stored_staypoint_file) as file:
                selected_stay_type = file.read()
            print("selected_stay_type-------I AM HERE-----------: ", selected_stay_type)


        session["emission_type"] = selected_emission_type
        session['fleet_type'] = selected_fleet_type
        session["id_stay_type"] = selected_stay_type
        session["ZMU_tod"] = selected_ZMU_tod
        session["check_ZMU_tod"] = session["ZMU_tod"]

        ## --------- SELECT TOD -------- ##############
        selected_ZMU_tod = int(selected_ZMU_tod)
        if selected_ZMU_tod == 6:  ## WORKING day
            tod = "W"
        elif selected_ZMU_tod == 7:  ## PRE holiday
            tod = "P"
        elif selected_ZMU_tod == 8:  ## HOLIDAY
            tod = "H"
        elif selected_ZMU_tod == 9:  ## WORKING + PREHOLIDAYS + HOLIDAY
            tod = "WPH"


        ## --------- SELECT STAYPOINT -------- ##############
        selected_stay_type = int(selected_stay_type)
        if selected_stay_type == 21:  ## HOME
            stay_type = "H"
        elif selected_stay_type == 22:  ## WORK
            stay_type = "W"
        elif selected_stay_type == 23:  ## OTHER
            stay_type = "Home + Work"

        print("-----stay_type------------------------------------:", stay_type)
        print("-----selected_stay_type------------------------------------:", selected_stay_type)


        selected_fleet_type = int(selected_fleet_type)
        if selected_fleet_type == 21:
            fleet_type = "rm1"
        elif selected_fleet_type == 22:
            fleet_type = "el1"
        elif selected_fleet_type == 23:
            fleet_type = "el2"

        print("fleet_type------:", fleet_type)


        ## TRY if session exists
        try:
            session["ZMU_hourrange"] = request.form.get("ZMU_hourrange")
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
            selected_ZMU_hourrange = str(selected_ZMU_hourrange)
        except:
            session["ZMU_hourrange"] = 2
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])

        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_hourrange = int(selected_ZMU_hourrange)
        if selected_ZMU_hourrange == 0:     ## 00:00 ---> 07:00
            hourrange_id = "N1"
        elif selected_ZMU_hourrange == 1:    ## 07:00 ----> 10:00
            hourrange_id = "M1"
        elif selected_ZMU_hourrange == 2:    ## 10:00 ---> 14:00
            hourrange_id = "M2"
        elif selected_ZMU_hourrange == 3:    ##  14:00 ---> 16:00
            hourrange_id = "A1"
        elif selected_ZMU_hourrange == 4:   ## 16:00 ---> 20:00
            hourrange_id = "A2"
        elif selected_ZMU_hourrange == 5:  ## 20:00 ---> 24:00
            hourrange_id = "A3"

        session["hourrange_id"] = hourrange_id
        print("------hourrange_id------------>>>:", hourrange_id)
        print("selected fleet type...........................................", selected_fleet_type)


        session["tod"] = tod
        print("----- tod------:", session["tod"])

        ######################################################################################
        #####----- make selection between FCD data and Synthetic data ------ #################
        ######################################################################################

        ## switch to table.........TRIPS----FCD data
        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text


        ####----- query all staypoints ----- #######################
        if (selected_stay_type == 21 or selected_stay_type == 22):
            query_all_staypoints = text('''SELECT count(id_staypoint),
                                                             id_zone
                                                             FROM fcd.staypoints
                                                                        WHERE
                                                                        fcd.staypoints.id_stay_type = :s
                                                                        AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                        GROUP BY
                                                                         id_zone''')

            stmt = query_all_staypoints.bindparams(s=str(stay_type))

        elif (selected_stay_type == 23):
            query_all_staypoints = text('''SELECT count(id_staypoint),
                                                                        id_zone
                                                                        FROM fcd.staypoints
                                                                                   WHERE  
                                                                                   fcd.staypoints.id_stay_type != 'O'
                                                                                   AND (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                                   GROUP BY
                                                                                    id_zone''')

            stmt = query_all_staypoints

        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        all_staypoints = pd.DataFrame(res)
        all_staypoints.rename({'id_zone': 'zmu'}, axis=1, inplace=True)
        all_staypoints.rename({'count': 'count_staypoints'}, axis=1, inplace=True)  ### all staypoints by zone
        all_staypoints.replace([np.inf, -np.inf], np.nan, inplace=True)
        all_staypoints = all_staypoints[
            all_staypoints['zmu'].notna()]
        all_staypoints['zmu'] = all_staypoints.zmu.astype('int')

        ##### ----- make geojson for staypoints --------- ###############################
        if (selected_stay_type == 21 or selected_stay_type == 22):
            query_staypoints = text('''SELECT id_staypoint, id_veh, n_points, name,
                                                                 id_stay_type, lon, lat, id_zone
                                                                    FROM fcd.staypoints 
                                                                     WHERE (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                   AND id_stay_type=:s ''')
            stmt = query_staypoints.bindparams(s=str(stay_type))


        elif (selected_stay_type == 23):
            query_staypoints = text('''SELECT id_staypoint, id_veh, n_points, name,
                                                                              id_stay_type, lon, lat, id_zone
                                                                                 FROM fcd.staypoints 
                                                                                  WHERE (fcd.staypoints.info->>'virtual')::boolean IS false 
                                                                                  AND id_stay_type !='O' ''')
            stmt = query_staypoints

        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        df_staypoints = pd.DataFrame(res)


        ##-----> make a geodataframe with lat, lon, coordinates
        geometry = [Point(xy) for xy in zip(df_staypoints.lon, df_staypoints.lat)]
        crs = {'init': 'epsg:4326'}
        gdf_staypoints = GeoDataFrame(df_staypoints, crs=crs, geometry=geometry)
        ## save as .geojson file
        gdf_staypoints.to_file(filename=path_app + 'static/staypoints_tod.geojson',
                               driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + 'static/staypoints_tod.geojson', 'r+', encoding='utf8',
                  errors='ignore') as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var points_staypoints = \n" + old)  # assign the "var name" in the .geojson file

        #############################################################################################################
        #### use extennd emissions over all the traffic zones crossed during the trip (valid only for NOX, NMVOCs, PM, PM_nexh)

        if (selected_emission_type == 13 or selected_emission_type == 14 or selected_emission_type == 15 or selected_emission_type == 16):
            query_emissions_origin = text('''WITH data AS(
                                                                  SELECT *
                                                                     FROM federico.distributed_trips_emiss_cons_fcd
                                                                     LEFT JOIN fcd.trips 
                                                                                 ON federico.distributed_trips_emiss_cons_fcd.id_trip = trips.id        
                                                                                   WHERE date(trips.dt_o) BETWEEN :x AND :xx   
                                                                                    AND trips.tod_o = :z      
                                                                                   /*limit 1000*/
                                                                )
                                                                  SELECT id_car_fleet,  zmu, id_trip, id_veh, dt_o, dt_d, id_zone_o, id_zone_d, ec, ec_wtt, nox, nmvoc, pm, pm_nexh, co2eq, co2eq_wtt, 
                                                                  date_part('hour', dt_o) as hour,
                                                                  TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                                                  from data     
                                                                  WHERE hour_range_o = :y  AND
                                                                  id_car_fleet =:w ''')

            print("------------>>>> USING EXTENDED EMISSIONS THROUGH all the ZONES <<<<<<------------------------------")

        else:
            query_emissions_origin = text('''WITH data AS(
                                                              SELECT *
                                                                 FROM impacts.trips_cons_emis_fcd
                                                                 LEFT JOIN fcd.trips 
                                                                             ON trips_cons_emis_fcd.id_trip = trips.id        
                                                                               WHERE date(trips.dt_o) BETWEEN :x AND :xx   
                                                                                AND trips.tod_o = :z      
                                                                               /*limit 1000*/
                                                            )
                                                              SELECT id_car_fleet, id_trip, id_veh, dt_o, dt_d, id_zone_o, id_zone_d, ec, ec_wtt, nox, nmvoc, pm, pm_nexh, co2eq, co2eq_wtt, 
                                                              date_part('hour', dt_o) as hour,
                                                              TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                                              from data     
                                                              WHERE hour_range_o = :y  AND
                                                              id_car_fleet =:w ''')


        ################### ---- COSTS of EMISSIONS or POLLUTANTS ------- ########################################

        query_emissions_costs_origin = text('''WITH data AS(SELECT *
                                                                           FROM impacts.trips_emission_costs_fcd
                                                                           LEFT JOIN fcd.trips 
                                                                                       ON trips_emission_costs_fcd.id_trip = trips.id        
                                                                                         WHERE date(trips.dt_o) BETWEEN :x AND :xx   
                                                                                          AND trips.tod_o = :z      
                                                                                         /*limit 1000*/
                                                                      )
                                                                        SELECT id_car_fleet, id_trip, id_veh, dt_o, dt_d, id_zone_o, id_zone_d, nox_cost, nmvoc_cost, pm_cost, pmnnex_cost, co2_cost, wtt_co2_cost, 
                                                                        date_part('hour', dt_o) as hour,
                                                                        TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                                                        from data     
                                                                        WHERE hour_range_o = :y  AND
                                                                        id_car_fleet =:w ''')

        ################### ---- COSTS of EXTERNALITIES ------- ########################################

        query_externalities_costs_origin = text('''WITH data AS(SELECT *
                                                                                FROM impacts.trips_external_costs_fcd
                                                                                LEFT JOIN fcd.trips 
                                                                                            ON trips_external_costs_fcd.id_trip = trips.id        
                                                                                              WHERE date(trips.dt_o) BETWEEN :x AND :xx   
                                                                                               AND trips.tod_o = :z      
                                                                                              /*limit 1000*/
                                                                           )
                                                                             SELECT id_car_fleet, id_trip, id_veh, dt_o, dt_d, id_zone_o, id_zone_d, v0_cost, real_cost, deltatime_cost, acc_cost, noise_cost, 
                                                                             date_part('hour', dt_o) as hour,
                                                                             TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                                                             from data     
                                                                             WHERE hour_range_o = :y  AND
                                                                             id_car_fleet =:w ''')

        #### ---- query all trips having a staypoint ------#########
        ### staypoint = Home or WORK
        if (selected_stay_type == 21 or selected_stay_type == 22) and (selected_ZMU_tod != 9):

            stmt = query_emissions_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                     y=str(hourrange_id), z=str(tod), w=str(fleet_type))

            stmt_costs = query_emissions_costs_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                     y=str(hourrange_id), z=str(tod), w=str(fleet_type))

            stmt_external_costs = query_externalities_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                 xx=str(selected_ZMU_day_end),
                                                                 y=str(hourrange_id), z=str(tod), w=str(fleet_type))

        ###### staypoint: home or work and all Time of days (W, P, H)
        elif (selected_stay_type == 21 or selected_stay_type == 22) and (selected_ZMU_tod == 9):

            stmt = query_emissions_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                    y=str(hourrange_id))

            stmt_costs = query_emissions_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                 xx=str(selected_ZMU_day_end),
                                                                 y=str(hourrange_id))

            stmt_external_costs = query_externalities_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                              xx=str(selected_ZMU_day_end),
                                                                              y=str(hourrange_id))

        ### staypoint = Home + WORK
        elif (selected_stay_type == 23) and (selected_ZMU_tod != 9):
            stmt = query_emissions_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                    y=str(hourrange_id), z=str(tod))

            stmt_costs = query_emissions_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                 xx=str(selected_ZMU_day_end),
                                                                 y=str(hourrange_id), z=str(tod))

            stmt_external_costs = query_externalities_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                              xx=str(selected_ZMU_day_end),
                                                                              y=str(hourrange_id), z=str(tod))

        ### staypoint = Home + WORK and all Time of days (W, P, H)
        elif (selected_stay_type == 23) and (selected_ZMU_tod == 9):
            stmt = query_emissions_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                    y=str(hourrange_id))

            stmt_costs = query_emissions_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                 xx=str(selected_ZMU_day_end),
                                                                 y=str(hourrange_id))

            stmt_external_costs = query_externalities_costs_origin.bindparams(x=str(selected_ZMU_day_start),
                                                                              xx=str(selected_ZMU_day_end),
                                                                              y=str(hourrange_id))

        print(selected_stay_type)
        print(selected_ZMU_tod)

        ### ---> EMISSIONS <------#####################
        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        emission_origin_zones_day = pd.DataFrame(res)

        ### ---> COSTS of EMISSIONS <------#####################
        with engine.connect() as conn:
            res = conn.execute(stmt_costs).all()
        costs_origin_zones_day = pd.DataFrame(res)

        ### ---> COSTS of EXTERNALITIES <------#####################
        with engine.connect() as conn:
            res = conn.execute(stmt_external_costs).all()
        external_costs_origin_zones_day = pd.DataFrame(res)


        try:
            emission_origin_zones_day = pd.merge(emission_origin_zones_day, df_staypoints[['id_veh', 'id_stay_type']], on=['id_veh'], how='left')
        except (KeyError, UnboundLocalError):
            print("----- I am here at abort -404----------")
            session["check_ZMU_tod"] = 1
            print(session["check_ZMU_tod"])
            return render_template("index_zmu_emiss_select_day.html")
            session["check_ZMU_tod"] = session["ZMU_tod"]
            print(session["check_ZMU_tod"])
            # abort(404)

        #### merge with staypoints
        costs_origin_zones_day = pd.merge(costs_origin_zones_day, df_staypoints[['id_veh', 'id_stay_type']],
                                             on=['id_veh'], how='left')
        external_costs_origin_zones_day = pd.merge(external_costs_origin_zones_day, df_staypoints[['id_veh', 'id_stay_type']],
                                          on=['id_veh'], how='left')

        ## -----  get ZMU zones  -------- ################################
        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA['centroid'] = ZMU_ROMA.apply(wkb_tranformation_centroid, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA)

        ##### ---->>> Consider emission from ORIGIN (generation) @ ORIGIN  (highlight ORIGIN (coloured with the emission concentration at the Origin)

        #### use extennd emissions over all the traffic zones crossed during the trip (valid only for NOX, NMVOCs, PM, PM_nexh)
        if (selected_emission_type == 13 or selected_emission_type == 14 or selected_emission_type == 15 or selected_emission_type == 16):
            aggregated_gdf_emission = emission_origin_zones_day[
                ['zmu', 'ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt']].groupby(
                ['zmu'], sort=False).sum().reset_index().rename(
                columns={0: 'sum_ec', 1: 'sum_ec_wtt', 2: 'sum_nox', 3: 'sum_nmvoc', 4: 'sum_pm', 5: 'sum_pm_nexh',
                         6: 'sum_co2_eq', 7: 'sum_co2eq_wtt'})

        else:
            aggregated_gdf_emission = emission_origin_zones_day[['id_zone_o', 'ec','ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt']].groupby(['id_zone_o'], sort=False).sum().reset_index().rename(
                columns={0: 'sum_ec', 1:'sum_ec_wtt', 2:'sum_nox', 3:'sum_nmvoc', 4:'sum_pm', 5:'sum_pm_nexh', 6:'sum_co2_eq', 7:'sum_co2eq_wtt'})

            aggregated_gdf_emission.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)

        aggregated_gdf_emission = pd.merge(aggregated_gdf_emission, ZMU_ROMA, on=['zmu'], how='left')
        aggregated_gdf_emission = aggregated_gdf_emission[aggregated_gdf_emission['geometry'].notna()]

        aggregated_gdf_emission = aggregated_gdf_emission[
            ['ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt', 'index_zmu', 'POP_TOT_ZMU', 'zmu',
             'nome_comun', 'quartiere', 'geometry', 'pgtu']]

        aggregated_gdf_emission.replace([np.inf, -np.inf], np.nan, inplace=True)

        ## merge with total staypoints in each traffic ZONE ZMU
        aggregated_gdf_emission = pd.merge(aggregated_gdf_emission, all_staypoints,
                                           on='zmu', how='left')


        ######### ----->>> COSTS of EMISSIONS <<------------ ######################################################
        aggregated_gdf_costs = costs_origin_zones_day[
            ['id_zone_o', 'nox_cost', 'nmvoc_cost', 'pm_cost', 'pmnnex_cost', 'co2_cost', 'wtt_co2_cost']].groupby(['id_zone_o'],
                                                                                                          sort=False).sum().reset_index().rename(
            columns={0: 'sum_nox_cost', 1: 'sum_nmvoc_cost', 2: 'sum_pm_cost', 3: 'sum_pmnnex_cost', 4: 'sum_co2_cost', 5: 'sum_wtt_co2_cost'})

        aggregated_gdf_costs.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)

        aggregated_gdf_costs = pd.merge(aggregated_gdf_costs, ZMU_ROMA, on=['zmu'], how='left')
        aggregated_gdf_costs = aggregated_gdf_costs[aggregated_gdf_costs['geometry'].notna()]

        aggregated_gdf_costs = aggregated_gdf_costs[
            ['nox_cost', 'nmvoc_cost', 'pm_cost', 'pmnnex_cost', 'co2_cost', 'wtt_co2_cost', 'index_zmu', 'POP_TOT_ZMU', 'zmu',
             'nome_comun', 'quartiere', 'geometry', 'pgtu']]

        aggregated_gdf_costs.replace([np.inf, -np.inf], np.nan, inplace=True)

        ## merge with total staypoints in each traffic ZONE ZMU
        aggregated_gdf_costs = pd.merge(aggregated_gdf_costs, all_staypoints,
                                           on='zmu', how='left')




        ######### ----->>> EXTERNALITIES COSTS  <<------------ ######################################################
        aggregated_gdf_externalities = external_costs_origin_zones_day[
            ['id_zone_o', 'v0_cost', 'real_cost', 'deltatime_cost', 'acc_cost', 'noise_cost']].groupby(
            ['id_zone_o'],
            sort=False).sum().reset_index().rename(
            columns={0: 'sum_v0_cost', 1: 'sum_real_cost', 2: 'sum_deltatime_cost', 3: 'sum_acc_cost', 4: 'sum_noise_cost'})

        aggregated_gdf_externalities.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)

        aggregated_gdf_externalities = pd.merge(aggregated_gdf_externalities, ZMU_ROMA, on=['zmu'], how='left')
        aggregated_gdf_externalities = aggregated_gdf_externalities[aggregated_gdf_externalities['geometry'].notna()]

        aggregated_gdf_externalities = aggregated_gdf_externalities[
            ['v0_cost', 'real_cost', 'deltatime_cost', 'acc_cost', 'noise_cost', 'index_zmu', 'POP_TOT_ZMU',
             'zmu',
             'nome_comun', 'quartiere', 'geometry', 'pgtu']]

        aggregated_gdf_externalities.replace([np.inf, -np.inf], np.nan, inplace=True)

        ## merge with total staypoints in each traffic ZONE ZMU
        aggregated_gdf_externalities = pd.merge(aggregated_gdf_externalities, all_staypoints,
                                        on='zmu', how='left')

        aggregated_gdf_emission['zmu'] = aggregated_gdf_emission.zmu.astype('int')

        aggregated_gdf_emission.replace([np.inf, -np.inf], np.nan, inplace=True)
        aggregated_gdf_emission['ec'] = round(
            aggregated_gdf_emission['ec'], 2)
        aggregated_gdf_emission['ec_wtt'] = round(
            aggregated_gdf_emission['ec_wtt'], 2)
        aggregated_gdf_emission['nox'] = round(
            aggregated_gdf_emission['nox'], 2)
        aggregated_gdf_emission['nmvoc'] = round(
            aggregated_gdf_emission['nmvoc'], 2)
        aggregated_gdf_emission['pm'] = round(
            aggregated_gdf_emission['pm'], 2)
        aggregated_gdf_emission['pm_nexh'] = round(
            aggregated_gdf_emission['pm_nexh'], 2)
        aggregated_gdf_emission['co2eq'] = round(
            aggregated_gdf_emission['co2eq'], 2)
        aggregated_gdf_emission['co2eq_wtt'] = round(
            aggregated_gdf_emission['co2eq_wtt'], 2)


        # 'nox_cost', 'nmvoc_cost', 'pm_cost', 'pmnnex_cost', 'co2_cost', 'wtt_co2_cost'
        aggregated_gdf_costs['nox_cost'] = round(
            aggregated_gdf_costs['nox_cost'], 4)
        aggregated_gdf_costs['nmvoc_cost'] = round(
            aggregated_gdf_costs['nmvoc_cost'], 4)
        aggregated_gdf_costs['pm_cost'] = round(
            aggregated_gdf_costs['pm_cost'], 4)
        aggregated_gdf_costs['pmnnex_cost'] = round(
            aggregated_gdf_costs['pmnnex_cost'], 4)
        aggregated_gdf_costs['co2_cost'] = round(
            aggregated_gdf_costs['co2_cost'], 4)
        aggregated_gdf_costs['wtt_co2_cost'] = round(
            aggregated_gdf_costs['wtt_co2_cost'], 4)

        # 'v0_cost', 'real_cost', 'deltatime_cost', 'acc_cost', 'noise_cost'
        aggregated_gdf_externalities['v0_cost'] = round(
            aggregated_gdf_externalities['v0_cost'], 4)
        aggregated_gdf_externalities['real_cost'] = round(
            aggregated_gdf_externalities['real_cost'], 4)
        aggregated_gdf_externalities['deltatime_cost'] = round(
            aggregated_gdf_externalities['deltatime_cost'], 4)
        aggregated_gdf_externalities['acc_cost'] = round(
            aggregated_gdf_externalities['acc_cost'], 4)
        aggregated_gdf_externalities['noise_cost'] = round(
            aggregated_gdf_externalities['noise_cost'], 4)
        ### ---- EMISSIONS  <---- ##############
        try:
            aggregated_gdf_emission = gpd.GeoDataFrame(aggregated_gdf_emission)
        except IndexError:
            abort(404)

        ### ---- COSTS of EMISSIONS  <---- ##############
        try:
            aggregated_gdf_costs = gpd.GeoDataFrame(aggregated_gdf_costs)
        except IndexError:
            abort(404)

        ### ---- COSTS of EXTERNALITIES  <---- ##############
        try:
            aggregated_gdf_externalities = gpd.GeoDataFrame(aggregated_gdf_externalities)
        except IndexError:
            abort(404)


        ## save as .geojson file
        ### ---- EMISSIONS  <---- ##############
        aggregated_gdf_emission.to_file(filename=path_app + 'static/aggregated_gdf_emission.geojson',
                                       driver='GeoJSON')
        ### ---- COSTS of EMISSIONS  <---- ##############
        aggregated_gdf_costs.to_file(filename=path_app + 'static/aggregated_gdf_costs.geojson',
                                        driver='GeoJSON')

        ### ---- COSTS of EXTERNALITIES  <---- ##############
        aggregated_gdf_externalities.to_file(filename=path_app + 'static/aggregated_gdf_externalities.geojson',
                                     driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/aggregated_gdf_emission.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregated_emissions_zmu = \n" + old)  # assign the "var name" in the .geojson file

        with open(path_app + "static/aggregated_gdf_costs.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregate_costs_zmu = \n" + old)  # assign the "var name" in the .geojson file

        with open(path_app + "static/aggregated_gdf_externalities.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregate_externalities_zmu = \n" + old)  # assign the "var name" in the .geojson file





        ####### ----------------------------------------------------------- #######################
        ####### ----------------------------------------------------------- #######################
        #### make AGGREGATION BY DAY and by ORIGIN zone to find HOURLY PROFILE from all ORIGIN ZMUs


        query_emissions_origin_hourly_profile = text('''WITH data AS(
                                                SELECT *
                                                   FROM impacts.trips_cons_emis_fcd
                                                   LEFT JOIN fcd.trips 
                                                               ON trips_cons_emis_fcd.id_trip = trips.id        
                                                                 WHERE date(trips.dt_o) BETWEEN :x AND :xx   
                                                                  AND trips.tod_o = :z      
                                                                 /*limit 1000*/
                                              )
                                                SELECT id_car_fleet, id_trip, dt_o, dt_d, id_zone_o, id_zone_d, ec, ec_wtt, nox, nmvoc, pm, pm_nexh, co2eq, co2eq_wtt,
                                                date_part('hour', dt_o) as hour,
                                                TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                                from data  WHERE id_car_fleet =:w ''')

        stmt = query_emissions_origin_hourly_profile.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                 z=str(tod), w=str(fleet_type))
        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        emission_origin_zones_hourly_profile = pd.DataFrame(res)

        emission_origin_zones_hourly_profile.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
        emission_origin_zones_hourly_profile = emission_origin_zones_hourly_profile[
            emission_origin_zones_hourly_profile['zmu'].notna()]
        emission_origin_zones_hourly_profile['zmu'] = emission_origin_zones_hourly_profile.zmu.astype('int')

        ##### --- make sums of all emissions ----***** ###########################################################
        ########################### ///////////// ------- ****** //////// ***** #################### Mei Ru -----#
        aggregated_emission_origin_zones_hourly_profile = emission_origin_zones_hourly_profile[
            ['zmu', 'hour', 'ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt']].groupby(['hour', 'zmu'],
                                                                                  sort=False).sum().reset_index().rename(
            columns={0: 'sum'})

        aggregated_emission_origin_zones_hourly_profile = emission_origin_zones_hourly_profile[
            ['zmu', 'hour', 'ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt']].groupby(['hour', 'zmu'],
            sort=False).sum().reset_index().rename(
            columns={0: 'sum_ec', 1: 'sum_ec_wtt', 2: 'sum_nox', 3: 'sum_nmvoc', 4: 'sum_pm', 5: 'sum_pm_nexh',
                     6: 'sum_co2_eq', 7: 'sum_co2eq_wtt'})

        aggregated_emission_origin_zones_hourly_profile = pd.merge(aggregated_emission_origin_zones_hourly_profile, ZMU_ROMA, on=['zmu'], how='left')
        aggregated_emission_origin_zones_hourly_profile = aggregated_emission_origin_zones_hourly_profile[aggregated_emission_origin_zones_hourly_profile['geometry'].notna()]

        aggregated_emission_origin_zones_hourly_profile = aggregated_emission_origin_zones_hourly_profile[
            ['ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt', 'index_zmu', 'POP_TOT_ZMU', 'zmu', 'hour',
             'nome_comun', 'quartiere', 'pgtu']]

        aggregated_emission_origin_zones_hourly_profile.replace([np.inf, -np.inf], np.nan, inplace=True)


        aggregated_emission_origin_zones_hourly_profile['hour'] = aggregated_emission_origin_zones_hourly_profile.hour.astype('int')
        aggregated_emission_origin_zones_hourly_profile['ec'] = round(aggregated_emission_origin_zones_hourly_profile['ec'], 2)
        aggregated_emission_origin_zones_hourly_profile['ec_wtt'] = round(
            aggregated_emission_origin_zones_hourly_profile['ec_wtt'], 2)
        aggregated_emission_origin_zones_hourly_profile['nox'] = round(
            aggregated_emission_origin_zones_hourly_profile['nox'], 2)
        aggregated_emission_origin_zones_hourly_profile['nmvoc'] = round(
            aggregated_emission_origin_zones_hourly_profile['nmvoc'], 2)
        aggregated_emission_origin_zones_hourly_profile['pm'] = round(
            aggregated_emission_origin_zones_hourly_profile['pm'], 2)
        aggregated_emission_origin_zones_hourly_profile['pm_nexh'] = round(
            aggregated_emission_origin_zones_hourly_profile['pm_nexh'], 2)
        aggregated_emission_origin_zones_hourly_profile['co2eq'] = round(
            aggregated_emission_origin_zones_hourly_profile['co2eq'], 2)
        aggregated_emission_origin_zones_hourly_profile['co2eq_wtt'] = round(
            aggregated_emission_origin_zones_hourly_profile['co2eq_wtt'], 2)

        aggregated_emission_origin_zones_hourly_profile['start_date'] = selected_ZMU_day_start
        aggregated_emission_origin_zones_hourly_profile['end_date'] = selected_ZMU_day_end
        aggregated_emission_origin_zones_hourly_profile['fleet'] = fleet_type

        aggregated_emission_origin_zones_hourly_profile.to_csv(
            path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')


        ##### --->>>>>> make the sessions data...<<<------------################################
        ### convert Geodataframe into .geojson...
        session["aggregated_emissions_origin_zones"] = aggregated_gdf_emission.to_json()
        session["aggregated_costs_origin_zones"] = aggregated_gdf_costs.to_json()
        session["aggregated_externalities_costs_origin_zones"] = aggregated_gdf_externalities.to_json()
        # print(session["aggregated_gdf_OD_GTFS"])

        # print(session['id'])
        return render_template("index_zmu_emiss_select_hour.html",
                               var_ZMU_day=selected_ZMU_day_start,
                               session_aggregated_emissions_oring_zones = session["aggregated_emissions_origin_zones"],
                               session_aggregated_costs_oring_zones = session["aggregated_costs_origin_zones"],
                               session_aggregated_externalities_costs_oring_zones = session["aggregated_externalities_costs_origin_zones"])

from flask import send_file

@app.route('/download/',methods=["GET"])
def download():
    return send_file(
        'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv',
        mimetype='text/csv',
        download_name='aggregated_emission_file.csv',
        as_attachment=True
    )



###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################




###############################################################################################
#########------/////////////////////////////////////////////////////--------##################
#########----- HOME & WORK locations ----------------------------############################
############################################################################################
##########################################################################################
########################################################################################
######################################################################################
####################################################################################
##################################################################################


### select hour (ZMU)...from Database
@app.route('/home_work_selector/', methods=['GET', 'POST'])
def home_work_selector():
    if request.method == "POST":
        # selected_ZMU_hour = 9
        # selected_ZMU_day = '2022-10-04'
        session["ZMU_day"] = '2022-10-04'
        session["ZMU_hour"] = 9

        try:
            selected_ZMU_day = session["ZMU_day"].strftime('%Y-%m-%d')
            selected_ZMU_hour = session["ZMU_hour"]
            print("--selected_ZMU_day--->: ", selected_ZMU_day, "and", "---selected_ZMU_hour--->: ", selected_ZMU_hour)
        except AttributeError:
            abort(404)

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool
        from sqlalchemy.sql import text

        ####***************************************************************************************##################
        ##--------------->>>>  query on HOME LOCATION (Special dataset DB ROMA 2019) ------------- ###################
        engine_2019 = create_engine("postgresql://postgres:superuser@192.168.134.36:5432/HAIG_ROMA")

        query_home = text('''SELECT  "Id_Term", "Notti_1Casa", "Notti_2Casa", "Notti_Out",
                                                          "Coord_1_Casa", "Coord_2_Casa", "Trans_Confine" 
                                                         from "idterm_Info_FK_2022"
                                                         WHERE  "Notti_1Casa" > 0 
                                                                                /*limit 1000*/ ''')  # "Veh_Type" = 1 AND

        stmt = query_home
        with engine_2019.connect() as conn:
            res = conn.execute(stmt).all()
        homes_locations = pd.DataFrame(res)
        homes_locations.drop_duplicates(['Id_Term'], inplace=True)

        ############################
        #### HOME ##################
        lats_1home = []
        lons_1home = []
        lats_2home = []
        lons_2home = []
        n_notti1home = []
        n_notti2home = []

        Id_Term1 = []
        Id_Term2 = []

        for i in range(len(homes_locations)):
            # print(i)
            # print(homes_locations.iloc[i])
            if ((homes_locations.iloc[i].Coord_1_Casa != '{0,0}') and (
                    homes_locations.iloc[i].Coord_1_Casa != '{-1,-1}')):
                latitude1 = (re.split('; |, |\{|  \n |\,| \n |\}| ', homes_locations.iloc[i].Coord_1_Casa))[2]
                longitude1 = (re.split('; |, |\{|  \n |\,| \n |\}| ', homes_locations.iloc[i].Coord_1_Casa))[1]
                idterm = homes_locations.iloc[i].Id_Term
                n_notti = homes_locations.iloc[i].Notti_1Casa
                lats_1home.append(latitude1)
                lons_1home.append(longitude1)
                Id_Term1.append(idterm)
                n_notti1home.append(n_notti)

            if ((homes_locations.iloc[i].Coord_2_Casa != '{0,0}') and (
                    homes_locations.iloc[i].Coord_2_Casa != '{-1,-1}')):
                latitude2 = (re.split('; |, |\{|  \n |\,| \n |\}| ', homes_locations.iloc[i].Coord_2_Casa))[2]
                longitude2 = (re.split('; |, |\{|  \n |\,| \n |\}| ', homes_locations.iloc[i].Coord_2_Casa))[1]
                idterm = homes_locations.iloc[i].Id_Term
                n_notti = homes_locations.iloc[i].Notti_2Casa
                lats_2home.append(latitude2)
                lons_2home.append(longitude2)
                Id_Term2.append(idterm)
                n_notti2home.append(n_notti)

        df_home1_locations = pd.DataFrame({'lat_casa': lats_1home,
                                           'lon_casa': lons_1home,
                                           'n_notti': n_notti1home,
                                           'Id_Term': Id_Term1})

        df_home2_locations = pd.DataFrame({'lat_casa': lats_2home,
                                           'lon_casa': lons_2home,
                                           'n_notti': n_notti2home,
                                           'Id_Term': Id_Term2})

        df_home_locations = pd.concat([df_home1_locations,
                                       df_home2_locations])

        df_home_locations = df_home1_locations

        ## ----->> crop the data out of the inner border (Riquadro interno)
        M = 5  # Fattore Moltiplicativo (per variare il riquadro interno)
        D_lon = 0.0065
        D_lat = 0.0045  # Delta gradi, corrispondenti a 500 m.

        # ________________________________________________Riscontrati
        Lon_Min_Ris = 11.9214
        Lon_Max_Ris = 13.22569
        Lat_Min_Ris = 41.56645
        Lat_Max_Ris = 42.13107
        # ________________________________________________Riquadro interno
        Lon_Min_Int = Lon_Min_Ris + D_lon * 20
        Lon_Max_Int = Lon_Max_Ris - D_lon * M
        Lat_Min_Int = Lat_Min_Ris + D_lat * M
        Lat_Max_Int = Lat_Max_Ris - D_lat * M

        df_home_locations['lat_casa'] = df_home_locations.lat_casa.astype('float')
        df_home_locations['lon_casa'] = df_home_locations.lon_casa.astype('float')

        df_home_locations = df_home_locations[
            (df_home_locations['lat_casa'] <= Lat_Max_Int) & (df_home_locations['lat_casa'] >= Lat_Min_Int) &
            (df_home_locations['lon_casa'] >= Lon_Min_Int) & (df_home_locations['lon_casa'] <= Lon_Max_Int)]

        ####-----> make a Geodataframe....
        geometry = [Point(xy) for xy in zip(df_home_locations.lon_casa, df_home_locations.lat_casa)]
        crs = {'init': 'epsg:4326'}
        gdf_home_locations = GeoDataFrame(df_home_locations, crs=crs, geometry=geometry)
        # save first as geojson file

        gdf_home_locations.to_file(filename=path_app + 'static/home_locations_roma_2022.geojson',
                                   driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/home_locations_roma_2022.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var home_locations_2022 = \n" + old)  # assign the "var name" in the .geojson file

        #############################################################################################################
        ####***************************************************************************************##################
        ##--------------->>>>  query on  W O R K  LOCATION (Special dataset DB ROMA 2019) ------------- #############

        engine_2019 = create_engine("postgresql://postgres:superuser@192.168.134.36:5432/HAIG_ROMA")

        query_work = text('''SELECT  "Id_Term", "Coord_1_Lavoro", "Coord_2_Lavoro", "N_Lavori",
                                                             "Giorni_al_1Lav", "Giorni_al_2Lav", "Trans_Confine" 
                                                            from "idterm_Info_FK_2022"
                                                            WHERE "Giorni_al_1Lav" > 0 
                                                                                   /*limit 1000*/ ''')  # "Veh_Type" = 1 AND

        stmt = query_work
        with engine_2019.connect() as conn:
            res = conn.execute(stmt).all()
        work_locations = pd.DataFrame(res)
        work_locations.drop_duplicates(['Id_Term'], inplace=True)

        ############################
        #### WORK ##################
        lats_1work = []
        lons_1work = []
        lats_2work = []
        lons_2work = []
        n_giorni1work = []
        n_giorni2work = []

        Id_Term1 = []
        Id_Term2 = []

        for i in range(len(work_locations)):
            # print(i)
            # print(work_locations.iloc[i])
            if ((work_locations.iloc[i].Coord_1_Lavoro != '{0,0}') and (
                    work_locations.iloc[i].Coord_1_Lavoro != '{-1,-1}')):
                latitude1 = (re.split('; |, |\{|  \n |\,| \n |\}| ', work_locations.iloc[i].Coord_1_Lavoro))[2]
                longitude1 = (re.split('; |, |\{|  \n |\,| \n |\}| ', work_locations.iloc[i].Coord_1_Lavoro))[1]
                idterm = work_locations.iloc[i].Id_Term
                n_working_days = work_locations.iloc[i].Giorni_al_1Lav
                lats_1work.append(latitude1)
                lons_1work.append(longitude1)
                Id_Term1.append(idterm)
                n_giorni1work.append(n_working_days)

            if ((work_locations.iloc[i].Coord_2_Lavoro != '{0,0}') and (
                    work_locations.iloc[i].Coord_2_Lavoro != '{-1,-1}')):
                latitude2 = (re.split('; |, |\{|  \n |\,| \n |\}| ', work_locations.iloc[i].Coord_2_Lavoro))[2]
                longitude2 = (re.split('; |, |\{|  \n |\,| \n |\}| ', work_locations.iloc[i].Coord_2_Lavoro))[1]
                idterm = work_locations.iloc[i].Id_Term
                n_working_days = work_locations.iloc[i].Giorni_al_2Lav
                lats_2work.append(latitude2)
                lons_2work.append(longitude2)
                Id_Term2.append(idterm)
                n_giorni2work.append(n_working_days)

        df_work1_locations = pd.DataFrame({'lat_work': lats_1work,
                                           'lon_work': lons_1work,
                                           'n_working_days': n_giorni1work,
                                           'Id_Term': Id_Term1})

        df_work2_locations = pd.DataFrame({'lat_work': lats_2work,
                                           'lon_work': lons_2work,
                                           'n_working_days': n_giorni2work,
                                           'Id_Term': Id_Term2})

        df_work_locations = pd.concat([df_work1_locations,
                                       df_work2_locations])

        ## ----->> crop the data out of the inner border (Riquadro interno)
        M = 5  # Fattore Moltiplicativo (per variare il riquadro interno)
        D_lon = 0.0065
        D_lat = 0.0045  # Delta gradi, corrispondenti a 500 m.

        # ________________________________________________Riscontrati
        Lon_Min_Ris = 11.9214
        Lon_Max_Ris = 13.22569
        Lat_Min_Ris = 41.56645
        Lat_Max_Ris = 42.13107
        # ________________________________________________Riquadro interno
        Lon_Min_Int = Lon_Min_Ris + D_lon * 20
        Lon_Max_Int = Lon_Max_Ris - D_lon * M
        Lat_Min_Int = Lat_Min_Ris + D_lat * M
        Lat_Max_Int = Lat_Max_Ris - D_lat * M

        df_work_locations['lat_work'] = df_work_locations.lat_work.astype('float')
        df_work_locations['lon_work'] = df_work_locations.lon_work.astype('float')

        df_work_locations = df_work_locations[
            (df_work_locations['lat_work'] <= Lat_Max_Int) & (df_work_locations['lat_work'] >= Lat_Min_Int) &
            (df_work_locations['lon_work'] >= Lon_Min_Int) & (df_work_locations['lon_work'] <= Lon_Max_Int)]

        ####-----> make a Geodataframe....
        geometry = [Point(xy) for xy in zip(df_work_locations.lon_work, df_work_locations.lat_work)]
        crs = {'init': 'epsg:4326'}
        gdf_work_locations = GeoDataFrame(df_work_locations, crs=crs, geometry=geometry)

        # save first as geojson file
        gdf_work_locations.to_file(filename=path_app + 'static/work_locations_roma_2022.geojson',
                                   driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/work_locations_roma_2022.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var work_locations_2022 = \n" + old)  # assign the "var name" in the .geojson file


#######################################################################################################
#########################################################################################################
###########################################################################################################
##############################################################################################################
#################################################################################################################
####################################################################################################################
#######################################################################################################################


#######///////////////////////////////////////////////////////////////////////##############
#####-----------------------------------------------------------------------------##########
#######///////////////////////////////////////////////////////////////////////##############
#####-----------------------------------------------------------------------------##########
### ------  HIGHLIGHT ZMUs crossed from ORIGIN ZONES to all DESTINATION ZMU zones --- #####
### ------------------------------------------------------------------------------- ########



### select DATA TYPE  -------- #################################
@app.route('/ZMU_paths/', methods=['GET', 'POST'])
def ZMU_paths():

    import glob
    session["ZMU_day_start"] = '2022-10-01'
    session["ZMU_day_end"] = '2022-10-15'
    session["ZMU_hourrange"] = 2
    session["ZMU_tod"] = 6
    # session["data_type"] = 11

    #### ----- check for session ----> data type (FCD, SYNTHETIC)
    stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
    stored_data_type_files.sort(key=os.path.getmtime)
    stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]

    with open(stored_data_type_file) as file:
        selected_data_type = file.read()
    print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
    session["data_type"] = selected_data_type

    return render_template("index_zmu_paths_select_day.html")


### select DATA TYPE  -------- #################################
@app.route('/ZMU_paths_data_type/', methods=['GET', 'POST'])
def ZMU_paths_data_type():
    if request.method == "POST":
        session["data_type"] = request.form.get("data_type")
        selected_data_type = session["data_type"]
        print("selected_data_type:", selected_data_type)
        selected_data_type = str(selected_data_type)

        with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_data_type))

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        # selected_data_type = int(selected_data_type)
        if selected_data_type == '11':  ## FCD data
            print("FCD data")
            print("selected_data_type:--------selector", selected_data_type)

        elif selected_data_type == '12':  ## SYNTHETIC DATA
            print("SYNTHETIC DATA")
            print("selected_data_type:--------selector", selected_data_type)


        return render_template("index_zmu_paths_select_day.html")


@app.route('/ZMU_paths_day_selector/', methods=['GET', 'POST'])
### select day (ZMU)...from Database
def ZMU_paths_day_selector():
    if request.method == "POST":
        ###--->> record the ZMU_day in into the Flask Session
        ## TRY if session exists

        ##### ------ daterangepicker ----- ############################################
        ###############################################################################

        try:
            data = request.form["daterange"]
            session['input_data_range'] = data
            print("-------------data-------------:", data)
        except:
            data = "10/12/2022 - 10/13/2022"

        try:
            start_date = data.split(" - ")[0]
            start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            session["ZMU_day_start"] = str(start_date.date())
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("gotta!!!----->> selected_ZMU_day_start:", session["ZMU_day_start"])  ##--->> only get date
            selected_ZMU_day_start = str(selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            end_date = data.split(" - ")[1]
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            session["ZMU_day_end"] = str(end_date.date())
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("gotta!!!----->> selected_ZMU_day_end:", session["ZMU_day_end"])  ##--->> only get date
            selected_ZMU_day_end = str(selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable selected_ZMU_day_end: ", session["ZMU_day_end"])

        try:
            with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "r") as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
        except:
            # for stored_tod_file in glob.glob(path_app + "static/params/selected_data_type_*.txt"):
            #    print(stored_tod_file)
            stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
            stored_data_type_files.sort(key=os.path.getmtime)
            stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]
            with open(stored_data_type_file) as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)

        selected_data_type = session["data_type"]
        selected_data_type = int(selected_data_type)
        print("selected_data_type-------2: ", session["data_type"])

        return render_template("index_zmu_paths_select_day.html")


@app.route('/ZMU_paths_hour_selector/', methods=['GET', 'POST'])
def ZMU_paths_hour_selector():
    if request.method == "POST":

        import glob

        session["ZMU_tod"] = 6
        # selected_ZMU_hourrange = "1"
        # selected_ZMU_day_start = '2022-10-18'
        # selected_ZMU_day_end = '2022-10-22'
        # session["ZMU_tod"] = 6
        # tod = "W"

        try:
            # selected_ZMU_day_start = session["ZMU_day_start"].strftime('%Y-%m-%d')
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("day from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            # selected_ZMU_day_end = session["ZMU_day_end"].strftime('%Y-%m-%d')
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("day from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])

        try:
            with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "r") as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
        except:
            # for stored_tod_file in glob.glob(path_app + "static/params/selected_data_type_*.txt"):
            #    print(stored_tod_file)
            stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
            stored_data_type_files.sort(key=os.path.getmtime)
            stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]
            with open(stored_data_type_file) as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)

        selected_data_type = session["data_type"]
        selected_data_type = int(selected_data_type)
        print("selected_data_type-------2: ", session["data_type"])

        ## TRY if session exists
        try:
            session["ZMU_hourrange"] = request.form.get("ZMU_hourrange")
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
            selected_ZMU_hourrange = str(selected_ZMU_hourrange)
        except:
            session["ZMU_hourrange"] = 2
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])

        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_hourrange = int(selected_ZMU_hourrange)
        if selected_ZMU_hourrange == 0:  ## 00:00 ---> 07:00
            hourrange_id = "N1"
        elif selected_ZMU_hourrange == 1:  ## 07:00 ----> 10:00
            hourrange_id = "M1"
        elif selected_ZMU_hourrange == 2:  ## 10:00 ---> 14:00
            hourrange_id = "M2"
        elif selected_ZMU_hourrange == 3:  ##  14:00 ---> 16:00
            hourrange_id = "A1"
        elif selected_ZMU_hourrange == 4:  ## 16:00 ---> 20:00
            hourrange_id = "A2"
        elif selected_ZMU_hourrange == 5:  ## 20:00 ---> 24:00
            hourrange_id = "A3"

        session["hourrange_id"] = hourrange_id
        print("------hourrange_id------------>>>:", hourrange_id)
        print("selected data type...........................................", selected_data_type)

        session["tod"] = "W"
        tod = session["tod"]
        print("----- tod------:", session["tod"])

        ######################################################################################
        #####----- make selection between FCD data and Synthetic data ------ #################
        ######################################################################################
        if selected_data_type == 11:  ## FCD data ##
            print("--------------------------------------------------------FCD data")
            ## switch to table.........TRIPD----FCD data
            from sqlalchemy import create_engine
            from sqlalchemy import exc
            import sqlalchemy as sal
            from sqlalchemy.pool import NullPool

            engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
            from sqlalchemy.sql import text

            ##### ----- destinations ------- #################################
            query_destination = text('''SELECT * FROM fcd.trips
                                                         WHERE date(dt_d) BETWEEN :x AND :xx 
                                                          AND hour_range_d = :y
                                                          AND tod_d = :z ''')
            stmt = query_destination.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                y=str(hourrange_id), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            destination_routes = pd.DataFrame(res)

            ##### ----- origins ------- #################################
            query_origin = text('''SELECT * FROM fcd.trips
                                                        WHERE date(dt_o) BETWEEN :x AND :xx 
                                                        AND hour_range_o = :y
                                                        AND tod_o = :z ''')
            stmt = query_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                           y=str(hourrange_id), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_routes = pd.DataFrame(res)

        elif selected_data_type == 12:  ## SYNTHETIC DATA ##
            print("---------------------------------------------------SYNTHETIC DATA")
            ## switch to table.........TRIPD----FCD data
            from sqlalchemy import create_engine
            from sqlalchemy import exc
            import sqlalchemy as sal
            from sqlalchemy.pool import NullPool

            engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
            from sqlalchemy.sql import text

            ##### ----- destinations ------- #################################
            query_destination = text('''SELECT * FROM carlo.trips
                                                WHERE date(dt_d) BETWEEN :x AND :xx 
                                                                     AND hour_range_d = :y
                                                                     AND tod_d = :z ''')
            stmt = query_destination.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                y=str(hourrange_id), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            destination_routes = pd.DataFrame(res)

            ##### ----- origins ------- #################################
            query_origin = text('''SELECT * FROM carlo.trips
                                                WHERE date(dt_o) BETWEEN :x AND :xx 
                                                                   AND hour_range_o = :y
                                                                   AND tod_o = :z ''')
            stmt = query_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                           y=str(hourrange_id), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_routes = pd.DataFrame(res)


        ## -----  get ZMU zones  -------- ################################
        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA_with_population['centroid'] = ZMU_ROMA_with_population.apply(wkb_tranformation_centroid, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA_with_population)

        ### ----- DESTINATIONS ---------------------------------- ##################################################

        ## remove none values
        df_gdf_destination_routes = destination_routes[
            ['p_after', 'tt', 'id', 'dt_d', 'dist', 'id_zone_d', 'geom']]
        df_gdf_destination_routes.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
        df_gdf_destination_routes = df_gdf_destination_routes[df_gdf_destination_routes['zmu'].notna()]
        df_gdf_destination_routes['zmu'] = df_gdf_destination_routes.zmu.astype('int')

        df_gdf_destination_routes.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
        df_gdf_destination_routes.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
        df_gdf_destination_routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
        df_gdf_destination_routes.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

        ### ----- ORIGIN ---------------------------------- ##################################################

        ## remove none values
        df_gdf_origin_routes = origin_routes[
            ['p_before', 'tt', 'id', 'dt_o', 'dist', 'id_zone_o', 'geom']]
        df_gdf_origin_routes.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
        df_gdf_origin_routes = df_gdf_origin_routes[df_gdf_origin_routes['zmu'].notna()]
        df_gdf_origin_routes['zmu'] = df_gdf_origin_routes.zmu.astype('int')

        df_gdf_origin_routes.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
        df_gdf_origin_routes.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
        df_gdf_origin_routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
        df_gdf_origin_routes.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

        ### only CONSIDER "idtrajectories" from DIFFERENT zones ZMU
        crossing_zones = pd.merge(df_gdf_origin_routes[['zmu', 'idtrajectory']],
                                  df_gdf_destination_routes[['zmu', 'idtrajectory']], on=['idtrajectory'],
                                  how='inner')
        crossing_zones.columns = ['zmu_origin', 'idtrajectory', 'zmu_destination']

        ## keep only "idtrajectories" with different zmu_origin and zmu_destination
        df_crossed_zmu = []
        for i in range(len(crossing_zones)):
            if (crossing_zones.zmu_origin.iloc[i] != crossing_zones.zmu_destination.iloc[i]):
                # print("============ got it ! ===================")
                crossed_zmu = pd.DataFrame({'zmu_origin': [crossing_zones.zmu_origin.iloc[i]],
                                            'idtrajectory': [crossing_zones.idtrajectory.iloc[i]],
                                            'zmu_destination': [crossing_zones.zmu_destination.iloc[i]]})
                df_crossed_zmu.append(crossed_zmu)
        crossed_zmu = pd.concat(df_crossed_zmu)

        crossed_zmu.rename({'zmu_origin': 'zmu'}, axis=1, inplace=True)
        crossed_zmu = pd.merge(crossed_zmu, ZMU_ROMA, on=['zmu'], how='left')
        crossed_zmu = crossed_zmu[['zmu', 'index_zmu', 'idtrajectory', 'zmu_destination']]
        crossed_zmu.replace([np.inf, -np.inf], np.nan, inplace=True)
        crossed_zmu.dropna(inplace=True)
        crossed_zmu['index_zmu'] = crossed_zmu.index_zmu.astype('int')

        ## save "crossed_zmu" and "df_gdf_destination_routes" into csv files....
        ### THESE are the ORIGIN ---> DESTINATION matrices ---------------#############################
        crossed_zmu.to_csv(path_app + 'static/crossed_zmu_' + session.sid + '.csv')
        df_gdf_destination_routes.to_csv(
            path_app + 'static/df_gdf_destination_routes_path_zmu_' + session.sid + '.csv')


        return render_template("index_zmu_paths_select_hour.html")  # data_ZMU_path=data_ZMU_path



@app.route('/ZMU_paths_tod_selector/', methods=['GET', 'POST'])
def ZMU_paths_tod_selector():
    if request.method == "POST":
        import glob
        try:
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("hour from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("hour from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])

        try:
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
        except:
            selected_ZMU_hourrange = 2
            session["ZMU_hourrange"] = selected_ZMU_hourrange
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])

        try:
            with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "r") as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
        except:
            stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
            stored_data_type_files.sort(key=os.path.getmtime)
            stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]
            with open(stored_data_type_file) as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)

        selected_data_type = session["data_type"]
        selected_data_type = int(selected_data_type)
        print("selected_data_type-------2: ", session["data_type"])

        try:
            selected_hourrange = session["hourrange_id"]
            selected_hourrange = str(selected_hourrange)
            print("selected_hourrange:", selected_hourrange)
        except:
            selected_hourrange = "A2"
            session["hourrange_id"] = selected_hourrange
            print("selected_hourrange: ", session["hourrange_id"])

        ## TRY if session exists (get "tod")
        try:
            session["ZMU_tod"] = request.form.get("ZMU_tod")
            selected_ZMU_tod = session["ZMU_tod"]
            print("selected_ZMU_tod:", selected_ZMU_tod)
            selected_ZMU_tod = str(selected_ZMU_tod)
        except:
            session["ZMU_tod"] = 7
            selected_ZMU_tod = session["ZMU_tod"]
            print("selected_ZMU_tod: ", session["ZMU_tod"])

        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_tod = int(selected_ZMU_tod)
        if selected_ZMU_tod == 6:  ## WORKING day
            tod = "W"
        elif selected_ZMU_tod == 7:  ## PRE holiday
            tod = "P"
        elif selected_ZMU_tod == 8:  ## HOLIDAY
            tod = "H"

        session["tod"] = tod
        print("------tod------------>>>:", tod)

        ######################################################################################
        #####----- make selection between FCD data and Synthetic data ------ #################
        ######################################################################################
        if selected_data_type == 11:  ## FCD data ##
            print("--------------------------------------------------------FCD data")
            ## switch to table.........TRIPD----FCD data
            from sqlalchemy import create_engine
            from sqlalchemy import exc
            import sqlalchemy as sal
            from sqlalchemy.pool import NullPool

            engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
            from sqlalchemy.sql import text

            ##### ----- destinations ------- #################################
            query_destination = text('''SELECT * FROM fcd.trips
                                                         WHERE date(dt_d) BETWEEN :x AND :xx 
                                                          AND hour_range_d = :y
                                                          AND tod_d = :z ''')
            stmt = query_destination.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                y=str(selected_hourrange), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            destination_routes = pd.DataFrame(res)

            ##### ----- origins ------- #################################
            query_origin = text('''SELECT * FROM fcd.trips
                                                        WHERE date(dt_o) BETWEEN :x AND :xx 
                                                        AND hour_range_o = :y
                                                        AND tod_o = :z ''')
            stmt = query_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                           y=str(selected_hourrange), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_routes = pd.DataFrame(res)

        elif selected_data_type == 12:  ## SYNTHETIC DATA ##
            print("---------------------------------------------------SYNTHETIC DATA")

            ## switch to table.........TRIPD----FCD data
            from sqlalchemy import create_engine
            from sqlalchemy import exc
            import sqlalchemy as sal
            from sqlalchemy.pool import NullPool

            engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
            from sqlalchemy.sql import text

            ##### ----- destinations ------- #################################
            query_destination = text('''SELECT * FROM carlo.trips
                                                        WHERE date(dt_d) BETWEEN :x AND :xx 
                                                         AND hour_range_d = :y
                                                         AND tod_d = :z ''')
            stmt = query_destination.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                y=str(selected_hourrange), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            destination_routes = pd.DataFrame(res)

            ##### ----- origins ------- #################################
            query_origin = text('''SELECT * FROM carlo.trips
                                                   WHERE date(dt_o) BETWEEN :x AND :xx 
                                                   AND hour_range_o = :y
                                                   AND tod_o = :z ''')
            stmt = query_origin.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                           y=str(selected_hourrange), z=str(tod))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            origin_routes = pd.DataFrame(res)

        ## -----  get ZMU zones  -------- ################################
        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        ZMU_ROMA_with_population = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA_with_population['centroid'] = ZMU_ROMA_with_population.apply(wkb_tranformation_centroid, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA_with_population)

        #### -------------------------------------------- ##########################################################
        #### -------------------------------------------- ##########################################################
        #### -------------------------------------------- ##########################################################

        ### ----- DESTINATIONS ---------------------------------- ##################################################

        ## remove none values
        df_gdf_destination_routes = destination_routes[
            ['p_after', 'tt', 'id', 'dt_d', 'dist', 'id_zone_d', 'geom']]
        df_gdf_destination_routes.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
        df_gdf_destination_routes = df_gdf_destination_routes[df_gdf_destination_routes['zmu'].notna()]
        df_gdf_destination_routes['zmu'] = df_gdf_destination_routes.zmu.astype('int')

        df_gdf_destination_routes.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
        df_gdf_destination_routes.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
        df_gdf_destination_routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
        df_gdf_destination_routes.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

        ### ----- ORIGIN ---------------------------------- ##################################################

        ## remove none values
        df_gdf_origin_routes = origin_routes[
            ['p_before', 'tt', 'id', 'dt_o', 'dist', 'id_zone_o', 'geom']]
        df_gdf_origin_routes.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
        df_gdf_origin_routes = df_gdf_origin_routes[df_gdf_origin_routes['zmu'].notna()]
        df_gdf_origin_routes['zmu'] = df_gdf_origin_routes.zmu.astype('int')

        df_gdf_origin_routes.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
        df_gdf_origin_routes.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
        df_gdf_origin_routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
        df_gdf_origin_routes.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

        ### only CONSIDER "idtrajectories" from DIFFERENT zones ZMU
        crossing_zones = pd.merge(df_gdf_origin_routes[['zmu', 'idtrajectory']],
                                  df_gdf_destination_routes[['zmu', 'idtrajectory']], on=['idtrajectory'],
                                  how='inner')
        crossing_zones.columns = ['zmu_origin', 'idtrajectory', 'zmu_destination']

        ## keep only "idtrajectories" with different zmu_origin and zmu_destination
        df_crossed_zmu = []
        for i in range(len(crossing_zones)):
            if (crossing_zones.zmu_origin.iloc[i] != crossing_zones.zmu_destination.iloc[i]):
                # print("============ got it ! ===================")
                crossed_zmu = pd.DataFrame({'zmu_origin': [crossing_zones.zmu_origin.iloc[i]],
                                            'idtrajectory': [crossing_zones.idtrajectory.iloc[i]],
                                            'zmu_destination': [crossing_zones.zmu_destination.iloc[i]]})
                df_crossed_zmu.append(crossed_zmu)
        crossed_zmu = pd.concat(df_crossed_zmu)

        crossed_zmu.rename({'zmu_origin': 'zmu'}, axis=1, inplace=True)
        crossed_zmu = pd.merge(crossed_zmu, ZMU_ROMA, on=['zmu'], how='left')
        crossed_zmu = crossed_zmu[['zmu', 'index_zmu', 'idtrajectory', 'zmu_destination']]
        crossed_zmu.replace([np.inf, -np.inf], np.nan, inplace=True)
        crossed_zmu.dropna(inplace=True)
        crossed_zmu['index_zmu'] = crossed_zmu.index_zmu.astype('int')

        ## save "crossed_zmu" and "df_gdf_destination_routes" into csv files....
        ### THESE are the ORIGIN ---> DESTINATION matrices ---------------#############################
        crossed_zmu.to_csv(path_app + 'static/crossed_zmu_' + session.sid + '.csv')
        df_gdf_destination_routes.to_csv(
            path_app + 'static/df_gdf_destination_routes_path_zmu_' + session.sid + '.csv')

        return render_template("index_zmu_paths_select_hour.html")




@app.route('/choose_zmu_index_static', methods=['POST'])
def choose_zmu_index_static():
    data = request.json['data']
    session["ZMU_index"] = data
    print("I am here...selected_index_zmu is: ", session["ZMU_index"])
    print("-------------- I am here...selected_index_zmu is:---------------------- ", session["ZMU_index"])
    return jsonify({'result': session["ZMU_index"]})


@app.route('/choose_zmu_index', methods=['POST'])
def choose_zmu_index():
    data = request.json['data']
    session["ZMU_index"] = data
    print("I am here...selected_index_zmu is: ", session["ZMU_index"])

    #### ----- relaod ORIGIN ----> DESTINATION matrix
    crossed_zmu = pd.read_csv(path_app + 'static/crossed_zmu_' + session.sid + '.csv')
    df_gdf_destination_routes = pd.read_csv(
        path_app + 'static/df_gdf_destination_routes_path_zmu_' + session.sid + '.csv')

    crossed_zmu['index_zmu'] = crossed_zmu.index_zmu.astype('int')

    # ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2011.geojson")
    ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")

    selected_index_zmu = session["ZMU_index"]
    selected_index_zmu = int(float(selected_index_zmu))
    print("selected_index_zmu;", selected_index_zmu)
    filtered_crossed_zmu = crossed_zmu[
        crossed_zmu.index_zmu == selected_index_zmu]  ## this will be selected by the user.....flask + web interface.....

    print("length idtrajectory;", len(filtered_crossed_zmu.idtrajectory))

    try:
        highlighted_zmus = []
        for idtrajectory in filtered_crossed_zmu.idtrajectory.tolist():
            ## ---->>> cross trajectory geometry with zmu zones and find intersections -------
            path_trajectory = df_gdf_destination_routes[df_gdf_destination_routes.idtrajectory == idtrajectory]
            path_trajectory = path_trajectory[['zmu', 'geom']]

            ## transform geom into linestring....projection is in meters epsg:6875
            path_trajectory['geom'] = path_trajectory.apply(wkb_tranformation, axis=1)
            path_trajectory = gpd.GeoDataFrame(path_trajectory)
            path_trajectory.rename({'geom': 'geometry'}, axis=1, inplace=True)

            ## reference system = 6875 (in meters)
            path_trajectory = path_trajectory.set_geometry("geometry")
            path_trajectory = path_trajectory.set_crs('epsg:6875', allow_override=True)

            ## convert into lat , lon
            path_trajectory = path_trajectory.to_crs({'init': 'epsg:4326'})
            path_trajectory = path_trajectory.set_crs('epsg:4326', allow_override=True)

            ### find intersected ZMUs
            ZMUs_idtrajectory = gpd.sjoin(ZMU_ROMA[['zmu', 'geometry']], path_trajectory[['geometry']], how='inner',
                                          predicate='intersects')

            # print(idtrajectory)
            list_crossed_zmus = pd.DataFrame({'idtrajectory': [idtrajectory],
                                              'lista_crossed_zmus': [ZMUs_idtrajectory[
                                                                         "zmu"].tolist()]})  ## crossed zmus are not in order of trajectory direction
            highlighted_zmus.append(list_crossed_zmus)
        zmu_paths = pd.concat(highlighted_zmus)

        ### ---- make a dataframe with all the ZMUs interested related to the ZMU chosen by the user
        list_zmu_paths = []
        for i in range(len(zmu_paths)):
            list_zmu_paths.append(pd.DataFrame(zmu_paths.lista_crossed_zmus.iloc[i]))
        df_zmu_paths = pd.concat(list_zmu_paths)
        ## group by same ZMU....
        df_zmu_paths.rename({0: 'zmu_paths'}, axis=1, inplace=True)
        df_zmu_paths.reset_index(inplace=True)
        grouped_zmu_paths = df_zmu_paths.groupby(['zmu_paths']).count().reset_index()
        grouped_zmu_paths.columns = ['zmu', 'counts']
        ### merge with zmu and build a .json file
        grouped_zmu_paths = pd.merge(grouped_zmu_paths, ZMU_ROMA, on=['zmu'], how='left')

        ## save as .geojson file
        try:
            grouped_zmu_paths = gpd.GeoDataFrame(grouped_zmu_paths)
        except IndexError:
            abort(404)

        try:
            import os
            if os.path.exists(path_app + "static/grouped_zmu_paths.geojson"):
                os.remove(path_app + "static/grouped_zmu_paths.geojson")
            else:
                print("The file does not exist")

            grouped_zmu_paths.to_file(filename=path_app + 'static/grouped_zmu_paths_' + session.sid + '.geojson',
                                      driver='GeoJSON')

            grouped_zmu_paths.to_file(filename=path_app + 'static/grouped_zmu_paths.geojson',
                                      driver='GeoJSON')
            ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
            with open(path_app + "static/grouped_zmu_paths.geojson", "r+") as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var grouped_zmu_paths = \n" + old)  # assign the "var name" in the .geojson file
        except ValueError:
            print("empty dataframe.....")
    except ValueError:
        print("No objects to concatenate")

    print("length idtrajectory;", len(filtered_crossed_zmu.idtrajectory))
    print("-------------- I am here...selected_index_zmu is:---------------------- ", session["ZMU_index"])

    return jsonify({'result': session["ZMU_index"]})


#### ---->>> this is to refresh the page....with the FINAL LAYER
@app.route('/redirect_zmu_paths/', methods=['GET', 'POST'])
def redirect_zmu_paths():
    ### open .geojson file in the form of dictionary.....
    grouped_zmu_paths = open(path_app + 'static/grouped_zmu_paths_' + session.sid + '.geojson', )
    grouped_zmu_paths = json.load(grouped_zmu_paths)

    session["grouped_zmu_paths"] = grouped_zmu_paths
    # print("session_grouped_zmu_paths", session["grouped_zmu_paths"])

    return render_template("index_showing_zmu_paths_redirect.html",
                           session_grouped_zmu_paths=session["grouped_zmu_paths"])


@app.route('/layer_ZMU_path/', methods=['GET', 'POST'])
def layer_ZMU_path():
    return render_template("index_showing_zmu_paths.html")


###----///////////// ---------//////////------/////////////-----############
###----///////////// ---------//////////------/////////////-----############
###----///////////// ---------//////////------/////////////-----############
############ ---- TRIP LEGS ---------- #####################################
############################################################################


@app.route('/TRIP_LEGS/', methods=['GET', 'POST'])
def TRIP_LEGS():

    import glob

    session["ZMU_day_start"] = '2022-10-01'
    session["ZMU_day_end"] = '2022-10-15'
    session["ZMU_hour"] = 7
    session["ZMU_hourrange"] = 1
    session['input_data_range'] = "10/12/2022 - 10/13/2022"


    #### ----- check for session ----> data type (FCD, SYNTHETIC)
    stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
    stored_data_type_files.sort(key=os.path.getmtime)
    stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]

    with open(stored_data_type_file) as file:
        selected_data_type = file.read()
    print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
    session["data_type"] = selected_data_type

    return render_template("index_TRIP_LEGS_select_day.html")





### select day (ZMU)...from Database
@app.route('/TRIP_LEGS_day_selector/', methods=['GET', 'POST'])
def TRIP_LEGS_day_selector():
    if request.method == "POST":

        ##### ------ daterangepicker ----- ############################################
        ###############################################################################

        try:
            data = request.form["daterange"]
            session['input_data_range'] = data
            print("-------------data-------------:", data)
        except:
            data = "10/12/2022 - 10/13/2022"

        try:
            start_date = data.split(" - ")[0]
            start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            session["ZMU_day_start"] = str(start_date.date())
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("gotta!!!----->> selected_ZMU_day_start:", session["ZMU_day_start"])  ##--->> only get date
            selected_ZMU_day_start = str(selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            end_date = data.split(" - ")[1]
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            session["ZMU_day_end"] = str(end_date.date())
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("gotta!!!----->> selected_ZMU_day_end:", session["ZMU_day_end"])  ##--->> only get date
            selected_ZMU_day_end = str(selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable selected_ZMU_day_end: ", session["ZMU_day_end"])

        ##########################################################################################################

        return render_template("index_TRIP_LEGS_select_day.html")




### select DATA TYPE  -------- #################################
@app.route('/data_type_selector_LEGS/', methods=['GET', 'POST'])
def data_type_selector_LEGS():

    if request.method == "POST":

        session["data_type"] = request.form.get("data_type")
        selected_data_type = session["data_type"]
        print("selected_data_type:", selected_data_type)
        selected_data_type = str(selected_data_type)

        with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_data_type))

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_data_type = int(selected_data_type)
        if selected_data_type == 11:  ## FCD data
            print("FCD data")
            print("selected_data_type:--------selector", selected_data_type)


        elif selected_data_type == 12:  ## SYNTHETIC DATA
            print("SYNTHETIC DATA")
            print("selected_data_type:--------selector", selected_data_type)


        return render_template("index_TRIP_LEGS_select_day.html")


#####-------------------------------------------------------------##########
### ------  Build LINEE DI DESIDERIO (from ORIGIN to DESTINATION) ---- #####
### --------------------------------------------------------------- ########
@app.route('/TRIP_LEGS_hour_selector/', methods=['GET', 'POST'])
def TRIP_LEGS_hour_selector():
    if request.method == "POST":

        import glob
        import os

        # selected_ZMU_day_start = '2022-10-25'
        # selected_ZMU_day_end =  '2022-10-28'
        # selected_ZMU_hour = 7
        # selected_ZMU_hourrange = 1
        # selected_data_type = 1

        try:
            with open(path_app + "static/params/selected_data_type_" + session.sid + ".txt", "r") as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)
        except:
            # for stored_tod_file in glob.glob(path_app + "static/params/selected_data_type_*.txt"):
            #    print(stored_tod_file)
            stored_data_type_files = glob.glob(path_app + "static/params/selected_data_type_*.txt")
            stored_data_type_files.sort(key=os.path.getmtime)
            stored_data_type_file = stored_data_type_files[len(stored_data_type_files) - 1]
            with open(stored_data_type_file) as file:
                selected_data_type = file.read()
            print("selected_data_type-------I AM HERE-----------: ", selected_data_type)

        session["data_type"] = selected_data_type

        ## TRY if session exists
        try:
            session["ZMU_hourrange"] = request.form.get("ZMU_hourrange")
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
            selected_ZMU_hourrange = str(selected_ZMU_hourrange)
        except:
            session["ZMU_hourrange"] = 2
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])

        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_hourrange = int(selected_ZMU_hourrange)
        if selected_ZMU_hourrange == 0:  ## 00:00 ---> 07:00
            hourrange_id = "N1"
        elif selected_ZMU_hourrange == 1:  ## 07:00 ----> 10:00
            hourrange_id = "M1"
        elif selected_ZMU_hourrange == 2:  ## 10:00 ---> 14:00
            hourrange_id = "M2"
        elif selected_ZMU_hourrange == 3:  ##  14:00 ---> 16:00
            hourrange_id = "A1"
        elif selected_ZMU_hourrange == 4:  ## 16:00 ---> 20:00
            hourrange_id = "A2"
        elif selected_ZMU_hourrange == 5:  ## 20:00 ---> 24:00
            hourrange_id = "A3"

        session["hourrange_id"] = hourrange_id
        print("------hourrange_id------------>>>:", hourrange_id)


        try:
            # selected_ZMU_day_start = session["ZMU_day_start"].strftime('%Y-%m-%d')
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("day from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            # selected_ZMU_day_end = session["ZMU_day_end"].strftime('%Y-%m-%d')
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("day from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA['centroid'] = ZMU_ROMA.apply(wkb_tranformation_centroid, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA)

        ### ---> get filtered data of ZMU from DB  <--- ################################################################
        ################################################################################################################
        ################################################################################################################

        ### ----- find ORIGIN - DESTINATIONS trips ------------- ###################################
        ############################################################################################
        ############ ---------------------------------------------------------- ####################

        selected_data_type = int(selected_data_type)
        if selected_data_type == 11:  ## FCD data ##
            print("--------------------------------------------------------FCD data")

            query_crossed_zmu = text('''SELECT  dt_o, id_zone_o, id_zone_d, id
                                                    FROM fcd.trips
                                                    WHERE date(fcd.trips.dt_o) BETWEEN :x AND :xx 
                                                     AND id_zone_d != id_zone_o
                                                     AND fcd.trips.hour_range_o = :y ''')

        elif selected_data_type == 12:  ## SYNTHETIC data ##
            print("--------------------------------------------------------SYNTHETIC data")

            query_crossed_zmu = text('''SELECT  dt_o, id_zone_o, id_zone_d, id
                                                                FROM carlo.trips_new
                                                                WHERE date(carlo.trips_new.dt_o) BETWEEN :x AND :xx 
                                                                 AND id_zone_d != id_zone_o
                                                                 AND carlo.trips_new.hour_range_o = :y ''')

        stmt = query_crossed_zmu.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                            y=str(hourrange_id))
        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        crossed_zmu = pd.DataFrame(res)

        crossed_zmu = crossed_zmu.sample(frac=0.4)  # 40%;

        crossed_zmu = crossed_zmu[['id_zone_o', 'id_zone_d', 'id']]
        ## renames columns
        crossed_zmu.rename({'id_zone_o': 'zmu_origin'}, axis=1, inplace=True)
        crossed_zmu.rename({'id_zone_d': 'zmu_destination'}, axis=1, inplace=True)
        crossed_zmu.rename({'id': 'idtrajectory'}, axis=1, inplace=True)

        ######################################################################################################
        ######################################################################################################

        ##----> group by ORIGIN --> DESTINATION pairs to find the "LINEE di DESIDERIO"
        grouped_trajectories = crossed_zmu.groupby(['zmu_origin', 'zmu_destination']).count().reset_index()
        grouped_trajectories_ORIGIN = crossed_zmu.groupby(['zmu_origin']).count().reset_index()
        grouped_trajectories_DESTINATION = crossed_zmu.groupby(['zmu_destination']).count().reset_index()
        grouped_trajectories_ORIGIN.rename({'idtrajectory': 'count_origin'}, axis=1, inplace=True)
        grouped_trajectories_DESTINATION.rename({'idtrajectory': 'count_destination'}, axis=1, inplace=True)

        grouped_trajectories.rename({'idtrajectory': 'count_journeys'}, axis=1, inplace=True)
        # max(grouped_trajectories.count_journeys)

        grouped_trajectories = pd.merge(grouped_trajectories,
                                        grouped_trajectories_ORIGIN[['zmu_origin', 'count_origin']],
                                        left_on='zmu_origin', right_on='zmu_origin', how='left')

        grouped_trajectories = pd.merge(grouped_trajectories,
                                        grouped_trajectories_DESTINATION[['zmu_destination', 'count_destination']],
                                        left_on='zmu_destination', right_on='zmu_destination', how='left')

        ##----> find CENTROID of each ZMU zone (ORIGIN and DESTINATION)
        ## get geomeries of each ZMU zone (ORIGIN and DESTINATION)
        grouped_trajectories_ORIGIN = pd.merge(grouped_trajectories,
                                               ZMU_ROMA[['zmu', 'POP_TOT_ZMU', 'geometry', 'centroid']],
                                               left_on='zmu_origin', right_on='zmu', how='left')
        grouped_trajectories_DESTINATION = pd.merge(grouped_trajectories,
                                                    ZMU_ROMA[['zmu', 'POP_TOT_ZMU', 'geometry', 'centroid']],
                                                    left_on='zmu_destination', right_on='zmu', how='left')

        ##.... get CENTROIDS of each geometry
        grouped_trajectories_ORIGIN = gpd.GeoDataFrame(grouped_trajectories_ORIGIN)
        grouped_trajectories_DESTINATION = gpd.GeoDataFrame(grouped_trajectories_DESTINATION)

        ## !!!!!!! -------------- add "centroids" to each ZMU ------ too long run!!!!!! ........

        grouped_trajectories = pd.merge(grouped_trajectories,
                                        grouped_trajectories_ORIGIN[['zmu_origin', 'zmu_destination', 'centroid']],
                                        how='left')
        grouped_trajectories.rename({'centroid': 'centroid_ORIGIN'}, axis=1, inplace=True)

        grouped_trajectories = pd.merge(grouped_trajectories,
                                        grouped_trajectories_DESTINATION[['zmu_origin', 'zmu_destination', 'centroid']],
                                        how='left')
        grouped_trajectories.rename({'centroid': 'centroid_DESTINATION'}, axis=1, inplace=True)

        ## remove none values
        grouped_trajectories_ORIGIN = grouped_trajectories_ORIGIN[grouped_trajectories_ORIGIN['centroid'].notna()]
        grouped_trajectories_DESTINATION = grouped_trajectories_DESTINATION[
            grouped_trajectories_DESTINATION['centroid'].notna()]

        ### create a simple line from each origin and destination
        grouped_trajectories['ORIGIN'] = grouped_trajectories_ORIGIN.apply(lambda x: [y for y in x['centroid'].coords],
                                                                           axis=1)
        grouped_trajectories['DESTINATION'] = grouped_trajectories_DESTINATION.apply(
            lambda x: [y for y in x['centroid'].coords], axis=1)

        grouped_trajectories = pd.merge(grouped_trajectories,
                                        grouped_trajectories_ORIGIN[['zmu_origin', 'zmu_destination']],
                                        how='left')

        grouped_trajectories = pd.merge(grouped_trajectories,
                                        grouped_trajectories_DESTINATION[['zmu_origin', 'zmu_destination']],
                                        how='left')

        grouped_trajectories['weight'] = (grouped_trajectories['count_origin'])
        grouped_trajectories.replace([np.inf, -np.inf], np.nan, inplace=True)
        grouped_trajectories.dropna(inplace=True)

        ## make a list from ORIGIN to DESTINATION
        grouped_trajectories['tup'] = grouped_trajectories.apply(lambda x: list(zip(x.ORIGIN, x.DESTINATION)), axis=1)

        if selected_data_type == 11:  ## FCD data ##
            a = 1.7  ## general parameter for rescaling
            color_OD = 'blue'
            grouped_trajectories = grouped_trajectories[grouped_trajectories.count_journeys > 1]
            grouped_trajectories = grouped_trajectories.sample(frac=0.4)  # 40%;
            grouped_trajectories.count_journeys = round(grouped_trajectories.count_journeys, ndigits=0)
            print("-------->>>>>>>>>>>>>>length grouped trajectories:---------------------------",
                  len(grouped_trajectories))


        elif selected_data_type == 12:  ## SYNTHETIC data ##
            a = 1  ## general parameter for rescaling
            color_OD = 'blue'

            grouped_trajectories = grouped_trajectories[grouped_trajectories.count_journeys > 2]
            grouped_trajectories = grouped_trajectories.sample(frac=0.4)  # 40%;
            grouped_trajectories.count_journeys = round(grouped_trajectories.count_journeys, ndigits=0)
            print("-------->>>>>>>>>>>>>>length grouped trajectories:---------------------------",
                  len(grouped_trajectories))

        lista_TRIP_LEGS = []
        ##----> MAKE a dictionary...of points of polyline
        for i in range(len(grouped_trajectories)):
            trip_LEG = grouped_trajectories['tup'].iloc[i]
            ## unlist the nested list...
            trip_LEG = [item for sublist in trip_LEG for item in sublist]

            ## compute the tickenss fof the line (weight)
            OD_weight = (grouped_trajectories['count_journeys'].iloc[i]) / a

            ### ----> possible color list....
            color_OD = 'blue'
            if math.isnan(OD_weight):
                OD_weight = 1 / a  ## this is the default weight of the polyline
            elif ((OD_weight <= 3 / a) and (OD_weight > (1 / a))):
                color_OD = 'purple'
            elif ((OD_weight <= 5 / a) and (OD_weight > 3 / a)):
                color_OD = 'blue'
            elif ((OD_weight <= 8 / a) and (OD_weight > 5 / a)):
                color_OD = 'red'
            elif ((OD_weight <= 15 / a) and (OD_weight > 8 / a)):
                color_OD = 'orange'
            elif ((OD_weight > 15 / a)):
                OD_weight = OD_weight / 2
                color_OD = 'yellow'

            lista = []
            keys_coords = list(range(len(trip_LEG)))
            dict_lat = {}
            dict_lon = {}
            for u in keys_coords:
                dict_lat["lat"] = trip_LEG[u][1]
                dict_lon["lon"] = trip_LEG[u][0]
                # join two dictionaries
                element = {**dict_lat, **dict_lon}
                # print(element)
                lista.append(element)
            lista = (json.dumps(lista))
            # OD_weight = 20/a
            lista_trip_LEG = str(
                "L.motion.polyline(JSON.parse(\'" + lista + "\'" + "),  {color:\'" + color_OD + "\' , weight:" + str(
                    OD_weight) + "},  {easing: L.Motion.Ease.easeInOutQuad}, {removeOnEnd: true, icon: L.divIcon({html: " + "\"<i class='fa fa-car fa-2x fa-flip-horizontal' aria-hidden='true'></i>\"" + ", iconSize: L.point(26.5, 23)})" + "}).motionDuration(50)")
            lista_LEGS = pd.DataFrame({'motion_lines': [lista_trip_LEG]})
            lista_TRIP_LEGS.append(lista_LEGS)

        ## save data
        try:
            ##--->> save data
            lista_TRIP_LEGS_all = pd.concat(lista_TRIP_LEGS)
            import os
            if os.path.exists(path_app + "static/lista_TRIP_LEGS.txt"):
                os.remove(path_app + "static/lista_TRIP_LEGS.txt")
            else:
                print("The file does not exist")
            with open(path_app + "static/lista_TRIP_LEGS" + ".txt", "w") as file:
                for i in range(len(lista_TRIP_LEGS_all)):
                    motion_route = (lista_TRIP_LEGS_all[['motion_lines']].iloc[i])[0]
                    if i < len(lista_TRIP_LEGS_all) - 1:
                        file.write(str(motion_route) + ",\n")
                    else:
                        file.write(str(motion_route))
            ## add "var name" in front of the .txt file, in order to properly load it into the index.html file
            with open(path_app + "static/lista_TRIP_LEGS" + ".txt", "r+") as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write(
                    "var motion_TRIP_LEGS =[ \n" + old + "]")  # assign the "var name" in the .geojson file

        except ValueError:
            print("empty dataframe.....")

        # res_TRIP_LEGS = json.dumps(motion_route)
        lista_TRIP_LEGS = []
        for i in range(len(lista_TRIP_LEGS_all)):
            motion_route = (lista_TRIP_LEGS_all[['motion_lines']].iloc[i])[0]
            if i < len(lista_TRIP_LEGS_all) - 1:
                lista_TRIP_LEGS.append(motion_route)
            else:
                lista_TRIP_LEGS.append(motion_route)

        # lista_TRIP_LEGS = ','.join(lista_TRIP_LEGS)

        session["TRIP_LEGS"] = ','.join(lista_TRIP_LEGS)
        # print(session["TRIP_LEGS"])

        return render_template("index_TRIP_LEGS_select_hour.html",
                               session_TRIP_LEGS=session["TRIP_LEGS"])  # session_counts_OD=session["counts_OD"]


########## -------------------------------- ###################################
########## -------------------------------- ###################################
########## -------------------------------- ###################################
### ----> make TRIP DATA AGGREGATION over an AGGREGATION of ZMU zones ----- ###

@app.route('/AGGREGATED_ZMU_border_selector/', methods=['GET', 'POST'])
def AGGREGATERD_ZMU_border_selector():

    import glob

    if request.method == "POST":

        ### ---- >> delete previous 'BORDER_selected_ZMUs'
        session.pop('BORDER_selected_ZMUs', default=None)

        try:
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("hour from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("hour from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])

        try:
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
        except:
            selected_ZMU_hourrange = 2
            session["ZMU_hourrange"] = selected_ZMU_hourrange
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])

        try:
            selected_data_type = session["data_type"]
            selected_data_type = int(selected_data_type)
            print("selected_data_type:", selected_data_type)
        except:
            selected_data_type = 11
            session["data_type"] = selected_data_type
            print("selected_data_type: ", session["data_type"])

        try:
            selected_hourrange = session["hourrange_id"]
            selected_hourrange = str(selected_hourrange)
            print("selected_hourrange:", selected_hourrange)
        except:
            selected_hourrange = "A3"
            session["hourrange_id"] = selected_hourrange
            print("selected_hourrange: ", session["hourrange_id"])

        try:
            selected_tod = session["tod"]
            print("selected_tod:", selected_tod)
        except:
            selected_tod = "W"
            session["tod"] = selected_tod
            print("selected_tod: ", session["tod"])

        ##----->> compute route paramenters aggregation over the selected ZMUs
        try:
            with open(path_app + 'static/BORDER_selected_ZMUs_aggr_' + session.sid + '.geojson', "r") as file:
                BORDER_ZMUS = gpd.read_file.read()
        except:
            for stored_border_file in glob.glob(path_app + "static/BORDER_selected_ZMUs_aggr_*.geojson"):
                print(stored_border_file)
            with open(stored_border_file) as file:
                BORDER_ZMUS = gpd.read_file(file)


        try:
            with open(path_app + 'static/BORDER_selected_ZMUs_aggr_' + session.sid + '.geojson', "r") as file:
                custom_border = json.load(file)
        except:
            for stored_border_file in glob.glob(path_app + "static/BORDER_selected_ZMUs_aggr_*.geojson"):
                print(stored_border_file)
            with open(stored_border_file) as file:
                custom_border = json.load(file)


        session['BORDER_selected_ZMUs'] = custom_border
        # print("------BORDER----------------------", session['BORDER_selected_ZMUs'])

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        ###########################################################################
        #######--------------------------------------------- ######################
        ###--->>> get aggregation by DAY (keep hours disaggregated <<------########

        query_destination_day = text('''SELECT 
                                        p_before, tt, dt_d, id, dist, id_zone_o, id_zone_d,
                                        date_part('hour', dt_o) as hr, geom,
                                        TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                        FROM fcd.trips
                                        WHERE date(dt_o) BETWEEN :x AND :xx 
                                        AND tod_o = :z ''')
        stmt = query_destination_day.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                                         z=str(selected_tod))
        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        destination_routes_day = pd.DataFrame(res)

        ### ----- DESTINATIONS ---------------------------------- ##################################################
        ## transform the "destinations" table into a geodataframe

        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        destination_routes_day['geom'] = destination_routes_day.apply(wkb_tranformation, axis=1)
        destination_routes_day = gpd.GeoDataFrame(destination_routes_day)
        destination_routes_day.rename({'geom': 'geometry'}, axis=1, inplace=True)

        ## reference system = 6875 (in meters)
        destination_routes_day = destination_routes_day.set_geometry("geometry")
        destination_routes_day = destination_routes_day.set_crs('epsg:6875', allow_override=True)

        ## convert into lat , lon
        destination_routes_day = destination_routes_day.to_crs({'init': 'epsg:4326'})
        destination_routes_day = destination_routes_day.set_crs('epsg:4326', allow_override=True)

        destination_routes_day = destination_routes_day.sample(frac=0.2)  # 50%
        ## get the last coordinate point....LONG RUN.....
        dest_lats = []
        dest_lons = []
        for i in range(len(destination_routes_day)):
            row = destination_routes_day.geometry.iloc[i]
            x, y = row.coords.xy
            lats_longs = pd.DataFrame(list(zip(x, y)), columns=['longitude', 'latitude'])
            destination_longitude = lats_longs.iloc[len(lats_longs) - 1][0]
            destination_latitude = lats_longs.iloc[len(lats_longs) - 1][1]
            dest_lons.append(destination_longitude)
            dest_lats.append(destination_latitude)

        destination_routes_day = destination_routes_day[['p_before', 'tt', 'dt_d', 'id', 'dist', 'hr', 'day']]
        destination_routes_day['longitude'] = dest_lons
        destination_routes_day['latitude'] = dest_lats

        destination_routes_day.rename({'tt': 'triptime_s'}, axis=1, inplace=True)
        destination_routes_day.rename({'p_before': 'breaktime_s'}, axis=1, inplace=True)
        destination_routes_day.rename({'id': 'idtrajectory'}, axis=1, inplace=True)
        destination_routes_day.rename({'dist': 'tripdistance_m'}, axis=1, inplace=True)

        geometry_d = [Point(xy) for xy in zip(destination_routes_day.longitude, destination_routes_day.latitude)]
        geo_destination_routes_day = GeoDataFrame(destination_routes_day, geometry=geometry_d,
                                                  crs="EPSG:4326")

        # get ZMU containing the DESTINATION locations (gdf_tdf)
        BORDER_destination_routes = gpd.sjoin(BORDER_ZMUS, geo_destination_routes_day, how='right',
                                              predicate='contains')  ### <---- OK
        BORDER_destination_routes = pd.DataFrame(BORDER_destination_routes)
        ## only get trips ending within the BORDER_ZMUs that is index_left == 0)
        BORDER_destination_routes = BORDER_destination_routes[BORDER_destination_routes.index_left == 0]

        ## ---->> grouby + counts....only if you want to estimate the NUMBER of vehicles
        aggregated_BORDER_destinations_day = BORDER_destination_routes[['hr']].groupby(['hr'],
                                                                                       sort=False).size().reset_index().rename(
            columns={0: 'counts'})

        # aggregated_BORDER_destinations_day['day'] = selected_ZMU_day

        BORDER_destination_routes = BORDER_destination_routes[BORDER_destination_routes['triptime_s'] > 0]
        BORDER_destination_routes = BORDER_destination_routes[BORDER_destination_routes['breaktime_s'] > 0]
        BORDER_destination_routes = BORDER_destination_routes[
            BORDER_destination_routes['tripdistance_m'] > 0]

        #### ------->>>> groupby + mean triptime, tripdistance, breaktime <<<-----------###########################################
        aggregated_means_BORDER_destination = BORDER_destination_routes[
            ['hr', 'triptime_s', 'breaktime_s', 'tripdistance_m']].groupby(['hr'],
                                                                           sort=False).mean().reset_index().rename(
            columns={0: 'means'})

        # aggregated_means_BORDER_destination['day'] = selected_ZMU_day
        ## convert triptime_s into minutes
        aggregated_means_BORDER_destination['triptime_m'] = (aggregated_means_BORDER_destination['triptime_s']) / 60
        aggregated_means_BORDER_destination = aggregated_means_BORDER_destination[
            aggregated_means_BORDER_destination['triptime_s'].notna()]
        aggregated_means_BORDER_destination['triptime_m'] = aggregated_means_BORDER_destination.triptime_m.astype('int')
        ## convert breaktime_s into minutes
        aggregated_means_BORDER_destination['breaktime_m'] = (aggregated_means_BORDER_destination['breaktime_s']) / 60
        aggregated_means_BORDER_destination = aggregated_means_BORDER_destination[
            aggregated_means_BORDER_destination['breaktime_m'].notna()]
        aggregated_means_BORDER_destination['breaktime_m'] = aggregated_means_BORDER_destination.breaktime_m.astype(
            'int')
        ## convert tripdistance_m
        aggregated_means_BORDER_destination = aggregated_means_BORDER_destination[
            aggregated_means_BORDER_destination['tripdistance_m'].notna()]
        aggregated_means_BORDER_destination[
            'tripdistance_m'] = aggregated_means_BORDER_destination.tripdistance_m.astype('int')

        aggregated_means_BORDER_destination = aggregated_means_BORDER_destination[
            ['hr', 'tripdistance_m', 'triptime_m', 'breaktime_m']]


        ### -----> merge all data together ---- ###################################################################
        aggregated_means_BORDER_destination = pd.merge(aggregated_means_BORDER_destination,
                                                       aggregated_BORDER_destinations_day, on=['hr'], how='left')
        #####----->>> save csv file ---- ##################################################
        aggregated_means_BORDER_destination.to_csv(
            path_app + 'static/aggregated_counts_and_means_BORDER_destination_' + session.sid + '.csv')

        return render_template("index_aggregated_zmu_select_day.html",
                               BORDER_selected_ZMUs=session['BORDER_selected_ZMUs'])


from flask import send_file

@app.route('/download_aggregated_destinations/',methods=["GET"])
def download_aggregated_destinations():
    return send_file(
        'static/aggregated_counts_and_means_BORDER_destination_' + session.sid + '.csv',
        mimetype='text/csv',
        download_name='aggregated_destinations_file.csv',
        as_attachment=True
    )

@app.route('/process_zmu_index', methods=['POST'])
def process_zmu_index():
    data = request.json['data']
    selected_index_zmu = data
    print("I am here...result is: ", selected_index_zmu)
    print("session user ID:", session.sid)
    data = jsonify({'result': selected_index_zmu})
    data_zmu = data.get_data(as_text=True)
    ## save zmu result into txt file
    text_file = open(path_app + "static/params/index_zmu_" + session.sid + ".txt", "wt")
    n = text_file.write(data_zmu)
    text_file.close()
    print(data_zmu)
    return jsonify({'result': selected_index_zmu})


##--->> timeseries NUMBER OF VEHICLES ------ ##############
@app.route('/figure1')
def figure_plotly1():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_zmu_origin_by_day = pd.read_csv(
        path_app + 'static/aggregated_zmu_origin_day_' + session.sid + '.csv')
    # aggregated_zmu_destinations_by_day = pd.read_csv(path_app + 'static/aggregated_zmu_destinations_day_2d4cf911-664d-43b7-8078-6a222d4a6917.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_zmu_origin_by_day[(aggregated_zmu_origin_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hr', 'counts_norm', 'index_zmu', 'tripdistance_m',
                                 'triptime_m', 'breaktime_m']]
    filtered_ZMU.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    filtered_ZMU['triptime_m'] = ((filtered_ZMU.triptime_m) * (filtered_ZMU.counts_norm)) / max(filtered_ZMU.counts_norm)
    filtered_ZMU['tripdistance_m'] = (filtered_ZMU.tripdistance_m * filtered_ZMU.counts_norm) / max(filtered_ZMU.counts_norm)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="counts_norm", labels={
        "counts": "Num.Trips"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_counts/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_counts/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_counts/hourly_' + str(x) + '_zmu.html')


##--->> timeseries TRIPDISTANCE ------ ##############
@app.route('/figure2')
def figure_plotly2():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_zmu_origin_by_day = pd.read_csv(
        path_app + 'static/aggregated_zmu_origin_day_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    ## string split and get value....
    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_zmu_origin_by_day[
        (aggregated_zmu_origin_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hr', 'counts_norm', 'index_zmu', 'tripdistance_m',
                                 'triptime_m', 'breaktime_m']]
    filtered_ZMU.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    filtered_ZMU['triptime_m'] = ((filtered_ZMU.triptime_m) * (filtered_ZMU.counts_norm)) / max(filtered_ZMU.counts_norm)
    filtered_ZMU['tripdistance_m'] = (filtered_ZMU.tripdistance_m * filtered_ZMU.counts_norm) / max(filtered_ZMU.counts_norm)
    # filtered_ZMU['breaktime_m'] = (filtered_ZMU.breaktime_m * filtered_ZMU.counts) / max(filtered_ZMU.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> mean TRIPDISTANCE (meters) at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="tripdistance_m", labels={
        "tripdistance_m": "trip dist. (meters)"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_tripdistance/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_tripdistance/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_tripdistance/hourly_' + str(x) + '_zmu.html')


##--->> timeseries TRIPTIME ------ ##############
@app.route('/figure3')
def figure_plotly3():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_zmu_origin_by_day = pd.read_csv(
        path_app + 'static/aggregated_zmu_origin_day_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    ## string split and get value....
    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))
    print("I am here....in plotly....")
    # filtered_ZMU = aggregated_zmu_destinations_by_day[(aggregated_zmu_destinations_by_day.day == selected_ZMU_day) & (aggregated_zmu_destinations_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = aggregated_zmu_origin_by_day[
        (aggregated_zmu_origin_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hr', 'counts_norm', 'index_zmu', 'tripdistance_m',
                                 'triptime_m', 'breaktime_m']]
    filtered_ZMU.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    filtered_ZMU['triptime_m'] = ((filtered_ZMU.triptime_m) * (filtered_ZMU.counts_norm)) / max(filtered_ZMU.counts_norm)
    filtered_ZMU['tripdistance_m'] = (filtered_ZMU.tripdistance_m * filtered_ZMU.counts_norm) / max(filtered_ZMU.counts_norm)
    # filtered_ZMU['breaktime_m'] = (filtered_ZMU.breaktime_m * filtered_ZMU.counts) / max(filtered_ZMU.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> mean TRIPTIME (minutes) at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="triptime_m", labels={
        "triptime_m": "trip time (min.)"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_triptime/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_triptime/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_triptime/hourly_' + str(x) + '_zmu.html')


##--->> timeseries STOPTIME ------ ##############
@app.route('/figure4')
def figure_plotly4():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_zmu_origin_by_day = pd.read_csv(
        path_app + 'static/aggregated_zmu_origin_day_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    ## string split and get value....
    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))
    print("I am here....in plotly....")

    filtered_ZMU = aggregated_zmu_origin_by_day[
        (aggregated_zmu_origin_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hr', 'counts_norm', 'index_zmu', 'tripdistance_m',
                                 'triptime_m', 'breaktime_m']]
    filtered_ZMU.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    filtered_ZMU['triptime_m'] = ((filtered_ZMU.triptime_m) * (filtered_ZMU.counts_norm)) / max(filtered_ZMU.counts_norm)
    filtered_ZMU['tripdistance_m'] = (filtered_ZMU.tripdistance_m * filtered_ZMU.counts_norm) / max(filtered_ZMU.counts_norm)
    # filtered_ZMU['breaktime_m'] = (filtered_ZMU.breaktime_m * filtered_ZMU.counts) / max(filtered_ZMU.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> mean TRIPTIME (minutes) at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="breaktime_m", labels={
        "breaktime_m": "stop time (min.)"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_stoptime/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_stoptime/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_stoptime/hourly_' + str(x) + '_zmu.html')


##--->> POLAR CHART for trip counts, triptime, breaktime and trip distance ------ ##############
@app.route('/polar_FCD')
def figure_polar_FCD():
    import plotly.express as px
    import pandas as pd
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    csv_aggregated_zmu_origin = pd.read_csv(
        path_app + 'static/csv_aggregated_zmu_origin_' + session.sid + '.csv')
    csv_aggregated_zmu_origin.rename({'index_zmu_origin': 'index_zmu'}, axis=1, inplace=True)

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    ## string split and get value....
    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    #### make POLAR chart for SCORES about trip counts, triptime, breaktime, and tripdistance.

    aggregated_zmu_origin_selected = csv_aggregated_zmu_origin[['score_trip_counts', 'score_trip_time',
                                                                            'score_breaktime', 'score_trip_distance',
                                                                            'mark_trip_counts', 'mark_trip_time',
                                                                            'mark_breaktime', 'mark_trip_distance']][csv_aggregated_zmu_origin.index_zmu == selected_index_zmu]

    aggregated_zmu_origin_selected.reset_index(inplace=True)
    df = pd.DataFrame({'category': ['Number of Trips', 'Trip time', 'Break time', 'Trip Distance'],
                       'value': list(aggregated_zmu_origin_selected[['score_trip_counts', 'score_trip_time',
                                                                           'score_breaktime',
                                                                           'score_trip_distance']].iloc[0]),
                       'mark': list(aggregated_zmu_origin_selected[['mark_trip_counts', 'mark_trip_time',
                                                                          'mark_breaktime', 'mark_trip_distance']].iloc[0])})
    # Correct order of categoricals...
    cat = ['Low', 'Average', 'Important', 'Relevant']
    # output radial as an ordered number
    df2 = df.assign(mark=pd.Categorical(df["mark"], ordered=True, categories=cat).codes).sort_values(
        by='category')
    fig = px.line_polar(df2, theta='category', r='mark', color_discrete_sequence=['red'],
                        line_dash_sequence=['dash']).update_traces(fill='toself')

    # change axis back to text
    fig.update_layout(
        polar={"radialaxis": {"tickmode": "array", "tickvals": [i for i in range(len(cat))], "ticktext": cat}})

    fig.update_layout(
        font=dict(
            family="Arial Bold",
            size=20,  # Set the font size here
            color="Black"  # "RebeccaPurple"
        )
    )

    fig.update_xaxes(title_font_family="Arial")
    fig.update_xaxes(tickangle=90)
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_polar_fcd/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_polar_fcd/scores_zone_' + str(x) + '_zmu.html')
    return render_template('plotly_polar_fcd/scores_zone_' + str(x) + '_zmu.html')


################################################################################################
############## ---------------------------------- ##############################################
############ Aggregated data for ORIGIN ---> DESTINATION hourly profile for TPL ------ #########


##--->> timeseries NUMBER OF VEHICLES ------ ##############
@app.route('/figure5')
def figure_plotly5():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_origin_OD_hourly_profile = pd.read_csv(
        path_app + 'static/origin_OD_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_origin_OD_hourly_profile[(aggregated_origin_OD_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['ora', 'sum', 'index_zmu']]
    filtered_ZMU.sort_values('ora', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'ora': 'hr'}, axis=1, inplace=True)
    filtered_ZMU.rename({'sum': 'number_of_visits'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="number_of_visits", labels={
        "number_of_visits": "Num.of Visits"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_visits_tpl/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_visits_tpl/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_visits_tpl/hourly_' + str(x) + '_zmu.html')



###############################################################################################################
############## ---------------------------------- #############################################################
############ Aggregated data for EMISSIONS and  Energy Consumption @ ORIGIN hourly profile ---------- #########

##--->> timeseries EC ------ ##############
@app.route('/figure6')
def figure_plotly6():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'ec', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)


    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="ec", labels={
        "ec": "Energy Cons. [MJ]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_ec/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_ec/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_ec/hourly_' + str(x) + '_zmu.html')




##--->> timeseries EC well-to-tank ------ ##############
@app.route('/figure7')
def figure_plotly7():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    # filtered_ZMU = aggregated_zmu_destinations_by_day[(aggregated_zmu_destinations_by_day.day == selected_ZMU_day) & (aggregated_zmu_destinations_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'ec_wtt', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="ec_wtt", labels={
        "ec_wtt": "Energy Cons. Wtt [MJ]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_ec_wtt/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_ec_wtt/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_ec_wtt/hourly_' + str(x) + '_zmu.html')




##--->> timeseries NOx ------ ####################################################
@app.route('/figure8')
def figure_plotly8():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    # filtered_ZMU = aggregated_zmu_destinations_by_day[(aggregated_zmu_destinations_by_day.day == selected_ZMU_day) & (aggregated_zmu_destinations_by_day.index_zmu == selected_index_zmu)]
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'nox', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="nox", labels={
        "nox": "NOx [grams]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_nox/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_nox/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_nox/hourly_' + str(x) + '_zmu.html')







##--->> timeseries nmvoc ------ ####################################################
@app.route('/figure9')
def figure_plotly9():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'nmvoc', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="nmvoc", labels={
        "nmvoc": "NMVOCs [grams]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_nmvoc/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_nmvoc/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_nmvoc/hourly_' + str(x) + '_zmu.html')



##--->> timeseries PM ------ ####################################################
@app.route('/figure10')
def figure_plotly10():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'pm', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="pm", labels={
        "pm": "PM [grams]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_pm/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_pm/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_pm/hourly_' + str(x) + '_zmu.html')






##--->> timeseries PM Tyres & Brakes ------ ####################################################
@app.route('/figure11')
def figure_plotly11():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'pm_nexh', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="pm_nexh", labels={
        "pm_nexh": "PM (tyres & brakes) [grams]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_pm_nexh/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_pm_nexh/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_pm_nexh/hourly_' + str(x) + '_zmu.html')





##--->> timeseries CO2 eq ------ ####################################################
@app.route('/figure12')
def figure_plotly12():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    print("I am here....in plotly....")
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'co2eq', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="co2eq", labels={
        "co2eq": "CO2 eq. [grams]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_co2eq/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_co2eq/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_co2eq/hourly_' + str(x) + '_zmu.html')




##--->> timeseries CO2 eq wtt ------ ####################################################
@app.route('/figure13')
def figure_plotly13():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_emission_consumption_hourly_profile = pd.read_csv(
        path_app + 'static/aggregated_emission_origin_zones_hourly_profile_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))
    print("I am here....in plotly....")
    filtered_ZMU = aggregated_emission_consumption_hourly_profile[(aggregated_emission_consumption_hourly_profile.index_zmu == selected_index_zmu)]
    filtered_ZMU = filtered_ZMU[['hour', 'co2eq_wtt', 'index_zmu']]
    filtered_ZMU.sort_values('hour', ascending=True, inplace=True)
    ## rename
    filtered_ZMU.rename({'hour': 'hr'}, axis=1, inplace=True)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(filtered_ZMU, x='hr', y="co2eq_wtt", labels={
        "co2eq_wtt": "CO2eq wtt [grams]"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_plots_co2eq_wtt/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_plots_co2eq_wtt/hourly_' + str(x) + '_zmu.html')
    return render_template('plotly_plots_co2eq_wtt/hourly_' + str(x) + '_zmu.html')



###################################################################################################################################################################
###################################################################################################################################################################
###################################################################################################################################################################
###################################################################################################################################################################
###################################################################################################################################################################
###################################################################################################################################################################

#####################################################################################
### ----- AGGREGATED STATISTICS within ZMUs selected BORDER -------- ################


##--->> timeseries NUMBER OF VEHICLES ------ ##############
@app.route('/figure1_BORDER')
def figure_BORDER_plotly1():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data within BORDER from csv file  <--- ###########################
    aggregated_BORDER_destinations_by_day = pd.read_csv(
        path_app + 'static/aggregated_counts_and_means_BORDER_destination_' + session.sid + '.csv')

    ##----> filter by day

    print("I am here....in plotly....")

    aggregated_BORDER_destinations_by_day.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    aggregated_BORDER_destinations_by_day['triptime_m'] = ((aggregated_BORDER_destinations_by_day.triptime_m) * (aggregated_BORDER_destinations_by_day.counts)) / max(
        aggregated_BORDER_destinations_by_day.counts)
    aggregated_BORDER_destinations_by_day['tripdistance_m'] = (aggregated_BORDER_destinations_by_day.tripdistance_m * aggregated_BORDER_destinations_by_day.counts) / max(
        aggregated_BORDER_destinations_by_day.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> number of Vehicles at destination-----#############################
    fig = px.line(aggregated_BORDER_destinations_by_day, x='hr', y="counts", labels={
        "counts": "Num.Trips"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_BORDER_counts/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_BORDER_counts/hourly_BORDER_' + str(x) + '.html')
    return render_template('plotly_BORDER_counts/hourly_BORDER_' + str(x) + '.html')


##--->> timeseries TRIPDISTANCE ------ ##############
@app.route('/figure2_BORDER')
def figure_BORDER_plotly2():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_BORDER_destinations_by_day = pd.read_csv(
        path_app + 'static/aggregated_counts_and_means_BORDER_destination_' + session.sid + '.csv')

    aggregated_BORDER_destinations_by_day.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    aggregated_BORDER_destinations_by_day['triptime_m'] = ((aggregated_BORDER_destinations_by_day.triptime_m) * (aggregated_BORDER_destinations_by_day.counts)) / max(
        aggregated_BORDER_destinations_by_day.counts)
    aggregated_BORDER_destinations_by_day['tripdistance_m'] = (aggregated_BORDER_destinations_by_day.tripdistance_m * aggregated_BORDER_destinations_by_day.counts) / max(
        aggregated_BORDER_destinations_by_day.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> mean TRIPDISTANCE (meters) at destination-----#############################
    fig = px.line(aggregated_BORDER_destinations_by_day, x='hr', y="tripdistance_m", labels={
        "tripdistance_m": "trip dist. (meters)"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_BORDER_tripdistance/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_BORDER_tripdistance/hourly_BORDER_' + str(x) + '.html')
    return render_template('plotly_BORDER_tripdistance/hourly_BORDER_' + str(x) + '.html')


##--->> timeseries TRIPTIME ------ ##############
@app.route('/figure3_BORDER')
def figure_BORDER_plotly3():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_BORDER_destinations_by_day = pd.read_csv(
        path_app + 'static/aggregated_counts_and_means_BORDER_destination_' + session.sid + '.csv')


    aggregated_BORDER_destinations_by_day.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    aggregated_BORDER_destinations_by_day['triptime_m'] = ((aggregated_BORDER_destinations_by_day.triptime_m) * (aggregated_BORDER_destinations_by_day.counts)) / max(
        aggregated_BORDER_destinations_by_day.counts)
    aggregated_BORDER_destinations_by_day['tripdistance_m'] = (aggregated_BORDER_destinations_by_day.tripdistance_m * aggregated_BORDER_destinations_by_day.counts) / max(
        aggregated_BORDER_destinations_by_day.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> mean TRIPTIME (minutes) at destination-----#############################
    fig = px.line(aggregated_BORDER_destinations_by_day, x='hr', y="triptime_m", labels={
        "triptime_m": "trip time (min.)"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_BORDER_triptime/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_BORDER_triptime/hourly_BORDER_' + str(x) + '.html')
    return render_template('plotly_BORDER_triptime/hourly_BORDER_' + str(x) + '.html')


##--->> timeseries STOPTIME ------ ##############
@app.route('/figure4_BORDER')
def figure_BORDER_plotly4():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################

    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    aggregated_BORDER_destinations_by_day = pd.read_csv(
        path_app + 'static/aggregated_counts_and_means_BORDER_destination_' + session.sid + '.csv')


    aggregated_BORDER_destinations_by_day.sort_values('hr', ascending=True, inplace=True)

    ####---->>> normalize data
    aggregated_BORDER_destinations_by_day['triptime_m'] = ((aggregated_BORDER_destinations_by_day.triptime_m) * (aggregated_BORDER_destinations_by_day.counts)) / max(
        aggregated_BORDER_destinations_by_day.counts)
    aggregated_BORDER_destinations_by_day['tripdistance_m'] = (aggregated_BORDER_destinations_by_day.tripdistance_m * aggregated_BORDER_destinations_by_day.counts) / max(
        aggregated_BORDER_destinations_by_day.counts)

    ## plot houlry profile with plotly and make an. html file
    ##----->>> mean TRIPTIME (minutes) at destination-----#############################
    fig = px.line(aggregated_BORDER_destinations_by_day, x='hr', y="breaktime_m", labels={
        "breaktime_m": "stop time (min.)"})
    ##----> delete files within the folder "/templates/plotly_plots..."
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_BORDER_stoptime/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_BORDER_stoptime/hourly_BORDER_' + str(x) + '.html')
    return render_template('plotly_BORDER_stoptime/hourly_BORDER_' + str(x) + '.html')


####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################
###########---- FCD data --------------------#######################################
####################################################################################


## function to transform Geometry from text to LINESTRING
def wkb_tranformation(line):
    return wkb.loads(line.geom, hex=True)


## use to reverse lat lon position
def reverseTuple(lstOfTuple):
    return [tup[::-1] for tup in lstOfTuple]


####################################################################################
####################################################################################
###########---- FCD data --------------------#######################################
####################################################################################


@app.route('/animation_FCD/', methods=['GET', 'POST'])
def animation_FCD():

    session["FCD_day_start"]  = '2022-10-18'
    session["FCD_day_end"]  = '2022-10-20'
    session["FCD_tod"] = 6
    session["FCD_hourrange"] = 2
    session['input_data_range'] = "10/13/2022 - 10/14/2022"

    return render_template("index_animated_FCD.html")


@app.route('/FCD_day_selector/', methods=['GET', 'POST'])
### select day (ZMU)...from Database
def FCD_day_selector():
    if request.method == "POST":

        ##### ------ daterangepicker ----- ############################################
        ###############################################################################

        try:
            data = request.form["daterange"]
            session['input_data_range'] = data
            print("-------------data-------------:", data)
        except:
            data = "10/12/2022 - 10/13/2022"

        try:
            start_date = data.split(" - ")[0]
            start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            session["FCD_day_start"] = str(start_date.date())
            selected_FCD_day_start = session["FCD_day_start"]
            print("gotta!!!----->> selected_FCD_day_start:", session["FCD_day_start"])  ##--->> only get date
            selected_FCD_day_start = str(selected_FCD_day_start)
        except:
            selected_FCD_day_start = '2022-10-04'
            session["FCD_day_start"] = selected_FCD_day_start
            print("using stored variable FCD_day_start: ", session["FCD_day_start"])

        try:
            end_date = data.split(" - ")[1]
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            session["FCD_day_end"] = str(end_date.date())
            selected_FCD_day_end = session["FCD_day_end"]
            print("gotta!!!----->> selected_FCD_day_end:", session["FCD_day_end"])  ##--->> only get date
            selected_FCD_day_end = str(selected_FCD_day_end)
        except:
            selected_FCD_day_end = '2022-10-15'
            session["FCD_day_end"] = selected_FCD_day_end
            print("using stored variable selected_FCD_day_end: ", session["FCD_day_end"])

        return render_template("index_animated_FCD.html")



@app.route('/FCD_hour_selector/', methods=['GET', 'POST'])
def FCD_hour_selector():
    if request.method == "POST":

        session["FCD_tod"] = 6
        # selected_FCD_hourrange = "1"
        # selected_FCD_day_start = '2022-10-18'
        # selected_FCD_day_end = '2022-10-20'
        # tod = "W"

        try:
            # selected_ZMU_day_start = session["ZMU_day_start"].strftime('%Y-%m-%d')
            selected_FCD_day_start = session["FCD_day_start"]
            print("day from selected_FCD_day_start:", selected_FCD_day_start)
        except:
            selected_FCD_day_start = '2022-10-04'
            session["FCD_day_start"] = selected_FCD_day_start
            print("using stored variable FCD_day_start: ", session["FCD_day_start"])

        try:
            # selected_ZMU_day_end = session["ZMU_day_end"].strftime('%Y-%m-%d')
            selected_FCD_day_end = session["FCD_day_end"]
            print("day from selected_FCD_day_end:", selected_FCD_day_end)
        except:
            selected_FCD_day_end = '2022-10-15'
            session["FCD_day_end"] = selected_FCD_day_end
            print("using stored variable FCD_day_end: ", session["FCD_day_end"])


        ## TRY if session exists
        try:
            session["FCD_hourrange"] = request.form.get("FCD_hourrange")
            selected_FCD_hourrange = session["FCD_hourrange"]
            print("selected_FCD_hourrange:", selected_FCD_hourrange)
            # print("hourange--------here????", selected_FCD_hourrange)
            selected_FCD_hourrange = str(selected_FCD_hourrange)
        except:
            session["FCD_hourrange"] = 2
            selected_FCD_hourrange = session["FCD_hourrange"]
            print("selected_FCD_hourrange: ", session["FCD_hourrange"])

        ## --------- get hourrange table from DB   -------- #######################

        selected_FCD_hourrange = int(selected_FCD_hourrange)
        if selected_FCD_hourrange == 0:  ## 00:00 ---> 07:00
            hourrange_id = "N1"
        elif selected_FCD_hourrange == 1:  ## 07:00 ----> 10:00
            hourrange_id = "M1"
        elif selected_FCD_hourrange == 2:  ## 10:00 ---> 14:00
            hourrange_id = "M2"
        elif selected_FCD_hourrange == 3:  ##  14:00 ---> 16:00
            hourrange_id = "A1"
        elif selected_FCD_hourrange == 4:  ## 16:00 ---> 20:00
            hourrange_id = "A2"
        elif selected_FCD_hourrange == 5:  ## 20:00 ---> 24:00
            hourrange_id = "A3"

        session["hourrange_id"] = hourrange_id
        print("------hourrange_id------------>>>:", hourrange_id)

        session["tod"] = "W"
        tod = session["tod"]
        print("----- tod------:", session["tod"])

        ## switch to table.........TRIPD----FCD data
        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        def reverseTuple(lstOfTuple):
            return [tup[::-1] for tup in lstOfTuple]

        query_origin_destination = text('''SELECT  dt_o, id,  id_zone_o, id_zone_d,
                                                    date_part('hour', dt_o) as hour, geom,
                                                    TO_CHAR(dt_o::DATE, 'dd-mm-yyyy') as day
                                                    FROM fcd.trips
                                                        WHERE date(dt_o) BETWEEN :x AND :xx  
                                                        AND hour_range_d = :y
                                                        AND tod_d = :z ''')

        stmt = query_origin_destination.bindparams(x=str(selected_FCD_day_start), xx=str(selected_FCD_day_end),
                                            y=str(hourrange_id), z=str(tod))

        # stmt = query_origin_destination.bindparams(x=str(selected_FCD_day), y=str(selected_FCD_hour))

        with engine.connect() as conn:
            res = conn.execute(stmt).all()

        routes_origin_destination = pd.DataFrame(res)

        ### ---> set reproducible sampling
        routes_origin_destination = routes_origin_destination.sample(frac=0.05)  # 10%; # n=1000

        ## get ZMU zones
        zmu_zones = text('''SELECT * from landuse.zones_with_pop_2015''')

        with engine.connect() as conn:
            res = conn.execute(zmu_zones).all()

        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geometry, hex=True)

        ZMU_ROMA = pd.DataFrame(res)
        ## transform geom into linestring....
        ZMU_ROMA['geometry'] = ZMU_ROMA.apply(wkb_tranformation, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA)
        ZMU_ROMA = ZMU_ROMA[['area', 'zmu', 'comune', 'quartiere', 'pgtu', 'municipio', 'geometry']]
        ## make a column with the index of the ZMU_ROMA
        ZMU_ROMA['index_zmu'] = ZMU_ROMA.index
        ZMU_ROMA = ZMU_ROMA.set_crs('epsg:4326', allow_override=True)

        ##### -------->>>> ORIGIN
        routes_origin_destination.rename({'id_zone_o': 'zmu'}, axis=1, inplace=True)
        ##merge with zmu zones
        routes_origin_destination = pd.merge(routes_origin_destination,
                                             ZMU_ROMA[['zmu', 'index_zmu', 'area', 'comune', 'quartiere']],
                                             on=['zmu'], how='left')
        routes_origin_destination.rename({'zmu': 'zmu_origin'}, axis=1, inplace=True)
        routes_origin_destination.rename({'index_zmu': 'index_zmu_origin'}, axis=1, inplace=True)
        routes_origin_destination.rename({'area': 'area_origin'}, axis=1, inplace=True)
        routes_origin_destination.rename({'comune': 'nome_comun_origin'}, axis=1, inplace=True)
        routes_origin_destination.rename({'quartiere': 'quartiere_origin'}, axis=1, inplace=True)

        ##### ------>>>>> DESTINATION
        routes_origin_destination.rename({'id_zone_d': 'zmu'}, axis=1, inplace=True)
        ##merge with zmu zones
        routes_origin_destination = pd.merge(routes_origin_destination,
                                             ZMU_ROMA[['zmu', 'index_zmu', 'area', 'comune', 'quartiere']],
                                             on=['zmu'], how='left')
        routes_origin_destination.rename({'zmu': 'zmu_destination'}, axis=1, inplace=True)
        routes_origin_destination.rename({'index_zmu': 'index_zmu_destination'}, axis=1, inplace=True)
        routes_origin_destination.rename({'area': 'area_destination'}, axis=1, inplace=True)
        routes_origin_destination.rename({'comune': 'nome_comun_destination'}, axis=1, inplace=True)
        routes_origin_destination.rename({'quartiere': 'quartiere_destination'}, axis=1, inplace=True)

        ## merge ORIGIN and DESTINATION routes by 'idtrajectory'
        routes = routes_origin_destination
        routes.rename({'id': 'idtrajectory'}, axis=1, inplace=True)

        ## save routes
        routes.to_csv(path_app + 'static/selected_routes.csv')

        ## transform geom into linestring....projection is in meters epsg:6875
        routes.rename({'geom': 'geometry'}, axis=1, inplace=True)
        routes['geometry'] = routes.apply(wkb_tranformation, axis=1)
        routes = gpd.GeoDataFrame(routes)


        ## reference system = 6875 (in meters)
        routes = routes.set_geometry("geometry")
        routes = routes.set_crs('epsg:6875', allow_override=True)

        ## convert into lat , lon
        routes = routes.to_crs({'init': 'epsg:4326'})
        routes = routes.set_crs('epsg:4326', allow_override=True)

        ## transfor hours as integer
        routes['hour'] = routes['hour'].astype(int)


        ## ---> initialize an empty list....
        route_FCD = []
        lista_polylines_FCD = []
        ##--> build the path of each FCD....
        all_days_IDs = list(routes.day.unique())  ## list all DAYS
        all_idtrajectory_IDs = list(routes.idtrajectory.unique())  ## list all the idterms for a particular day
        
        ## load previously saved "weight of zmu_zones"
        weight_of_zmu_zones = pd.read_csv(path_app + "static/weights_zmu.csv")
        for idx_day, day_id in enumerate(all_days_IDs):
            ## select all trips for a particular day
            full_day_trips = routes[routes.day == day_id]
            ## loop al over the routes
            for idx, idtrajectory_id in enumerate(all_idtrajectory_IDs):
                ## idtrajectory_id = 45814622
                # print(str(idtrajectory_id))
                trip = full_day_trips[full_day_trips.idtrajectory == idtrajectory_id]
                trip.reset_index(inplace=True)
                if len(trip)>0:
                    zmu_origin = trip['zmu_origin'][0]
                    zmu_destination = trip['zmu_destination'][0]
                    # make a polyline from linestring
                    trip_polyline = trip.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
                    trip_polyline = pd.DataFrame(trip_polyline)
                    trip_polyline.reset_index(inplace=True)
                    trip_polyline = trip_polyline[0][0]
                    ##---> reverse lon lat poisition (LON, LAT)
                    trip_polyline = reverseTuple(trip_polyline)
                lista = []
                keys_coords = list(range(len(trip_polyline)))
                dict_lat = {}
                dict_lon = {}
                for u in keys_coords:
                    dict_lat["lat"] = trip_polyline[u][0]
                    dict_lon["lon"] = trip_polyline[u][1]
                    # join two dictionaries
                    element = {**dict_lat, **dict_lon}
                    # print(element)
                    lista.append(element)
                lista = (json.dumps(lista))
                lista_trip_poline = str(
                    "L.motion.polyline(JSON.parse(\'" + lista + "\'" + "),  {color: 'blue', weight: 3},  {easing: L.Motion.Ease.easeInOutQuad}, {removeOnEnd: true,  icon: L.divIcon({html: " + "\"<i class='fa fa-car fa-2x fa-flip-horizontal' aria-hidden='true'></i>\"" + ", iconSize: L.point(26.5, 23)})" + " }).motionDuration(100)")
                lista_trip_poline = pd.DataFrame({'motion_lines': [lista_trip_poline]})
                lista_polylines_FCD.append(lista_trip_poline)

                ### ---------------------------------------------------------##########
                ###---- convert list of tuples to list of list -----###################
                trip_polyline = [list(ele) for ele in trip_polyline]
                ## build a L.polyline for the leaflet layer to put in the java script for the html page.
                trip_poline = "L.polyline(" + str(trip_polyline) + ")"
                df_ROUTE = pd.DataFrame({'zmu_origin': [(zmu_origin)],
                                         'zmu_destination': [(zmu_destination)],
                                         'trip': [trip_poline],
                                         'route': [trip_polyline],
                                         # 'OD_point': [OD_lista],
                                         'destination_point': [trip_polyline[-1]]})
                # 'timeline': [timeline_poline]})
                route_FCD.append(df_ROUTE)

        ## convert list into dataframe
        try:
            ##--->> save data
            lista_polylines_FCD_all = pd.concat(lista_polylines_FCD)
            import os
            if os.path.exists(path_app + "static/lista_coords.txt"):
                os.remove(path_app + "static/lista_coords.txt")
            else:
                print("The file does not exist")
            with open(path_app + "static/lista_coords.txt", "w") as file:
                for i in range(len(lista_polylines_FCD_all)):
                    motion_route = (lista_polylines_FCD_all[['motion_lines']].iloc[i])[0]
                    if i < len(lista_polylines_FCD_all) - 1:
                        file.write(str(motion_route) + ",\n")
                    else:
                        file.write(str(motion_route))
                        ## add "var name" in front of the .txt file, in order to properly loat it into the index.html file
            with open(path_app + "static/lista_coords.txt", "r+") as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var motion_polyline_route_FCD =[ \n" + old + "]")  # assign the "var name" in the .geojson file

            ### ---->>> route------------------------------------###############
            route_FCD_all = pd.concat(route_FCD)

            ##--->>> find recurrency of the same Origin --> Destination between zmu---##################
            OD_zmu = route_FCD_all.groupby(['zmu_origin', 'zmu_destination']).size().reset_index()
            OD_zmu.rename(columns={0: 'OD_counts'}, inplace=True)
            ### --->>> assign a weight to each zmu zone
            weight_of_zmu_zones = pd.merge(OD_zmu, route_FCD_all, on=['zmu_origin', 'zmu_destination'],
                                           how='left')
            weight_of_zmu_zones['zmu_destination'] = weight_of_zmu_zones.zmu_destination.astype('Int64')
            (weight_of_zmu_zones[['zmu_origin', 'zmu_destination', 'OD_counts']]).to_csv(
                path_app + 'static/weights_zmu.csv')
            route_FCD_all['zmu_destination'] = route_FCD_all.zmu_destination.astype('Int64')

            import os
            if os.path.exists(path_app + "static/selected_trip_path_FCD.txt"):
                os.remove(path_app + "static/selected_trip_path_FCD.txt")
            else:
                print("The file does not exist")
            with open(path_app + "static/selected_trip_path_FCD.txt", "w") as file:
                for i in range(len(route_FCD_all)):
                    route_trip = (route_FCD_all[['trip']].iloc[i])[0]
                    if i < len(route_FCD_all) - 1:
                        file.write(str(route_trip) + ",\n")
                    else:
                        file.write(str(route_trip))

            ## add "var name" in front of the .txt file, in order to properly loat it into the index.html file
            with open(path_app + "static/selected_trip_path_FCD.txt", "r+") as f:
                old = f.read()  # read everything in the file
                f.seek(0)  # rewind
                f.write("var route_FCD =[ \n" + old + "]")  # assign the "var name" in the .geojson file

            ############--------------------------######################################
            ############--------------------------######################################

            route_FCD = []
            for i in range(len(route_FCD_all)):
                route_trip = (route_FCD_all[['trip']].iloc[i])[0]
                if i < len(route_FCD_all) - 1:
                    route_FCD.append(route_trip)
                else:
                    route_FCD.append(route_trip)

            session["route_FCD"] = ','.join(route_FCD)
            # print(session["route_path"])

        except ValueError:
            print("empty dataframe.....")

        print("I am here")
        return render_template("index_animated_FCD_selected.html",
                               session_route_FCD=session["route_FCD"])


#################################################################
####### ------ TRAILS ---- FCD ------------ #####################


@app.route('/trails_FCD/', methods=['GET', 'POST'])
def trails_FCD():

    try:
        selected_FCD_day_start = session["FCD_day_start"]
        print("day from selected_FCD_day_start:", selected_FCD_day_start)
    except:
        selected_FCD_day_start = '2022-10-04'
        session["FCD_day_start"] = selected_FCD_day_start
        print("using stored variable FCD_day_start: ", session["FCD_day_start"])

    try:
        # selected_ZMU_day_end = session["ZMU_day_end"].strftime('%Y-%m-%d')
        selected_FCD_day_end = session["FCD_day_end"]
        print("day from selected_FCD_day_end:", selected_FCD_day_end)
    except:
        selected_FCD_day_end = '2022-10-15'
        session["FCD_day_end"] = selected_FCD_day_end
        print("using stored variable FCD_day_end: ", session["FCD_day_end"])

    try:
        selected_FCD_hourrange = session["FCD_hourrange"]
        print("selected_FCD_hourrange:", selected_FCD_hourrange)
    except:
        selected_FCD_hourrange = selected_FCD_hourrange
        session["FCD_hourrange"] = selected_FCD_hourrange
        print("selected_FCD_hourrange: ", session["FCD_hourrange"])


    ## function to transform Geometry from text to LINESTRING
    def wkb_tranformation(line):
        return wkb.loads(line.geom, hex=True)

    ## use to reverse lat lon position
    def reverseTuple(lstOfTuple):
        return [tup[::-1] for tup in lstOfTuple]

    ##--reload routes
    routes = pd.read_csv(path_app + 'static/selected_routes.csv')
    ## transform geom into linestring....
    ## transform geom into linestring....projection is in meters epsg:6875
    routes['geom'] = routes.apply(wkb_tranformation, axis=1)
    routes = gpd.GeoDataFrame(routes)
    routes.rename({'geom': 'geometry'}, axis=1, inplace=True)

    ## reference system = 6875 (in meters)
    routes = routes.set_geometry("geometry")
    routes = routes.set_crs('epsg:6875', allow_override=True)

    ## convert into lat , lon
    routes = routes.to_crs({'init': 'epsg:4326'})
    routes = routes.set_crs('epsg:4326', allow_override=True)

    ## transfor hours as integer
    routes['hour'] = routes['hour'].astype(int)
    lista_polylines_FCD = []
    ##--> build the path of each FCD....
    all_days_IDs = list(routes.day.unique())  ## list all DAYS
    all_idtrajectory_IDs = list(routes.idtrajectory.unique())  ## list all the idterms for a particular day
    ## load previously saved "weight of zmu_zones"
    weight_of_zmu_zones = pd.read_csv(path_app + "static/weights_zmu.csv")
    for idx_day, day_id in enumerate(all_days_IDs):
        ## select all trips for a particular day
        full_day_trips = routes[routes.day == day_id]
        ## loop al over the routes
        for idx, idtrajectory_id in enumerate(all_idtrajectory_IDs):
            trip = full_day_trips[full_day_trips.idtrajectory == idtrajectory_id]
            if len(trip)>0:
                trip = pd.merge(trip, weight_of_zmu_zones[['zmu_origin', 'zmu_destination', 'OD_counts']],
                                on=['zmu_origin', 'zmu_destination'],
                                how='left')
                ### ----> possible color list....
                a = 7
                OD_weight = (trip.OD_counts[0]) / a
                color_OD = 'blue'
                if math.isnan(OD_weight):
                    OD_weight = 1  ## this is the default weight of the polyline
                elif ((OD_weight <= 0.5 / a) and (OD_weight > (0.1 / a))):
                    color_OD = 'blue'
                elif ((OD_weight <= 1 / a) and (OD_weight > 0.5 / a)):
                    color_OD = 'blue'
                elif ((OD_weight <= 3 / a) and (OD_weight > 1 / a)):
                    color_OD = 'blue'
                elif ((OD_weight <= 4 / a) and (OD_weight > 3 / a)):
                    color_OD = 'red'
                elif ((OD_weight <= 5 / a) and (OD_weight > 4 / a)):
                    color_OD = 'red'
                elif ((OD_weight <= 10 / a) and (OD_weight > 5 / a)):
                    color_OD = 'red'
                elif ((OD_weight <= 20 / a) and (OD_weight > 10 / a)):
                    color_OD = 'red'
                elif ((OD_weight <= 30 / a) and (OD_weight > 20 / a)):
                    color_OD = 'orange'
                elif ((OD_weight <= 40 / a) and (OD_weight > 30 / a)):
                    color_OD = 'orange'
                elif ((OD_weight > 40 / a)):
                    color_OD = 'yellow'

                trip.drop_duplicates(['zmu_origin'], inplace=True)
                trip.reset_index(inplace=True)
                ### make a polyline from linestring
                trip_polyline = trip.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
                trip_polyline = pd.DataFrame(trip_polyline)
                trip_polyline.reset_index(inplace=True)
                trip_polyline = trip_polyline[0][0]
                ##---> reverse lon lat poisition (LON, LAT)
                trip_polyline = reverseTuple(trip_polyline)
                ##----> MAKE a dictionary...of points of polyline
                lista = []
                keys_coords = list(range(len(trip_polyline)))
                dict_lat = {}
                dict_lon = {}
                for u in keys_coords:
                    dict_lat["lat"] = trip_polyline[u][0]
                    dict_lon["lon"] = trip_polyline[u][1]
                    # join two dictionaries
                    element = {**dict_lat, **dict_lon}
                    # print(element)
                    lista.append(element)
                lista = (json.dumps(lista))
                # lista_trip_poline = str("L.motion.polyline(JSON.parse(\'" + lista + "\'" + "),  {color: 'blue', weight:" + str(OD_weight) + "},  {easing: L.Motion.Ease.easeInOutQuad}, {removeOnEnd: true}).motionDuration(200)")

                # lista_trip_poline = str(
                #    "L.motion.polyline(JSON.parse(\'" + lista + "\'" + "),  {color:\'" + color_OD + "\' , weight:" + str(
                #        OD_weight) + "},  {easing: L.Motion.Ease.easeInOutQuad}, {removeOnEnd: true, showMarker: false, icon: L.divIcon({html: " + "\"<i class='fa fa-car fa-2xs fa-flip-horizontal' aria-hidden='true'></i>\"" + ", iconSize: L.point(26.5, 23)})" + "}).motionDuration(7000)")
                lista_trip_poline = str(
                    "L.motion.polyline(JSON.parse(\'" + lista + "\'" + "),  {color:\'" + color_OD + "\' , weight:" + str(
                        OD_weight) + "},  {easing: L.Motion.Ease.easeInOutQuad}, {removeOnEnd: true, showMarker: false, icon: L.divIcon({html: " + "\"<i class='fa fa-car fa-2xs fa-flip-horizontal' aria-hidden='true'></i>\"" + ", iconSize: L.point(0, 0)})" + "}).motionDuration(40000)")

                lista_trip_poline = pd.DataFrame({'motion_lines': [lista_trip_poline]})
                lista_polylines_FCD.append(lista_trip_poline)

    ## convert list into dataframe
    try:
        ##--->> save data
        lista_polylines_FCD_all = pd.concat(lista_polylines_FCD)

        import os
        if os.path.exists(path_app + "static/lista_coords.txt"):
            os.remove(path_app + "static/lista_coords.txt")
        else:
            print("The file does not exist")
        with open(path_app + "static/lista_coords.txt", "w") as file:
            for i in range(len(lista_polylines_FCD_all)):
                motion_route = (lista_polylines_FCD_all[['motion_lines']].iloc[i])[0]
                if i < len(lista_polylines_FCD_all) - 1:
                    file.write(str(motion_route) + ",\n")
                else:
                    file.write(str(motion_route))
                    ## add "var name" in front of the .txt file, in order to properly loat it into the index.html file
        with open(path_app + "static/lista_coords.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var motion_polyline_route_FCD =[ \n" + old + "]")  # assign the "var name" in the .geojson file

    except ValueError:
        print("empty dataframe.....")



    lista_coords = []
    for i in range(len(lista_polylines_FCD_all)):
        motion_route = (lista_polylines_FCD_all[['motion_lines']].iloc[i])[0]
        if i < len(lista_polylines_FCD_all) - 1:
            lista_coords.append(motion_route)
        else:
            lista_coords.append(motion_route)

    session["lista_coords"] = ','.join(lista_coords)
    # print(session["lista_coords"])

    return render_template("index_trails_FCD_selected.html",
                           session_lista_coords=session["lista_coords"])



@app.route('/GTFS_type_selector/', methods=['GET', 'POST'])
def GTFS_type_selector():

    session['GTFS_hour'] = '7'

    if request.method == "POST":

        user = session.sid
        print("session user ID:", user)

        session["GTFS_type"] = request.form.get("GTFS_type")
        selected_GTFS_type = session["GTFS_type"]
        print("selected_GTFS_type:", selected_GTFS_type)
        selected_GTFS_type = str(selected_GTFS_type)

        with open(path_app + 'static/params/GTFS_type_' + user + '.txt', "w") as file:
            file.write(str(selected_GTFS_type))

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_GTFS_type = int(selected_GTFS_type)
        if selected_GTFS_type == 11:  ## bus
            GTFS_type = 'bus'
            print("Road data ----> bus")
            print("selected_GTFS_type:--------selector", selected_GTFS_type)
            session['type'] = GTFS_type
            print("------GTFS_type------------>>>:", GTFS_type)
            with open(path_app + 'static/params/GTFS_name_' + user + '.txt', "w") as file:
                file.write(str(GTFS_type))


        elif selected_GTFS_type == 12:  ## ferro
            GTFS_type = 'rail'
            print("Rail data ----> ferro")
            print("selected_GTFS_type:--------selector", selected_GTFS_type)
            session['type'] = GTFS_type
            print("------GTFS_type------------>>>:", GTFS_type)
            with open(path_app + 'static/params/GTFS_name_' + user + '.txt', "w") as file:
                file.write(str(GTFS_type))

        return render_template("index_GTFS_select_daytype.html")




### select hour range and (ZMU) from Database
@app.route('/GTFS_tod_selector/', methods=['GET', 'POST'])
def GTFS_tod_selector():

    session['GTFS_hour'] = '7'
    session["GTFS_tod"] = 9
    if request.method == "POST":

        user = session.sid
        print("session user ID:", user)

        with open(path_app + "static/params/GTFS_type_" + session.sid + ".txt", "r") as file:
            selected_GTFS_type = file.read()
        print("selected_GTFS_type-------I AM HERE-----------: ", selected_GTFS_type)
        session["GTFS_type"] = selected_GTFS_type


        with open(path_app + "static/params/GTFS_name_" + session.sid + ".txt", "r") as file:
            selected_GTFS_type_name = file.read()
        print("selected_GTFS_type_name-------I AM HERE-----------: ", selected_GTFS_type_name)
        session["type"] = selected_GTFS_type_name



        try:
            if session["GTFS_type"]:
                print("selected_GTFS_type:", session["GTFS_type"])
                # selected_GTFS_type = session["GTFS_type"]
        except:
            print("--------------")
            selected_GTFS_type = 11
            session["GTFS_type"] = selected_GTFS_type
            print("selected_GTFS_type----exception: ", session["GTFS_type"])


        ### find the type of day (WORKING day - PRE holiday -  HOLIDAY)
        ## TRY if session exists (get "tod")
        try:
            session["GTFS_tod"] = request.form.get("GTFS_tod")
            selected_GTFS_tod = session["GTFS_tod"]
            print("selected_GTFS_tod:", selected_GTFS_tod)
            selected_GTFS_tod = str(selected_GTFS_tod)
        except:
            session["GTFS_tod"] = 7
            selected_GTFS_tod = session["GTFS_tod"]
            print("selected_GTFS_tod: ", session["GTFS_tod"])

        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_GTFS_tod))

        ## --------- get hourrange table from DB   -------- #######################

        selected_GTFS_tod = int(selected_GTFS_tod)
        if selected_GTFS_tod == 6:     ## WORKING day
            tod = "W"
        elif selected_GTFS_tod == 7:    ## PRE holiday
            tod = "P"
        elif selected_GTFS_tod == 8:    ## HOLIDAY
            tod = "H"

        session["tod"] = tod
        print("------tod------------>>>:", tod)

        return render_template("index_GTFS_select_daytype.html")




@app.route('/GTFS_LEGS_hour_selector/', methods=['GET', 'POST'])
def GTFS_LEGS_hour_selector():

    session['GTFS_hour'] = '7'
    import glob

    try:
        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "r") as file:
            selected_GTFS_tod = file.read()
        print("selected_ZMU_tod-------I AM HERE-----------: ", selected_GTFS_tod)
    except:
        stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
        stored_tod_files.sort(key=os.path.getmtime)
        stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]
        with open(stored_tod_file) as file:
            selected_GTFS_tod = file.read()
        print("selected_GTFS_tod-------I AM HERE-----------: ", selected_GTFS_tod)



    try:
        with open(path_app + "static/params/GTFS_type_" + session.sid + ".txt", "r") as file:
            selected_GTFS_type = file.read()
        print("selected_GTFS_type-------I AM HERE-----------: ", selected_GTFS_type)
    except:
        stored_GTFS_type_files = glob.glob(path_app + "static/params/GTFS_type_*.txt")
        stored_GTFS_type_files.sort(key=os.path.getmtime)
        stored_GTFS_type_file = stored_GTFS_type_files[len(stored_GTFS_type_files) - 1]
        with open(stored_GTFS_type_file) as file:
            selected_GTFS_type = file.read()
        print("selected_GTFS_type-------I AM HERE-----------: ", selected_GTFS_type)

    with open(path_app + "static/params/GTFS_name_" + session.sid + ".txt", "r") as file:
        selected_GTFS_type_name = file.read()
    print("selected_GTFS_type_name-------I AM HERE-----------: ", selected_GTFS_type_name)


    session["type"] = selected_GTFS_type_name
    session["GTFS_type"] = selected_GTFS_type
    session["GTFS_tod"] = selected_GTFS_tod
    # session["check_ZMU_tod"] = session["ZMU_tod"]


    user = session.sid
    print("session user ID:", user)

    if request.method == "POST":
        ## TRY if session exists
        try:
            session["GTFS_hour"] = request.form.get("GTFS_hour")
            selected_GTFS_hour = session["GTFS_hour"]
            print("selected_GTFS_hour within session:", selected_GTFS_hour)
            selected_GTFS_hour = str(selected_GTFS_hour)
        except:
            session["GTFS_hour"] = 7
            selected_GTFS_hour = session["GTFS_hour"]
            print("using stored variable: ", session["GTFS_hour"])

        with open(path_app + "static/params/selected_GTFS_hour_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_GTFS_hour))
        tod =  session["tod"]
        print("------GTFS_type------------>>>:", selected_GTFS_type_name)
        print("------tod------------>>>:", tod)


        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        ## use to reverse lat lon position
        def reverseTuple(lstOfTuple):
            return [tup[::-1] for tup in lstOfTuple]

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool
        import matplotlib.pyplot as plt
        import shapely
        import numpy as np

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        print("selected_GTFS_hour:", selected_GTFS_hour)

        if (selected_GTFS_type_name == 'bus') & (tod == 'W'):
            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                           from_lat, from_lon, to_lat, to_lon, to_stop_name,
                                                           timeinsec, dist_metri, fromstop_id_elevation, tostop_id_elevation,
                                                           date_part('hour', from_ctime) as hour, geom,
                                                           TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                           FROM gtfs.gtfs_bus_feriale
                                                               WHERE extract(hour from from_ctime) = :y
                                                                         /*limit 1000*/ ''')
            print("------GTFS_type------------############# :", selected_GTFS_type_name)
            print("------tod------------#########:", tod)
            print("------------ selected_GTFS_hour -------- ######:", selected_GTFS_hour)

        elif (selected_GTFS_type_name == 'bus') & (tod == 'H'):
            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                            from_lat, from_lon, to_lat, to_lon,
                                                            to_stop_name, timeinsec, 
                                                            dist_metri, fromstop_id_elevation, 
                                                            tostop_id_elevation,
                                                            date_part('hour', from_ctime) as hour, geom,
                                                            TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                            FROM gtfs.gtfs_bus_festivo
                                                               WHERE extract(hour from from_ctime) = :y
                                                                         /*limit 1000*/ ''')
            print("------GTFS_type------------###########:", selected_GTFS_type_name)
            print("------tod------------########:", tod)
            print("------------ selected_GTFS_hour -------- ######:", selected_GTFS_hour)

        elif (selected_GTFS_type_name == 'bus') & (tod == 'P'):
            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                            from_lat, from_lon, to_lat, to_lon,
                                                            to_stop_name, timeinsec, dist_metri, 
                                                            fromstop_id_elevation, tostop_id_elevation,
                                                            date_part('hour', from_ctime) as hour, geom,
                                                            TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                            FROM gtfs.gtfs_bus_prefestivo
                                                               WHERE extract(hour from from_ctime) = :y
                                                                         /*limit 1000*/ ''')
            print("------GTFS_type------------###########:", selected_GTFS_type_name)
            print("------tod------------########:", tod)
            print("------------ selected_GTFS_hour -------- ######:", selected_GTFS_hour)


        elif (selected_GTFS_type_name == 'rail') & (tod == 'W'):
            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                           from_lat, from_lon, to_lat, to_lon, 
                                                           to_stop_name, timeinsec, dist_metri_shape, 
                                                           fromstop_id_elevation, tostop_id_elevation,
                                                           date_part('hour', from_ctime) as hour, geom, kwh,
                                                           TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                           FROM gtfs.gtfs_ferro_feriale
                                                               WHERE extract(hour from from_ctime) = :y
                                                                         /*limit 1000*/ ''')
            print("------GTFS_type------------###########:", selected_GTFS_type_name)
            print("------tod------------########:", tod)
            print("------------ selected_GTFS_hour -------- ######:", selected_GTFS_hour)

        elif (selected_GTFS_type_name == 'rail') & (tod == 'H'):
            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                           from_lat, from_lon, to_lat, to_lon,
                                                           to_stop_name, timeinsec, dist_metri_shape, 
                                                           fromstop_id_elevation, tostop_id_elevation,
                                                           date_part('hour', from_ctime) as hour, geom, kwh,
                                                           TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                           FROM gtfs.gtfs_ferro_festivo
                                                               WHERE extract(hour from from_ctime) = :y
                                                                         /*limit 1000*/ ''')
            print("------GTFS_type------------###########:", selected_GTFS_type_name)
            print("------tod------------########:", tod)
            print("------------ selected_GTFS_hour -------- ######:", selected_GTFS_hour)


        elif (selected_GTFS_type_name == 'rail') & (tod == 'P'):
            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                                  from_lat, from_lon, to_lat, to_lon, 
                                                                  to_stop_name, timeinsec, dist_metri_shape, 
                                                                  fromstop_id_elevation, tostop_id_elevation,
                                                                  date_part('hour', from_ctime) as hour, geom, kwh,
                                                                  TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                                  FROM gtfs.gtfs_ferro_prefestivo
                                                                     WHERE extract(hour from from_ctime) = :y
                                                                               /*limit 1000*/ ''')
            print("------GTFS_type------------###########:", selected_GTFS_type_name)
            print("------tod------------########:", tod)
            print("------------ selected_GTFS_hour -------- ######:", selected_GTFS_hour)


        stmt = query_gtfs.bindparams(y=str(selected_GTFS_hour))

        with engine.connect() as conn:
            res = conn.execute(stmt).all()

        routes_gtfs = pd.DataFrame(res)
        len(routes_gtfs)
        ### groupby AND INDEX......
        GTFS_STOPS = routes_gtfs.groupby(['to_lat', 'to_lon', 'to_stop_name']).size().reset_index().rename(
                columns={0: 'counts'})

        ##-----> make a geodataframe with lat, lon, coordinates
        geometry = [Point(xy) for xy in zip(GTFS_STOPS.to_lon, GTFS_STOPS.to_lat)]
        crs = {'init': 'epsg:4326'}
        gdf_stop_buses = GeoDataFrame(GTFS_STOPS, crs=crs, geometry=geometry)
        ## save as .geojson file
        gdf_stop_buses.to_file(filename=path_app + 'static/gtfs_stops_tod.geojson',
                               driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + 'static/gtfs_stops_tod.geojson', 'r+', encoding='utf8',
                  errors='ignore') as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var stop_buses = \n" + old)  # assign the "var name" in the .geojson file

        ## transform geodataframe into .geojson and send to the .html direclty within the current session
        stop_buses_json = gdf_stop_buses.to_json()
        # print("gdf_stop_buses_json:", gdf_stop_buses_json)

        session["stop_buses_json"] = stop_buses_json
        # print("-------- GTFS data file------------:", session["stop_buses_json"])

        ##### ------ HEATMAPS ------------- #############################################
        #################################################################################

        ## find the extents of the map
        xmin, ymin, xmax, ymax = gdf_stop_buses.total_bounds
        # cell_size = 0.005 ## 500 meters
        cell_size = 0.01  ## 1 km (0.01)
        grid_cells = []
        for x0 in np.arange(xmin, xmax + cell_size, cell_size):
            for y0 in np.arange(ymin, ymax + cell_size, cell_size):
                # bounds
                x1 = x0 - cell_size
                y1 = y0 + cell_size
                grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))
        cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                crs=gdf_stop_buses.crs)

        merged_bus = gpd.sjoin(gdf_stop_buses, cell, how='left', op='within')

        # make a simple count variable that we can sum
        merged_bus['n_buses'] = 1
        # Compute stats per grid cell -- aggregate number of vehicles to grid cells with dissolve
        dissolve = merged_bus.dissolve(by="index_right", aggfunc="count")
        cell.loc[dissolve.index, 'n_buses'] = dissolve.n_buses.values
        ## ---->> save GRIDDED data ------------#####
        centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
        centroids = pd.DataFrame(centroids, columns=["x", "y"])
        gridded_data = pd.DataFrame({'x': centroids.x,
                                     'y': centroids.y,
                                     'z': cell.n_buses})
        ## remove none values
        gridded_data = gridded_data[gridded_data['z'].notna()]

        lista = []
        for i in range(len(gridded_data)):
            # print(centroids.x.iloc[i])
            stringa = str(
                "{lat:" + str(gridded_data.y.iloc[i]) + ", lng:" + str(gridded_data.x.iloc[i]) + ", count:" + str(
                    gridded_data.z.iloc[i]) + "}")
            # print(stringa)
            lista.append(stringa)
        joined_lista = (",".join(lista))
        joined_lista = str("[" + joined_lista + "]")
        #### send data direclty to the .html file....within tis session
        session["stop_buses_heatmap"] = joined_lista
        # print(session["stop_buses_heatmap"])


        ## save file
        with open(path_app + "static/gridded_n_buses.txt", "w") as file:
            file.write(str(joined_lista))
        with open(path_app + "static/gridded_n_buses.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var n_buses = \n" + old)  # assign the "var name" in the .geojson file

        min_n_buses = min(gridded_data.z)
        max_n_buses = max(gridded_data.z)


        session["min_n_buses"] = min_n_buses
        session["max_n_buses"] = max_n_buses


        with open(path_app + "static/min_n_buses.txt", "w") as file:
            file.write(str(min_n_buses))
        with open(path_app + "static/min_n_buses.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var min_n_buses = \n" + old)  # assign the "var name" in the .geojson file

        with open(path_app + "static/max_n_buses.txt", "w") as file:
            file.write(str(max_n_buses))
        with open(path_app + "static/max_n_buses.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var max_n_buses = \n" + old)  # assign the "var name" in the .geojson file




        ################################################################################
        ################################################################################

        ###################################################################################
        ################ ---- get TPL LINES from GTFS (DB)  -------------- ################

        ### groupby AND INDEX......

        if (selected_GTFS_type_name == 'rail') & (tod == 'W'):
            GTFS_LEGS = routes_gtfs.groupby(['geom', 'from_stop_name', 'to_stop_name', 'kwh', 'dist_metri_shape']).size().reset_index().rename(columns={0: 'counts'})
            GTFS_LEGS['index_LEGS'] = GTFS_LEGS.index
            ## remove "dist_metri" == 0
            GTFS_LEGS = GTFS_LEGS[GTFS_LEGS.dist_metri_shape != 0]
        elif (selected_GTFS_type_name == 'rail') & (tod == 'P'):
            GTFS_LEGS = routes_gtfs.groupby(['geom', 'from_stop_name', 'to_stop_name', 'kwh', 'dist_metri_shape']).size().reset_index().rename(columns={0: 'counts'})
            GTFS_LEGS['index_LEGS'] = GTFS_LEGS.index
            ## remove "dist_metri" == 0
            GTFS_LEGS = GTFS_LEGS[GTFS_LEGS.dist_metri_shape != 0]
        elif (selected_GTFS_type_name == 'rail') & (tod == 'H'):
            GTFS_LEGS = routes_gtfs.groupby(['geom', 'from_stop_name', 'to_stop_name', 'kwh', 'dist_metri_shape']).size().reset_index().rename(columns={0: 'counts'})
            GTFS_LEGS['index_LEGS'] = GTFS_LEGS.index
            ## remove "dist_metri" == 0
            GTFS_LEGS = GTFS_LEGS[GTFS_LEGS.dist_metri_shape != 0]
        elif (selected_GTFS_type_name == 'bus'):
            GTFS_LEGS = routes_gtfs.groupby(['geom', 'from_stop_name', 'to_stop_name', 'dist_metri']).size().reset_index().rename(columns={0: 'counts'})
            GTFS_LEGS['index_LEGS'] = GTFS_LEGS.index
            GTFS_LEGS['kwh'] = GTFS_LEGS['counts']
            ## remove "dist_metri" == 0
            GTFS_LEGS = GTFS_LEGS[GTFS_LEGS.dist_metri != 0]


        ## initialize an empty list
        gtfs_LEGS = []
        ## loop al over the routes
        for idx, id_LEG in enumerate(list(GTFS_LEGS.index_LEGS)):
            LEG = GTFS_LEGS[GTFS_LEGS.index_LEGS == id_LEG]
            LEG.reset_index(inplace=True)

            ### make a polyline from linestring
            GTFS_LEG_polyline = LEG['geom'][0].strip("[]")
            GTFS_LEG_polyline = str("[") + GTFS_LEG_polyline + str("]")
            GTFS_LEG_polyline = eval(GTFS_LEG_polyline)
            GTFS_LEG_polyline = reverseTuple(GTFS_LEG_polyline)

            ## make a geodataframe
            geom = LineString(GTFS_LEG_polyline)
            poline_gdf = gpd.GeoDataFrame(geometry=[geom])
            ## make a dataframe

            if (selected_GTFS_type_name == 'bus'):
                df_trip_poline = pd.DataFrame({'from': [LEG['from_stop_name'][0]],
                                           'to': [LEG['to_stop_name'][0]],
                                           'counts': [LEG['counts'][0]],
                                           'consumption': [LEG['kwh'][0]],
                                           'dist_metri': [LEG['dist_metri'][0]]
                                           })
            elif (selected_GTFS_type_name == 'rail'):
                df_trip_poline = pd.DataFrame({'from': [LEG['from_stop_name'][0]],
                                               'to': [LEG['to_stop_name'][0]],
                                               'counts': [LEG['counts'][0]],
                                               'consumption': [LEG['kwh'][0]],
                                               'dist_metri': [LEG['dist_metri_shape'][0]]
                                               })

            ## attach geometry
            geom = poline_gdf['geometry']
            df_trip_poline['geometry'] = geom
            gtfs_LEGS.append(df_trip_poline)

        ## concatenate all trips
        gtfs_LEGS_all = pd.concat(gtfs_LEGS)
        ## normalize cosumption
        gtfs_LEGS_all['consumption']= round( (gtfs_LEGS_all['consumption']) / (gtfs_LEGS_all['dist_metri']/1000) , ndigits=2)

        ## plot quick histogram
        # import matplotlib.pyplot as plt
        # plt.style.use("ggplot")
        # plt.hist(list(gtfs_LEGS_all['consumption']), bins=30)
        # plt.savefig(path_app + 'static/consumption_hist.png')
        # plt.clf()


        del(gtfs_LEGS)
        del(GTFS_LEGS)

        gtfs_LEGS_all = gpd.GeoDataFrame(gtfs_LEGS_all)
        gtfs_LEGS_all = gtfs_LEGS_all.set_crs('epsg:4326')

        ## transform geodataframeo into .geojson
        LEGS_gtfs = gtfs_LEGS_all.to_json()


        session["LEGS_gtfs"] = LEGS_gtfs
        # print("----LEGS_gtfs-----------------------:",   session["LEGS_gtfs"])

        ### ---->>>> save into .geojson file ----#######################################################
        with open(path_app + 'static/gtfs_LEGS.geojson', 'w') as f:
            f.write(gtfs_LEGS_all.to_json())
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/gtfs_LEGS.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gtfs_hour = \n" + old)  # assign the "var name" in the .geojson file

        return render_template("index_trails_GTFS_selected.html",
                               session_stop_buses = session["stop_buses_json"],
                               session_LEGS_gtfs = session["LEGS_gtfs"],
                               session_STOPS_gtfs_heatmap = session["stop_buses_heatmap"])  # session_lista_coords_GTFS=session["lista_coords_GTFS"]


###################################################################################
###################################################################################
###################################################################################
###################################################################################






################################################################################################################
################################################################################################################
############# ------- TPL EMISSIONS_TPL by trip ID and from ZMUs zones ----------------#########################
################################################################################################################


### select BUS FLEET TYPE  -------- #################################
@app.route('/fleet_selector/', methods=['GET', 'POST'])
def fleet_selector():
    import glob

    if request.method == "POST":

        session["bus_fleet_type"] = request.form.get("bus_fleet_type")
        selected_bus_fleet_type = session["bus_fleet_type"]
        print("selected_bus_fleet_type:", selected_bus_fleet_type)
        selected_bus_fleet_type = str(selected_bus_fleet_type)


        selected_bus_fleet_type = int(selected_bus_fleet_type)
        if selected_bus_fleet_type == 100:
            print("rm1")
            fleet = 'rm1'
            print("selected_bus_fleet_type:--------selector", selected_bus_fleet_type, fleet)


        with open(path_app + "static/params/selected_bus_fleet_type:" + session.sid + ".txt", "w") as file:
            file.write(str(selected_bus_fleet_type))

        return render_template("index_GTFS_emiss_select_daytype.html")



### select BUS LOAD -------- #################################
@app.route('/load_selector/', methods=['GET', 'POST'])
def load_selector():
    import glob

    if request.method == "POST":

        session["bus_load"] = request.form.get("bus_load")
        selected_bus_load = session["bus_load"]
        print("selected_bus_load:", selected_bus_load)
        selected_bus_load = str(selected_bus_load)


        selected_bus_load = int(selected_bus_load)
        if selected_bus_load == 50:
            print("rm1")
            load = 'rm1'
            print("selected_bus_load:--------selector", selected_bus_load, load)


        with open(path_app + "static/params/selected_bus_load_:" + session.sid + ".txt", "w") as file:
            file.write(str(selected_bus_load))

        return render_template("index_GTFS_emiss_select_daytype.html")



### select EMISSION FUEL TYPE  -------- #################################
@app.route('/fuel_type_selector/', methods=['GET', 'POST'])
def fuel_type_selector():
    import glob

    if request.method == "POST":

        session["fuel_type"] = request.form.get("fuel_type")
        selected_fuel_type = session["fuel_type"]
        print("selected_fuel_type:", selected_fuel_type)
        selected_fuel_type = str(selected_fuel_type)


        selected_fuel_type = int(selected_fuel_type)
        if selected_fuel_type == 102:
            print("diesel")
            fuel = 'diesel'
            print("selected_fuel_type:--------selector", selected_fuel_type, fuel)

        elif selected_fuel_type == 103:
            print("cng")
            fuel = 'cng'
            print("selected_fuel_type:--------selector", selected_fuel_type, fuel)

        elif selected_fuel_type == 104:  ##
            print("electricity")
            fuel = 'electricity'
            print("selected_fuel_type:--------selector", selected_fuel_type, fuel)

        elif selected_fuel_type == 105:  ##
            print("biodiesel")
            fuel = 'biodiesel'
            print("selected_fuel_type:--------selector", selected_fuel_type, fuel)


        with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_fuel_type))

        return render_template("index_GTFS_emiss_select_daytype.html")




### select EURO STANDARD TYPE  -------- #################################
@app.route('/euro_standard_selector/', methods=['GET', 'POST'])
def euro_standard_selector():
    import glob

    if request.method == "POST":

        try:
            with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "r") as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
        except:
            stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
            stored_fuel_files.sort(key=os.path.getmtime)
            stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
            with open(stored_fuel_file) as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)

        session["fuel_type"] = selected_fuel_type
        session["euro_type"] = request.form.get("euro_type")
        selected_euro_standard = session["euro_type"]
        print("selected_euro_standard:", selected_euro_standard)
        selected_euro_standard = str(selected_euro_standard)


        selected_euro_standard = int(selected_euro_standard)
        if selected_euro_standard == 11:
            print("euro 3")
            euro = 3
            print("selected_euro_standard:--------selector", selected_euro_standard, euro)

        elif selected_euro_standard == 12:
            print("euro 4")
            euro = 4
            print("selected_euro_standard:--------selector", selected_euro_standard, euro)

        elif selected_euro_standard == 13:
            print("euro 5")
            euro = 5
            print("selected_euro_standard:--------selector", selected_euro_standard, euro)

        elif selected_euro_standard == 14:
            print("euro 6")
            euro = 6
            print("selected_euro_standard:--------selector", selected_euro_standard, euro)


        with open(path_app + "static/params/selected_euro_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_euro_standard))

        return render_template("index_GTFS_emiss_select_daytype.html")




### select SEGMENT TYPE  -------- #################################
@app.route('/segment_selector/', methods=['GET', 'POST'])
def segment_selector():
    import glob

    if request.method == "POST":

        try:
            with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "r") as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
        except:
            stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
            stored_fuel_files.sort(key=os.path.getmtime)
            stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
            with open(stored_fuel_file) as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)

        try:
            with open(path_app + "static/params/selected_euro_type_" + session.sid + ".txt", "r") as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)
        except:
            stored_euro_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_euro_files.sort(key=os.path.getmtime)
            stored_euro_file = stored_euro_files[len(stored_euro_files) - 1]
            with open(stored_euro_file) as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)

        session["fuel_type"] = selected_fuel_type
        session["euro_type"] = selected_euro_standard


        session["segment_type"] = request.form.get("segment_type")
        selected_segment_type = session["segment_type"]
        print("selected_segment_type:", selected_segment_type)
        selected_segment_type = str(selected_segment_type)


        selected_segment_type = int(selected_segment_type)
        if selected_segment_type == 21:
            print("standard")
            segment = 'standard'
            print("selected_segment_type:--------selector", selected_segment_type, segment)

        elif selected_segment_type == 22:
            print("articulated")
            segment = 'articulated'
            print("selected_segment_type:--------selector", selected_segment_type, segment)

        elif selected_segment_type == 23:
            print("midi")
            segment = 'midi'
            print("selected_segment_type:--------selector", selected_segment_type, segment)



        with open(path_app + "static/params/selected_segment_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_segment_type))

        return render_template("index_GTFS_emiss_select_daytype.html")






### select ENGINE TYPE  -------- #################################
@app.route('/engine_selector/', methods=['GET', 'POST'])
def engine_selector():
    import glob

    if request.method == "POST":

        try:
            with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "r") as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
        except:
            stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
            stored_fuel_files.sort(key=os.path.getmtime)
            stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
            with open(stored_fuel_file) as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)

        try:
            with open(path_app + "static/params/selected_euro_type_" + session.sid + ".txt", "r") as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)
        except:
            stored_euro_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_euro_files.sort(key=os.path.getmtime)
            stored_euro_file = stored_euro_files[len(stored_euro_files) - 1]
            with open(stored_euro_file) as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)

        try:
            with open(path_app + "static/params/selected_segment_type_" + session.sid + ".txt", "r") as file:
                selected_segment_type = file.read()
            print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)
        except:
            stored_segment_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_segment_files.sort(key=os.path.getmtime)
            stored_segment_file = stored_segment_files[len(stored_segment_files) - 1]
            with open(stored_segment_file) as file:
                selected_segment_type = file.read()
            print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)

        session["fuel_type"] = selected_fuel_type
        session["euro_type"] = selected_euro_standard
        session["segment_type"] = selected_segment_type


        session["engine_type"] = request.form.get("engine_type")
        selected_engine_type = session["engine_type"]
        print("selected_engine_type:", selected_engine_type)
        selected_engine_type = str(selected_engine_type)


        selected_engine_type = int(selected_engine_type)
        if selected_engine_type == 30:
            print("monofuel")
            engine_type = 'monofuel'
            print("selected_engine_type:--------selector", selected_engine_type, engine_type)

        elif selected_segment_type == 31:
            print("phev")
            engine_type = 'phev'
            print("selected_engine_type:--------selector", selected_engine_type, engine_type)


        with open(path_app + "static/params/selected_engine_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_engine_type))

        return render_template("index_GTFS_emiss_select_daytype.html")







### select EMISSION TYPE or POLLUTANT TYPE  -------- #################################
@app.route('/emission_type_selector_tpl/', methods=['GET', 'POST'])
def emission_type_selector_tpl():
    import glob

    if request.method == "POST":


        try:
            with open(path_app + "static/params/selected_bus_load_" + session.sid + ".txt", "r") as file:
                selected_bus_load = file.read()
            print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)
        except:
            stored_bus_load_files = glob.glob(path_app + "static/params/selected_bus_load_*.txt")
            stored_bus_load_files.sort(key=os.path.getmtime)
            stored_bus_load_file = stored_bus_load_files[len(stored_bus_load_files) - 1]
            with open(stored_bus_load_file) as file:
                selected_bus_load = file.read()
            print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)



        try:
            with open(path_app + "static/params/selected_bus_fleet_type_" + session.sid + ".txt", "r") as file:
                selected_bus_fleet_type = file.read()
            print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)
        except:
            stored_bus_fleet_files = glob.glob(path_app + "static/params/selected_bus_fleet_type_*.txt")
            stored_bus_fleet_files.sort(key=os.path.getmtime)
            stored_bus_fleet_file = stored_bus_fleet_files[len(stored_bus_fleet_files) - 1]
            with open(stored_bus_fleet_file) as file:
                selected_bus_fleet_type = file.read()
            print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)


        try:
            with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "r") as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
        except:
            stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
            stored_fuel_files.sort(key=os.path.getmtime)
            stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
            with open(stored_fuel_file) as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)

        try:
            with open(path_app + "static/params/selected_euro_type_" + session.sid + ".txt", "r") as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)
        except:
            stored_euro_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_euro_files.sort(key=os.path.getmtime)
            stored_euro_file = stored_euro_files[len(stored_euro_files) - 1]
            with open(stored_euro_file) as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)

        try:
            with open(path_app + "static/params/selected_segment_type_" + session.sid + ".txt", "r") as file:
                selected_segment_type = file.read()
            print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)
        except:
            stored_segment_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_segment_files.sort(key=os.path.getmtime)
            stored_segment_file = stored_segment_files[len(stored_segment_files) - 1]
            with open(stored_segment_file) as file:
                selected_segment_type = file.read()
            print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)

        try:
            with open(path_app + "static/params/selected_engine_type_" + session.sid + ".txt", "r") as file:
                selected_engine_type = file.read()
            print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)
        except:
            stored_engine_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_engine_files.sort(key=os.path.getmtime)
            stored_engine_file = stored_engine_files[len(stored_engine_files) - 1]
            with open(stored_engine_file) as file:
                stored_engine_file = file.read()
            print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)

        session["fuel_type"] = selected_fuel_type
        session["euro_type"] = selected_euro_standard
        session["segment_type"] = selected_segment_type
        session["engine_type"] = selected_engine_type
        session["bus_load"] = selected_bus_load
        session["bus_fleet_type"] = selected_bus_fleet_type


        session["emission_type"] = request.form.get("emission_type")
        selected_emission_type = session["emission_type"]
        print("selected_emission_type:", selected_emission_type)
        selected_emission_type = str(selected_emission_type)

        ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
        selected_emission_type = int(selected_emission_type)
        if selected_emission_type == 11:  ## EC
            pollutant = 'EC'
            print("EC")
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)
            ## switch to table.........render....
            
        elif selected_emission_type == 12:  ## EC wtt
            print("EC_wtt")
            pollutant = 'EC_wtt'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 13:  ## NOx
            print("NOx")
            pollutant = 'NOx'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 14:  ## NMVOC
            print("nmvoc")
            pollutant = 'nmvoc'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 15:  ## PM
            print("PM")
            pollutant = 'PM'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 16:  ## PM_nexh
            print("PM_nexh")
            pollutant = 'PM_nexh'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 17:  ## CO2 eq
            print("CO2eq")
            pollutant = 'CO2_eq'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)

        elif selected_emission_type == 18:  ## CO2 eq wtt
            print("CO2eq_wtt")
            pollutant = 'CO2_eq_wtt'
            print("selected_emission_type:--------selector", selected_emission_type, pollutant)


        with open(path_app + "static/params/selected_emission_type_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_emission_type))

        return render_template("index_GTFS_emiss_select_daytype.html")




@app.route('/tpl_tod_selector/', methods=['GET', 'POST'])
def tpl_tod_selector():

    import glob

    session['GTFS_hour'] = '7'
    session["GTFS_tod"] = 9
    if request.method == "POST":

        user = session.sid
        print("session user ID:", user)

        try:
            with open(path_app + "static/params/selected_bus_load_" + session.sid + ".txt", "r") as file:
                selected_bus_load = file.read()
            print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)
        except:
            stored_bus_load_files = glob.glob(path_app + "static/params/selected_bus_load_*.txt")
            stored_bus_load_files.sort(key=os.path.getmtime)
            stored_bus_load_file = stored_bus_load_files[len(stored_bus_load_files) - 1]
            with open(stored_bus_load_file) as file:
                selected_bus_load = file.read()
            print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)

        try:
            with open(path_app + "static/params/selected_bus_fleet_type_" + session.sid + ".txt", "r") as file:
                selected_bus_fleet_type = file.read()
            print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)
        except:
            stored_bus_fleet_files = glob.glob(path_app + "static/params/selected_bus_fleet_type_*.txt")
            stored_bus_fleet_files.sort(key=os.path.getmtime)
            stored_bus_fleet_file = stored_bus_fleet_files[len(stored_bus_fleet_files) - 1]
            with open(stored_bus_fleet_file) as file:
                selected_bus_fleet_type = file.read()
            print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)


        try:
            with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "r") as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
        except:
            stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
            stored_fuel_files.sort(key=os.path.getmtime)
            stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
            with open(stored_fuel_file) as file:
                selected_fuel_type = file.read()
            print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)

        try:
            with open(path_app + "static/params/selected_euro_type_" + session.sid + ".txt", "r") as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)
        except:
            stored_euro_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
            stored_euro_files.sort(key=os.path.getmtime)
            stored_euro_file = stored_euro_files[len(stored_euro_files) - 1]
            with open(stored_euro_file) as file:
                selected_euro_standard = file.read()
            print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)

        try:
            with open(path_app + "static/params/selected_segment_type_" + session.sid + ".txt", "r") as file:
                selected_segment_type = file.read()
            print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)
        except:
            stored_segment_files = glob.glob(path_app + "static/params/selected_segment_type_*.txt")
            stored_segment_files.sort(key=os.path.getmtime)
            stored_segment_file = stored_segment_files[len(stored_segment_files) - 1]
            with open(stored_segment_file) as file:
                selected_segment_type = file.read()
            print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)

        try:
            with open(path_app + "static/params/selected_engine_type_" + session.sid + ".txt", "r") as file:
                selected_engine_type = file.read()
            print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)
        except:
            stored_engine_files = glob.glob(path_app + "static/params/selected_engine_type_*.txt")
            stored_engine_files.sort(key=os.path.getmtime)
            stored_engine_file = stored_engine_files[len(stored_engine_files) - 1]
            with open(stored_engine_file) as file:
                selected_engine_type = file.read()
            print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)


        try:
            with open(path_app + "static/params/selected_emission_type_" + session.sid + ".txt", "r") as file:
                selected_emission_type = file.read()
            print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)
        except:
            stored_emission_files = glob.glob(path_app + "static/params/selected_emission_type_*.txt")
            stored_emission_files.sort(key=os.path.getmtime)
            stored_emission_file = stored_emission_files[len(stored_emission_files) - 1]
            with open(stored_emission_file) as file:
                selected_emission_type = file.read()
            print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)


        session["fuel_type"] = selected_fuel_type
        session["euro_type"] = selected_euro_standard
        session["segment_type"] = selected_segment_type
        session["engine_type"] = selected_engine_type
        session["emission_type"] = selected_emission_type
        session["bus_load"] = selected_bus_load
        session["bus_fleet_type"] = selected_bus_fleet_type


        ### find the type of day (WORKING day - PRE holiday -  HOLIDAY)
        ## TRY if session exists (get "tod")
        try:
            session["GTFS_tod"] = request.form.get("GTFS_tod")
            selected_GTFS_tod = session["GTFS_tod"]
            print("selected_GTFS_tod:", selected_GTFS_tod)
            selected_GTFS_tod = str(selected_GTFS_tod)
        except:
            session["GTFS_tod"] = 7
            selected_GTFS_tod = session["GTFS_tod"]
            print("selected_GTFS_tod: ", session["GTFS_tod"])

        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_GTFS_tod))

        ## --------- get hourrange table from DB   -------- #######################

        selected_GTFS_tod = int(selected_GTFS_tod)
        if selected_GTFS_tod == 6:     ## WORKING day
            tod = "W"
        elif selected_GTFS_tod == 7:    ## PRE holiday
            tod = "P"
        elif selected_GTFS_tod == 8:    ## HOLIDAY
            tod = "H"

        session["tod"] = tod
        print("------tod------------>>>:", tod)

        return render_template("index_GTFS_emiss_select_daytype.html")






@app.route('/tpl_emissions_legs_hour_selector/', methods=['GET', 'POST'])
def tpl_emissions_legs_hour_selector():

    session['GTFS_hour'] = '7'
    import glob

    try:
        with open(path_app + "static/params/selected_bus_load_" + session.sid + ".txt", "r") as file:
            selected_bus_load = file.read()
        print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)
    except:
        stored_bus_load_files = glob.glob(path_app + "static/params/selected_bus_load_*.txt")
        stored_bus_load_files.sort(key=os.path.getmtime)
        stored_bus_load_file = stored_bus_load_files[len(stored_bus_load_files) - 1]
        with open(stored_bus_load_file) as file:
            selected_bus_load = file.read()
        print("selected_bus_load-------I AM HERE-----------: ", selected_bus_load)

    try:
        with open(path_app + "static/params/selected_bus_fleet_type_" + session.sid + ".txt", "r") as file:
            selected_bus_fleet_type = file.read()
        print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)
    except:
        stored_bus_fleet_files = glob.glob(path_app + "static/params/selected_bus_fleet_type_*.txt")
        stored_bus_fleet_files.sort(key=os.path.getmtime)
        stored_bus_fleet_file = stored_bus_fleet_files[len(stored_bus_fleet_files) - 1]
        with open(stored_bus_fleet_file) as file:
            selected_bus_fleet_type = file.read()
        print("selected_bus_fleet_type-------I AM HERE-----------: ", selected_bus_fleet_type)


    try:
        with open(path_app + "static/params/selected_fuel_type_" + session.sid + ".txt", "r") as file:
            selected_fuel_type = file.read()
        print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)
    except:
        stored_fuel_files = glob.glob(path_app + "static/params/selected_fuel_type_*.txt")
        stored_fuel_files.sort(key=os.path.getmtime)
        stored_fuel_file = stored_fuel_files[len(stored_fuel_files) - 1]
        with open(stored_fuel_file) as file:
            selected_fuel_type = file.read()
        print("selected_fuel_type-------I AM HERE-----------: ", selected_fuel_type)

    try:
        with open(path_app + "static/params/selected_euro_type_" + session.sid + ".txt", "r") as file:
            selected_euro_standard = file.read()
        print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)
    except:
        stored_euro_files = glob.glob(path_app + "static/params/selected_euro_type_*.txt")
        stored_euro_files.sort(key=os.path.getmtime)
        stored_euro_file = stored_euro_files[len(stored_euro_files) - 1]
        with open(stored_euro_file) as file:
            selected_euro_standard = file.read()
        print("selected_euro_standard-------I AM HERE-----------: ", selected_euro_standard)

    try:
        with open(path_app + "static/params/selected_segment_type_" + session.sid + ".txt", "r") as file:
            selected_segment_type = file.read()
        print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)
    except:
        stored_segment_files = glob.glob(path_app + "static/params/selected_segment_type_*.txt")
        stored_segment_files.sort(key=os.path.getmtime)
        stored_segment_file = stored_segment_files[len(stored_segment_files) - 1]
        with open(stored_segment_file) as file:
            selected_segment_type = file.read()
        print("selected_segment_type-------I AM HERE-----------: ", selected_segment_type)

    try:
        with open(path_app + "static/params/selected_engine_type_" + session.sid + ".txt", "r") as file:
            selected_engine_type = file.read()
        print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)
    except:
        stored_engine_files = glob.glob(path_app + "static/params/selected_engine_type_*.txt")
        stored_engine_files.sort(key=os.path.getmtime)
        stored_engine_file = stored_engine_files[len(stored_engine_files) - 1]
        with open(stored_engine_file) as file:
            selected_engine_type = file.read()
        print("selected_engine_type-------I AM HERE-----------: ", selected_engine_type)

    try:
        with open(path_app + "static/params/selected_emission_type_" + session.sid + ".txt", "r") as file:
            selected_emission_type = file.read()
        print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)
    except:
        stored_emission_files = glob.glob(path_app + "static/params/selected_emission_type_*.txt")
        stored_emission_files.sort(key=os.path.getmtime)
        stored_emission_file = stored_emission_files[len(stored_emission_files) - 1]
        with open(stored_emission_file) as file:
            selected_emission_type = file.read()
        print("selected_emission_type-------I AM HERE-----------: ", selected_emission_type)


    try:
        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "r") as file:
            selected_GTFS_tod = file.read()
        print("selected_GTFS_tod-------I AM HERE-----------: ", selected_GTFS_tod)
    except:
        stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
        stored_tod_files.sort(key=os.path.getmtime)
        stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]
        with open(stored_tod_file) as file:
            selected_GTFS_tod = file.read()
        print("selected_GTFS_tod-------I AM HERE-----------: ", selected_GTFS_tod)


    session["fuel_type"] = selected_fuel_type
    session["euro_type"] = selected_euro_standard
    session["segment_type"] = selected_segment_type
    session["engine_type"] = selected_engine_type
    session["emission_type"] = selected_emission_type
    session["GTFS_tod"] = selected_GTFS_tod
    session["bus_load"] = selected_bus_load
    session["bus_fleet_type"] = selected_bus_fleet_type

    # selected_fuel_type = 102
    # selected_euro_standard = 12
    # selected_segment_type = 21
    # selected_engine_type = 31
    # selected_emission_type = 15
    # selected_GTFS_tod = 7
    # selected_GTFS_hour = 7
    # selected_bus_load = 50
    # selected_bus_fleet_type = 100

    selected_fuel_type = int(selected_fuel_type)
    if selected_fuel_type == 102:
        print("diesel")
        fuel = 'diesel'
        print("selected_fuel_type:--------selector", selected_fuel_type, fuel)

    elif selected_fuel_type == 103:
        print("cng")
        fuel = 'cng'
        print("selected_fuel_type:--------selector", selected_fuel_type, fuel)

    elif selected_fuel_type == 104:  ##
        print("electricity")
        fuel = 'electricity'
        print("selected_fuel_type:--------selector", selected_fuel_type, fuel)

    elif selected_fuel_type == 105:  ##
        print("biodiesel")
        fuel = 'biodiesel'
        print("selected_fuel_type:--------selector", selected_fuel_type, fuel)


    selected_euro_standard = int(selected_euro_standard)
    if selected_euro_standard == 11:
        print("euro 3")
        euro = 3
        print("selected_euro_standard:--------selector", selected_euro_standard, euro)

    elif selected_euro_standard == 12:
        print("euro 4")
        euro = 4
        print("selected_euro_standard:--------selector", selected_euro_standard, euro)

    elif selected_euro_standard == 13:
        print("euro 5")
        euro = 5
        print("selected_euro_standard:--------selector", selected_euro_standard, euro)

    elif selected_euro_standard == 14:
        print("euro 6")
        euro = 6
        print("selected_euro_standard:--------selector", selected_euro_standard, euro)

    selected_segment_type = int(selected_segment_type)
    if selected_segment_type == 21:
        print("standard")
        segment = 'standard'
        print("selected_segment_type:--------selector", selected_segment_type, segment)

    elif selected_segment_type == 22:
        print("articulated")
        segment = 'articulated'
        print("selected_segment_type:--------selector", selected_segment_type, segment)

    elif selected_segment_type == 23:
        print("midi")
        segment = 'midi'
        print("selected_segment_type:--------selector", selected_segment_type, segment)

    selected_engine_type = int(selected_engine_type)
    if selected_engine_type == 30:
        print("monofuel")
        engine_type = 'monofuel'
        print("selected_engine_type:--------selector", selected_engine_type, engine_type)

    elif selected_engine_type == 31:
        print("phev")
        engine_type = 'phev'
        print("selected_engine_type:--------selector", selected_engine_type, engine_type)

    selected_bus_load = int(selected_bus_load)
    if selected_bus_load == 50:
        print("rm1")
        bus_load = 'rm1'
        print("selected_bus_load:--------selector", selected_bus_load, bus_load)

    selected_bus_fleet_type = int(selected_bus_fleet_type)
    if selected_bus_fleet_type == 100:
        print("rm1")
        bus_fleet_type = 'rm1'
        print("selected_bus_fleet_type:--------selector", selected_bus_fleet_type, bus_fleet_type)



    ################## ---- query vehicle Type --------- ###############################
    ####################################################################################

    from sqlalchemy import create_engine
    from sqlalchemy import exc
    import sqlalchemy as sal
    from sqlalchemy.pool import NullPool

    ## function to transform Geometry from text to LINESTRING
    def wkb_tranformation(line):
        return wkb.loads(line.geom, hex=True)

    ## use to reverse lat lon position
    def reverseTuple(lstOfTuple):
        return [tup[::-1] for tup in lstOfTuple]

    from sqlalchemy import create_engine
    from sqlalchemy import exc
    import sqlalchemy as sal
    from sqlalchemy.pool import NullPool
    import matplotlib.pyplot as plt
    import shapely
    import numpy as np

    # engine = create_engine("postgresql://postgres:superuser@192.168.134.36:5432/HAIG_ROMA")
    engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
    connection = engine.connect()
    from sqlalchemy.sql import text


    query_all_veh_type = text('''select distinct id_veh_type from impacts.route_cons_emis_feriale  ''')
    stmt = query_all_veh_type

    with engine.connect() as conn:
        res = conn.execute(stmt).all()

    vehicle_type = pd.DataFrame(res)

    query_all_veh_type = text('''SELECT * FROM gen.bus_types ''')
    with engine.connect() as conn:
        res = conn.execute(query_all_veh_type).all()

    all_vehicle_type = pd.DataFrame(res)


    query_veh_type = text('''SELECT * FROM federico.effective_bus_types
                                      WHERE engine = :x AND
                                      segment =:y AND
                                      euro_standard =:z AND
                                      primary_fuel =:xx  ''')

    stmt = query_veh_type.bindparams(x=str(engine_type), y=str(segment),
                                     z=str(euro), xx=str(fuel))

    with engine.connect() as conn:
        res = conn.execute(stmt).all()

    vehicle_type = pd.DataFrame(res)
    vehicle_type.reset_index(inplace=True)
    print("---- I  am HERE ---------------- ", len(vehicle_type))


    vehicle_type = vehicle_type['id_veh_type'][0]
    print("-------- vehicle_type-------", vehicle_type)


    #########################################################################################################
    #########################################################################################################



    ## --------- SELECT DATA TYPE and redirect to new .html page -------- ##############
    selected_emission_type = int(selected_emission_type)
    if selected_emission_type == 11:  ## EC
        pollutant = 'EC'
        print("EC")
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)
        ## switch to table.........render....
        # return render_template("index_zmu_emiss_select_day.html")

    elif selected_emission_type == 12:  ## EC wtt
        print("EC_wtt")
        pollutant = 'EC_wtt'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    elif selected_emission_type == 13:  ## NOx
        print("NOx")
        pollutant = 'NOx'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    elif selected_emission_type == 14:  ## NMVOC
        print("nmvoc")
        pollutant = 'nmvoc'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    elif selected_emission_type == 15:  ## PM
        print("PM")
        pollutant = 'PM'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    elif selected_emission_type == 16:  ## PM_nexh
        print("PM_nexh")
        pollutant = 'PM_nexh'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    elif selected_emission_type == 17:  ## CO2 eq
        print("CO2eq")
        pollutant = 'CO2_eq'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    elif selected_emission_type == 18:  ## CO2 eq wtt
        print("CO2eq_wtt")
        pollutant = 'CO2_eq_wtt'
        print("selected_emission_type:--------selector", selected_emission_type, pollutant)

    selected_GTFS_tod = int(selected_GTFS_tod)
    if selected_GTFS_tod == 6:  ## WORKING day
        tod = "W"
    elif selected_GTFS_tod == 7:  ## PRE holiday
        tod = "P"
    elif selected_GTFS_tod == 8:  ## HOLIDAY
        tod = "H"


    user = session.sid
    print("session user ID:", user)

    if request.method == "POST":
        ## TRY if session exists
        try:
            session["GTFS_hour"] = request.form.get("GTFS_hour")
            selected_GTFS_hour = session["GTFS_hour"]
            print("selected_GTFS_hour within session:", selected_GTFS_hour)
            selected_GTFS_hour = str(selected_GTFS_hour)
        except:
            session["GTFS_hour"] = 7
            selected_GTFS_hour = session["GTFS_hour"]
            print("using stored variable: ", session["GTFS_hour"])

        with open(path_app + "static/params/selected_GTFS_hour_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_GTFS_hour))


        tod =  session["tod"]
        print("------tod------------>>>:", tod)


        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        ## use to reverse lat lon position
        def reverseTuple(lstOfTuple):
            return [tup[::-1] for tup in lstOfTuple]

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool
        import matplotlib.pyplot as plt
        import shapely
        import numpy as np

        # engine = create_engine("postgresql://postgres:superuser@192.168.134.36:5432/HAIG_ROMA")
        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        # selected_GTFS_hour = '8'
        # tod = 'W'

        print("selected_GTFS_hour:", selected_GTFS_hour)


        if (tod == 'W'):
            query_gtfs_emiss = text('''SELECT id_route_fleet, id_bus_load, route_id, trip_id, from_stop_id, to_stop_id, id_veh_type, from_ctime,
                                                   ec, ec_wtt, nox, nmvoc, pm, pm_nexh, co2eq, co2eq_wtt, km, hi, t, ac_cons, he_cons,
                                                                     date_part('hour', from_ctime) as hour
                                                                     FROM impacts.route_cons_emis_feriale
                                                                         WHERE extract(hour from from_ctime) = :x
                                                                         AND   id_route_fleet =:y
                                                                           AND id_bus_load =:z  ''')


            stmt = query_gtfs_emiss.bindparams(x=str(selected_GTFS_hour), y=str(bus_fleet_type), z=str(bus_load))


            with engine.connect() as conn:
                res = conn.execute(stmt).all()

            emiss_gtfs = pd.DataFrame(res)
            len(emiss_gtfs)


            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                        from_lat, from_lon, to_lat, to_lon,
                                                        to_stop_name, timeinsec, 
                                                        dist_metri, fromstop_id_elevation, 
                                                        tostop_id_elevation,
                                                        date_part('hour', from_ctime) as hour, geom,
                                                        TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                        FROM gtfs.gtfs_bus_feriale
                                                           WHERE extract(hour from from_ctime) = :y
                                                                    ''')

            stmt = query_gtfs.bindparams(y=str(selected_GTFS_hour))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()

            gtfs_select = pd.DataFrame(res)
            len(gtfs_select)

        elif (tod == 'P'):
            query_gtfs_emiss = text('''SELECT id_route_fleet, id_bus_load, route_id, trip_id, from_stop_id, to_stop_id, id_veh_type, from_ctime,
                                                      ec, ec_wtt, nox, nmvoc, pm, pm_nexh, co2eq, co2eq_wtt, km, hi, t, ac_cons, he_cons,
                                                                        date_part('hour', from_ctime) as hour
                                                                        FROM impacts.route_cons_emis_prefestivo
                                                                            WHERE extract(hour from from_ctime) = :x
                                                                            AND   id_route_fleet =:y
                                                                              AND id_bus_load =:z  ''')

            stmt = query_gtfs_emiss.bindparams(x=str(selected_GTFS_hour), y=str(bus_fleet_type), z=str(bus_load))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()

            emiss_gtfs = pd.DataFrame(res)
            len(emiss_gtfs)

            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                           from_lat, from_lon, to_lat, to_lon,
                                                           to_stop_name, timeinsec, 
                                                           dist_metri, fromstop_id_elevation, 
                                                           tostop_id_elevation,
                                                           date_part('hour', from_ctime) as hour, geom,
                                                           TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                           FROM gtfs.gtfs_bus_prefestivo
                                                              WHERE extract(hour from from_ctime) = :y
                                                                       ''')

            stmt = query_gtfs.bindparams(y=str(selected_GTFS_hour))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()

            gtfs_select = pd.DataFrame(res)
            len(gtfs_select)

        elif (tod == 'H'):
            query_gtfs_emiss = text('''SELECT id_route_fleet, id_bus_load, route_id, trip_id, from_stop_id, to_stop_id, id_veh_type, from_ctime,
                                                      ec, ec_wtt, nox, nmvoc, pm, pm_nexh, co2eq, co2eq_wtt, km, hi, t, ac_cons, he_cons,
                                                                        date_part('hour', from_ctime) as hour
                                                                        FROM impacts.route_cons_emis_festivo
                                                                            WHERE extract(hour from from_ctime) = :x
                                                                            AND   id_route_fleet =:y
                                                                              AND id_bus_load =:z  ''')

            stmt = query_gtfs_emiss.bindparams(x=str(selected_GTFS_hour), y=str(bus_fleet_type), z=str(bus_load))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()

            emiss_gtfs = pd.DataFrame(res)
            len(emiss_gtfs)

            query_gtfs = text('''SELECT route_id, trip_id, from_stop_id, to_stop_id, from_stop_name, from_ctime, 
                                                           from_lat, from_lon, to_lat, to_lon,
                                                           to_stop_name, timeinsec, 
                                                           dist_metri, fromstop_id_elevation, 
                                                           tostop_id_elevation,
                                                           date_part('hour', from_ctime) as hour, geom,
                                                           TO_CHAR(from_ctime::DATE, 'dd-mm-yyyy') as day
                                                           FROM gtfs.gtfs_bus_festivo
                                                              WHERE extract(hour from from_ctime) = :y
                                                                       ''')

            stmt = query_gtfs.bindparams(y=str(selected_GTFS_hour))

            with engine.connect() as conn:
                res = conn.execute(stmt).all()

            gtfs_select = pd.DataFrame(res)
            len(gtfs_select)



        ##### make a join with the orignal GTFS data to get stot name and location (lat, lon)
        emiss_gtfs = pd.merge(emiss_gtfs, gtfs_select[['route_id', 'trip_id','from_stop_id', 'to_stop_id', 'from_stop_name',
                                               'from_lat', 'from_lon', 'to_lat', 'to_lon',
                                               'to_stop_name', 'timeinsec', 'dist_metri', 'geom']],
                                 on=['from_stop_id', 'to_stop_id', 'route_id', 'trip_id'],
                                     how='left')


        ### --- make intersection with zmu zones to see in which zone every stop falls in ---- #################
        ## ---->>> make intersection with ZMUs

        def wkb_tranformation_centroid(line):
            return wkb.loads(line.centroid, hex=True)

        ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA['centroid'] = ZMU_ROMA.apply(wkb_tranformation_centroid, axis=1)
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA)
        ZMU_ROMA = ZMU_ROMA.set_crs('epsg:4326')

        ## make a Geodataframe....
        geometry = [Point(xy) for xy in zip(emiss_gtfs.to_lon, emiss_gtfs.to_lat)]
        crs = {'init': 'epsg:4326'}
        emiss_gtfs_gdf = GeoDataFrame(emiss_gtfs, crs=crs, geometry=geometry)


        emiss_gtfs_gdf = emiss_gtfs_gdf.set_crs('epsg:4326', allow_override=True)
        emiss_gtfs_gdf = gpd.sjoin(ZMU_ROMA, emiss_gtfs_gdf, how='inner',
                                 predicate='intersects')
        emiss_gtfs = pd.DataFrame(emiss_gtfs_gdf[['index_zmu', 'POP_TOT_ZMU', 'area', 'zmu', 'comune', 'nome_comun',
                   'quartiere', 'pgtu', 'municipio',
                   'index_right', 'route_id', 'trip_id', 'from_stop_id', 'to_stop_id',
                   'id_veh_type', 'from_ctime', 'ec', 'ec_wtt', 'nox', 'nmvoc', 'pm',
                   'pm_nexh', 'co2eq', 'co2eq_wtt', 'km', 'hi', 't', 'ac_cons', 'he_cons', 'hour', 'from_stop_name', 'from_lat',
                   'from_lon', 'to_lat', 'to_lon', 'to_stop_name', 'timeinsec',
                   'dist_metri', 'geom']])


        ###############################################################################
        ################ ---- get STOPS from GTFS (DB)  -------------- ################

        ### groupby AND INDEX......
        # GTFS_STOPS_from = routes_gtfs.groupby(['from_lat', 'from_lon', 'from_stop_name']).size().reset_index().rename(columns={0: 'counts'})
        GTFS_STOPS_emiss = emiss_gtfs.groupby(['to_lat', 'to_lon', 'to_stop_name']).size().reset_index().rename(
                columns={0: 'counts'})

        GTFS_STOPS_sum_emiss = emiss_gtfs[['to_lat', 'to_lon', 'to_stop_name','ec','ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt',
                                             'ac_cons', 'he_cons']].groupby(['to_lat', 'to_lon', 'to_stop_name']).sum().reset_index().rename(
                                              columns={0: 'sums'})

        GTFS_STOPS_sum_emiss_temp = emiss_gtfs[
            ['to_lat', 'to_lon', 'to_stop_name', 't']].groupby(['to_lat', 'to_lon', 'to_stop_name']).mean().reset_index().rename(
            columns={0: 'mean'})

        GTFS_STOPS_sum_emiss =  pd.merge(GTFS_STOPS_sum_emiss, GTFS_STOPS_sum_emiss_temp,
                                     on=['to_lat', 'to_lon', 'to_stop_name'],
                                         how='left')


        ##-----> make a geodataframe with lat, lon, coordinates
        geometry = [Point(xy) for xy in zip(GTFS_STOPS_emiss.to_lon, GTFS_STOPS_emiss.to_lat)]
        crs = {'init': 'epsg:4326'}
        gdf_stop_emiss_buses = GeoDataFrame(GTFS_STOPS_emiss, crs=crs, geometry=geometry)
        gdf_stop_sum_emiss_buses = GeoDataFrame(GTFS_STOPS_sum_emiss, crs=crs, geometry=geometry)
        ## save as .geojson file
        gdf_stop_emiss_buses.to_file(filename=path_app + 'static/gtfs_stops_emiss_tod.geojson',
                               driver='GeoJSON')
        gdf_stop_sum_emiss_buses.to_file(filename=path_app + 'static/gtfs_stops_means_emiss_tod.geojson',
                                     driver='GeoJSON')
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + 'static/gtfs_stops_emiss_tod.geojson', 'r+', encoding='utf8',
                  errors='ignore') as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var stop_emissions_buses = \n" + old)  # assign the "var name" in the .geojson file
        with open(path_app + 'static/gtfs_stops_means_emiss_tod.geojson', 'r+', encoding='utf8',
                  errors='ignore') as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var stop_means_emissions_buses = \n" + old)  # assign the "var name" in the .geojson file

        ## transform geodataframe into .geojson and send to the .html direclty within the current session
        stop_buses_emiss_json = gdf_stop_emiss_buses.to_json()
        gdf_stop_sum_emiss_buses_json = gdf_stop_sum_emiss_buses.to_json()
        # print("gdf_stop_buses_emiss_json:", stop_buses_emiss_json)

        session["stop_buses_emiss_json"] = stop_buses_emiss_json
        session["stop_buses_means_emiss_json"] = gdf_stop_sum_emiss_buses_json
        # print("-------- GTFS data file------------:", session["stop_buses_json"])

        ################################################################################
        ################################################################################
        ##### ------ HEATMAPS ------------- #############################################
        #################################################################################

        GTFS_LEGS_emiss = emiss_gtfs[['geom', 'from_stop_name', 'to_stop_name', 'index_zmu', 'zmu',
                                     'ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt',
                                      'ac_cons', 'he_cons']].groupby(['geom', 'from_stop_name', 'to_stop_name'],
            sort=False).sum().reset_index().rename(columns={0: 'sum'})


        GTFS_LEGS_emiss_temp = emiss_gtfs[
            ['geom', 'from_stop_name', 'to_stop_name', 't']].groupby(['geom', 'from_stop_name', 'to_stop_name']).mean().reset_index().rename(
                                                columns={0: 'mean'})

        GTFS_LEGS_emiss = pd.merge(GTFS_LEGS_emiss, GTFS_LEGS_emiss_temp,
                                        on=[ 'from_stop_name', 'to_stop_name', 'geom'],
                                        how='left')

        GTFS_LEGS_emiss['index_zmu'] = GTFS_LEGS_emiss.index_zmu.astype('int')
        GTFS_LEGS_emiss['zmu'] = GTFS_LEGS_emiss.zmu.astype('int')
        GTFS_LEGS_emiss['index_LEGS'] = GTFS_LEGS_emiss.index

        ## initialize an empty list
        gtfs_emiss_LEGS = []
        ## loop al over the routes
        print("---- I am HERE-----------------------------------------------")
        for idx, id_LEG in enumerate(list(GTFS_LEGS_emiss.index_LEGS)):
            LEG = GTFS_LEGS_emiss[GTFS_LEGS_emiss.index_LEGS == id_LEG]
            LEG.reset_index(inplace=True)

            ### make a polyline from linestring
            GTFS_LEG_polyline = LEG['geom'][0].strip("[]")
            GTFS_LEG_polyline = str("[") + GTFS_LEG_polyline + str("]")
            GTFS_LEG_polyline = reverseTuple(eval(GTFS_LEG_polyline))

            ## make a geodataframe
            poline_gdf = gpd.GeoDataFrame(geometry=[LineString(GTFS_LEG_polyline)])

            ## make a dataframe
            df_trip_poline = pd.DataFrame({'from': [LEG['from_stop_name'][0]],
                                       'to': [LEG['to_stop_name'][0]],
                                       #'ec': [LEG['ec'][0]],
                                       #'ec_wtt': [LEG['ec_wtt'][0]],
                                       #'nox': [LEG['nox'][0]],
                                       #'nmvoc': [LEG['nmvoc'][0]],
                                       #'pm': [LEG['pm'][0]],
                                       #'pm_nexh': [LEG['pm_nexh'][0]],
                                       #'co2_eq': [LEG['co2eq'][0]],
                                       #'co2_eq_wtt': [LEG['co2eq_wtt'][0]],
                                       #'temperature': [LEG['t'][0]],
                                       #'AC_cons': [LEG['ac_cons'][0]],
                                       #'heating_cons': [LEG['he_cons'][0]]
                                       })
            ## attach geometry
            df_trip_poline['geometry'] = poline_gdf['geometry']
            gtfs_emiss_LEGS.append(df_trip_poline)

        ## concatenate all trips
        gtfs_emiss_LEGS_all = pd.concat(gtfs_emiss_LEGS)

        del(gtfs_emiss_LEGS)
        del(GTFS_LEGS_emiss)

        gtfs_emiss_LEGS_all = gpd.GeoDataFrame(gtfs_emiss_LEGS_all)
        gtfs_emiss_LEGS_all = gtfs_emiss_LEGS_all.set_crs('epsg:4326')

        ## transform geodataframeo into .geojson
        emissions_LEGS_gtfs = gtfs_emiss_LEGS_all.to_json()


        session["emissions_LEGS_gtfs"] = emissions_LEGS_gtfs
        # print("----LEGS_gtfs-----------------------:",   session["emissions_LEGS_gtfs"])

        ### ---->>>> save into .geojson file ----#######################################################
        with open(path_app + 'static/gtfs_emiss_LEGS.geojson', 'w') as f:
            f.write(gtfs_emiss_LEGS_all.to_json())
        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/gtfs_emiss_LEGS.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gtfs_hour = \n" + old)  # assign the "var name" in the .geojson file



        ########--------------------------------#########################################################
        ########-----------------------------------------################################################
        ####### -------------- MAKE aggregation by ZMU ----------------------------------- ##############
        #################################################################################################
        #################################################################################################
        #################################################################################################

        ##### ---->>> Consider emission from ORIGIN (generation) @ ORIGIN  (highlight ORIGIN (coloured with the emission concentration at the Origin)
        ##### grouby + sum of the number of 'emission (ec,NOx, PM etc.)'

        aggregated_tpl_emission = emiss_gtfs[
            ['zmu', 'ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt',
             'ac_cons', 'he_cons']].groupby(
            ['zmu'], sort=False).sum().reset_index()

        aggregated_tpl_emission_temp = emiss_gtfs[
            ['zmu', 't']].groupby(
            ['zmu'], sort=False).mean().reset_index()

        aggregated_tpl_emission = pd.merge(aggregated_tpl_emission, aggregated_tpl_emission_temp,
                                   on=['zmu'],
                                   how='left')


        aggregated_tpl_emission = pd.merge(aggregated_tpl_emission, ZMU_ROMA, on=['zmu'], how='left')
        aggregated_tpl_emission = aggregated_tpl_emission[aggregated_tpl_emission['geometry'].notna()]

        aggregated_tpl_emission = aggregated_tpl_emission[
            ['ec', 'ec_wtt', 'nox', 'nmvoc', 'pm', 'pm_nexh', 'co2eq', 'co2eq_wtt',
              't', 'ac_cons', 'he_cons', 'index_zmu', 'POP_TOT_ZMU',
             'zmu',  'nome_comun', 'quartiere', 'geometry', 'pgtu']]

        aggregated_tpl_emission.replace([np.inf, -np.inf], np.nan, inplace=True)
        aggregated_tpl_emission['zmu'] = aggregated_tpl_emission.zmu.astype('int')

        aggregated_tpl_emission['ec'] = round(
            aggregated_tpl_emission['ec'], 2)
        aggregated_tpl_emission['ec_wtt'] = round(
            aggregated_tpl_emission['ec_wtt'], 2)
        aggregated_tpl_emission['nox'] = round(
            aggregated_tpl_emission['nox'], 2)
        aggregated_tpl_emission['nmvoc'] = round(
            aggregated_tpl_emission['nmvoc'], 2)
        aggregated_tpl_emission['pm'] = round(
            aggregated_tpl_emission['pm'], 4)
        aggregated_tpl_emission['pm_nexh'] = round(
            aggregated_tpl_emission['pm_nexh'], 4)
        aggregated_tpl_emission['co2eq'] = round(
            aggregated_tpl_emission['co2eq'], 2)
        aggregated_tpl_emission['co2eq_wtt'] = round(
            aggregated_tpl_emission['co2eq_wtt'], 2)
        aggregated_tpl_emission['t'] = round(
            aggregated_tpl_emission['t'], 2)
        aggregated_tpl_emission['ac_cons'] = round(
            aggregated_tpl_emission['ac_cons'], 4)
        aggregated_tpl_emission['he_cons'] = round(
            aggregated_tpl_emission['he_cons'], 4)

      
        ### ---- EMISSIONS  <---- ########################################################################
        ##################################################################################################

        try:
            aggregated_tpl_emission = gpd.GeoDataFrame(aggregated_tpl_emission)
        except IndexError:
            abort(404)

      

        ## save as .geojson file
        ### ---- EMISSIONS  <---- ##############
        aggregated_tpl_emission.to_file(filename=path_app + 'static/aggregated_tpl_emission.geojson',
                                        driver='GeoJSON')

        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/aggregated_tpl_emission.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregated_tpl_emissions_zmu = \n" + old)  # assign the "var name" in the .geojson file

        ##### --->>>>>> make the sessions data...<<<------------############################################
        ### convert Geodataframe into .geojson...
        session["aggregated_tpl_emissions_origin_zones"] = aggregated_tpl_emission.to_json()

        return render_template("index_GTFS_emiss_select_hour.html",
                               session_stop_emissions_buses = session["stop_buses_emiss_json"],
                               session_emissions_LEGS_gtfs = session["emissions_LEGS_gtfs"],
                               session_aggregated_tpl_emissions_oring_zones=session["aggregated_tpl_emissions_origin_zones"]
                               )


###################################################################################
###################################################################################
###################################################################################
###################################################################################






##################################################################################
##################################################################################
##################################################################################
##################################################################################
#### ---->> HEAT MAPS ---------------------- #####################################
##################################################################################

@app.route('/heatmaps_FCD/', methods=['GET', 'POST'])
def heatmaps_FCD():

    import glob
    session["ZMU_day_start"] = '2022-10-01'
    session["ZMU_day_end"] = '2022-10-15'
    # session["ZMU_hour"] = 7
    session["ZMU_hourrange"] = 999

    session["min_n_vehicles"] = 0
    session["max_n_vehicles"] = 56

    session["min_triptime"] = 0
    session["max_triptime"] = 899

    session["min_stoptime"] = 0
    session["max_stoptime"] = 899

    session["min_tripdistance"] = 0
    session["max_tripdistance"] = 85

    session["ZMU_tod"] = 6

    session['input_data_range'] = "10/13/2022 - 10/14/2022"

    stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
    stored_tod_files.sort(key=os.path.getmtime)
    stored_tod_file = stored_tod_files[len(stored_tod_files) - 1]

    with open(stored_tod_file) as file:
        selected_ZMU_tod = file.read()
    print("selected_ZMU_tod-------I AM HERE-----------: ", selected_ZMU_tod)
    session["ZMU_tod"] = selected_ZMU_tod

    return render_template("index_heatmaps_FCD.html", session_ZMU_hourrange = session["ZMU_hourrange"] )



### select day (ZMU)...from Database
@app.route('/FCD_heatmap_day_selector/', methods=['GET', 'POST'])
def FCD_heatmap_day_selector():

    # session["ZMU_tod"] = 6

    # session["data_type"] = 11
    # selected_ZMU_day_start = '2022-10-04'
    # selected_ZMU_day_end = '2022-10-05'
    # selected_ZMU_hourrange = 1
    # selected_ZMU_tod = 6
    if request.method == "POST":
        # session["ZMU_tod"] = 6
        ###--->> record the ZMU_day in into the Flask Session
        ## TRY if session exists

        ##### ------ daterangepicker ----- ############################################
        ###############################################################################

        try:
            data = request.form["daterange"]
            session['input_data_range'] = data
            print("-------------data-------------:", data)
        except:
            data = "10/12/2022 - 10/13/2022"

        try:
            start_date = data.split(" - ")[0]
            start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            session["ZMU_day_start"] = str(start_date.date())
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("gotta!!!----->> selected_ZMU_day_start:", session["ZMU_day_start"])  ##--->> only get date
            selected_ZMU_day_start = str(selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            end_date = data.split(" - ")[1]
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            session["ZMU_day_end"] = str(end_date.date())
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("gotta!!!----->> selected_ZMU_day_end:", session["ZMU_day_end"])  ##--->> only get date
            selected_ZMU_day_end = str(selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable selected_ZMU_day_end: ", session["ZMU_day_end"])

        ##########################################################################################################


        user = session.sid
        print("user:", user)

        print("session user ID:", session.sid)
        # print("full session:", session)
        return render_template("index_heatmaps_FCD.html")




### select Time of DAY (TOD) -------- #################################
@app.route('/tod_heatmap_selector/', methods=['GET', 'POST'])
def tod_heatmap_selector():

    import glob

    if request.method == "POST":

        session["ZMU_tod"] = request.form.get("ZMU_tod")
        selected_ZMU_tod = session["ZMU_tod"]
        print("selected_ZMU_tod:", selected_ZMU_tod)
        selected_ZMU_tod = str(selected_ZMU_tod)
        print("-----selected_ZMU_tod-----", selected_ZMU_tod)

        with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_ZMU_tod))

        return render_template("index_heatmaps_FCD.html")




#############################################################
## ----- using "tod" type of day.............................

### select hour range and (ZMU) from Database
@app.route('/FCD_heatmap_hourrange_selector/', methods=['GET', 'POST'])
def FCD_heatmap_hourrange_selector():

    import glob

    if request.method == "POST":
        try:
            # selected_ZMU_day_start = session["ZMU_day_start"].strftime('%Y-%m-%d')
            selected_ZMU_day_start = session["ZMU_day_start"]
            print("hour from selected_ZMU_day_start:", selected_ZMU_day_start)
        except:
            selected_ZMU_day_start = '2022-10-04'
            session["ZMU_day_start"] = selected_ZMU_day_start
            print("using stored variable ZMU_day_start: ", session["ZMU_day_start"])

        try:
            # selected_ZMU_day_end = session["ZMU_day_end"].strftime('%Y-%m-%d')
            selected_ZMU_day_end = session["ZMU_day_end"]
            print("hour from selected_ZMU_day_end:", selected_ZMU_day_end)
        except:
            selected_ZMU_day_end = '2022-10-15'
            session["ZMU_day_end"] = selected_ZMU_day_end
            print("using stored variable ZMU_day_end: ", session["ZMU_day_end"])


        ## TRY if session exists
        try:
            session["ZMU_hourrange"] = request.form.get("ZMU_hourrange")
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            selected_ZMU_hourrange = int(selected_ZMU_hourrange)
            print("selected_ZMU_hourrange:", selected_ZMU_hourrange)
        except:
            session["ZMU_hourrange"] = 2
            selected_ZMU_hourrange = session["ZMU_hourrange"]
            print("selected_ZMU_hourrange: ", session["ZMU_hourrange"])


        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_hourrange = int(selected_ZMU_hourrange)
        if selected_ZMU_hourrange == 0:  ## 00:00 ---> 07:00
            hourrange_id = "N1"
        elif selected_ZMU_hourrange == 1:  ## 07:00 ----> 10:00
            hourrange_id = "M1"
        elif selected_ZMU_hourrange == 2:  ## 10:00 ---> 14:00
            hourrange_id = "M2"
        elif selected_ZMU_hourrange == 3:  ##  14:00 ---> 16:00
            hourrange_id = "A1"
        elif selected_ZMU_hourrange == 4:  ## 16:00 ---> 20:00
            hourrange_id = "A2"
        elif selected_ZMU_hourrange == 5:  ## 20:00 ---> 24:00
            hourrange_id = "A3"

        session["hourrange_id"] = hourrange_id
        print("------hourrange_id------------>>>:", hourrange_id)



        try:
            with open(path_app + "static/params/selected_tod_zmu_" + session.sid + ".txt", "r") as file:
                selected_ZMU_tod = file.read()
            print("selected_ZMU_tod-------I AM HERE-----------: ", selected_ZMU_tod)
        except:
            ## sort in chronological order.....
            stored_tod_files = glob.glob(path_app + "static/params/selected_tod_zmu_*.txt")
            stored_tod_files.sort(key=os.path.getmtime)
            stored_tod_file = stored_tod_files[len(stored_tod_files)-1]

            with open(stored_tod_file) as file:
                selected_ZMU_tod = file.read()
            print("stored_tod_file-------I AM HERE-----------: ", selected_ZMU_tod)
        session["ZMU_tod"] = selected_ZMU_tod

        ## --------- get hourrange table from DB   -------- #######################

        selected_ZMU_tod = int(selected_ZMU_tod)
        if selected_ZMU_tod == 6:     ## WORKING day
            tod = "W"
        elif selected_ZMU_tod == 7:    ## PRE holiday
            tod = "P"
        elif selected_ZMU_tod == 8:    ## HOLIDAY
            tod = "H"

        session["tod"] = tod
        print("I am HERE ------tod------------>>>:", tod)

        ## switch to table.........TRIP----FCD data
        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool
        import matplotlib.pyplot as plt
        import shapely
        import numpy as np

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text
        query_destination = text(''' SELECT  id_veh, p_after, tt, dt_d, id, dist, hour_range_d,
                                                           date_part('hour', dt_d) as hour, geom
                                                          FROM fcd.trips  WHERE date(trips.dt_d) BETWEEN :x AND :xx 
                                                           AND hour_range_d = :y 
                                                          AND tod_d = :z ''')



        stmt = query_destination.bindparams(x=str(selected_ZMU_day_start), xx=str(selected_ZMU_day_end),
                                            y=str(hourrange_id), z=str(tod))

        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        routes_destination = pd.DataFrame(res)

        # routes_destination = routes_destination.sample(frac=0.1)  # 10%
        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)

        ## transform geom into linestring....projection is in meters epsg:6875
        routes_destination['geom'] = routes_destination.apply(wkb_tranformation, axis=1)
        routes_destination = gpd.GeoDataFrame(routes_destination)
        routes_destination.rename({'geom': 'geometry'}, axis=1, inplace=True)

        ## reference system = 6875 (in meters)
        routes_destination = routes_destination.set_geometry("geometry")
        routes_destination = routes_destination.set_crs('epsg:6875', allow_override=True)

        ## convert into lat , lon
        routes_destination = routes_destination.to_crs({'init': 'epsg:4326'})
        routes_destination = routes_destination.set_crs('epsg:4326', allow_override=True)


        df_coords = routes_destination.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
        df_coords = pd.DataFrame(df_coords)
        df_coords.reset_index(inplace=True)
        df_coords = df_coords[0]
        ##---> reverse lon lat poisition (LON, LAT)
        ##----> MAKE a dictionary...of points of polyline
        new_df = []
        index_coords = list(range(len(df_coords)))
        ## get last coordinate (@ destination of the TRIP)
        for u in index_coords:
            lat = df_coords[u][len(df_coords[u])-1][1]
            lon = df_coords[u][len(df_coords[u])-1][0]
            df_lon_lat = pd.DataFrame({'lon': [lon],
                                     'lat': [lat]})
            new_df.append(df_lon_lat)
        routes_destination_coords = pd.concat(new_df)



        ### ----- DESTINATIONS ---------------------------------- ##################################################
        ## transform the "destinations" table into a geodataframe
        geometry = [Point(xy) for xy in zip(routes_destination_coords.lon, routes_destination_coords.lat)]
        geo_destination_routes = GeoDataFrame(routes_destination, geometry=geometry, crs="EPSG:4326")  # CRS:3857
        gdf=geo_destination_routes

        ## find the extents of the map
        xmin, ymin, xmax, ymax = geo_destination_routes.total_bounds
        cell_size = 0.01  ## 1 km (0.01)
        grid_cells = []
        for x0 in np.arange(xmin, xmax + cell_size, cell_size):
            for y0 in np.arange(ymin, ymax + cell_size, cell_size):
                # bounds
                x1 = x0 - cell_size
                y1 = y0 + cell_size
                grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))
        cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                crs=gdf.crs)

        merged_full = gpd.sjoin(gdf, cell, how='left', op='within')
        ## remove geom
        merged = merged_full[['id_veh', 'id', 'tt',
                              'p_after', 'dist', 'hour', 'geometry',
                              'index_right']]

        # make a simple count variable that we can sum
        merged['n_vehicles'] = 1
        # Compute stats per grid cell -- aggregate number of vehicles to grid cells with dissolve
        dissolve = merged.dissolve(by="index_right", aggfunc="count")
        # aggregate by mean value the triptime, tripdistance and breaktime
        dissolve_means = merged.dissolve(by="index_right", aggfunc="mean")
        # put this into cells
        ## total number of vehicles within the grid

        #################################################################################################
        ##-------- total number of vehicles within the grid  --------------------------------------######
        #################################################################################################

        cell.loc[dissolve.index, 'n_vehicles'] = dissolve.n_vehicles.values
        ## ---->> save GRIDDED data ------------#####
        centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
        centroids = pd.DataFrame(centroids, columns=["x", "y"])
        gridded_data = pd.DataFrame({'x': centroids.x,
                                     'y': centroids.y,
                                     'z': cell.n_vehicles})
        ## remove none values
        gridded_data = gridded_data[gridded_data['z'].notna()]

        lista = []
        for i in range(len(gridded_data)):
            # print(centroids.x.iloc[i])
            stringa = str(
                "{lat:" + str(gridded_data.y.iloc[i]) + ", lng:" + str(gridded_data.x.iloc[i]) + ", count:" + str(
                    gridded_data.z.iloc[i]) + "}")
            # print(stringa)
            lista.append(stringa)
        joined_lista = (",".join(lista))
        joined_lista = str("[" + joined_lista + "]")

        #### send data direclty to the .html file....within tis session
        session["n_vehicles_destination"] = joined_lista
        # print(session["n_vehicles_destination"])

        ## save file
        with open(path_app + "static/gridded_n_vehicles_destination.txt", "w") as file:
            file.write(str(joined_lista))
        with open(path_app + "static/gridded_n_vehicles_destination.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gridded_destination_data = \n" + old)  # assign the "var name" in the .geojson file

        min_n_vehicles = min(gridded_data.z)
        max_n_vehicles = max(gridded_data.z)

        session["min_n_vehicles"] = min_n_vehicles
        session["max_n_vehicles"] = max_n_vehicles

        with open(path_app + "static/min_n_vehicles.txt", "w") as file:
            file.write(str(min_n_vehicles))
        with open(path_app + "static/min_n_vehicles.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var min_n_vehicles = \n" + old)  # assign the "var name" in the .geojson file
        with open(path_app + "static/max_n_vehicles.txt", "w") as file:
            file.write(str(max_n_vehicles))
        with open(path_app + "static/max_n_vehicles.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var max_n_vehicles = \n" + old)  # assign the "var name" in the .geojson file

        #################################################################################################
        ##-------- mean triptime within the grid  ------------------------------------------###########
        #################################################################################################
        cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                crs=gdf.crs)
        cell.loc[dissolve.index, 'tt'] = dissolve_means.tt.values
        ## ---->> save GRIDDED data ------------#####
        centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
        centroids = pd.DataFrame(centroids, columns=["x", "y"])
        gridded_data_triptime = pd.DataFrame({'x': centroids.x,
                                              'y': centroids.y,
                                              'z': cell.tt})
        ## remove none values
        gridded_data_triptime = gridded_data_triptime[gridded_data_triptime['z'].notna()]
        gridded_data_triptime.z = (gridded_data_triptime.z) / 60  ## triptime ---> minutes
        gridded_data_triptime['z'] = round(gridded_data_triptime.z, 0)
        gridded_data_triptime['z'] = gridded_data_triptime.z.astype('Int64')

        lista = []
        for i in range(len(gridded_data_triptime)):
            # print(centroids.x.iloc[i])
            stringa = str(
                "{lat:" + str(gridded_data_triptime.y.iloc[i]) + ", lng:" + str(
                    gridded_data_triptime.x.iloc[i]) + ", triptime:" + str(
                    gridded_data_triptime.z.iloc[i]) + "}")
            # print(stringa)
            lista.append(stringa)
        joined_lista = (",".join(lista))
        joined_lista = str("[" + joined_lista + "]")

        session["triptime_destination"] = joined_lista
        # print(session["triptime_destination"])

        ## save file
        with open(path_app + "static/gridded_triptime_destination.txt", "w") as file:
            file.write(str(joined_lista))
        with open(path_app + "static/gridded_triptime_destination.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gridded_destination_triptime = \n" + old)  # assign the "var name" in the .geojson file

        min_triptime = min(gridded_data_triptime.z)  ## minutes
        max_triptime = max(gridded_data_triptime.z)  ## minutes

        session["min_triptime"] = min_triptime
        session["max_triptime"] = max_triptime

        with open(path_app + "static/min_triptime.txt", "w") as file:
            file.write(str(min_triptime))
        with open(path_app + "static/min_triptime.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var min_triptime = \n" + old)  # assign the "var name" in the .geojson file
        with open(path_app + "static/max_triptime.txt", "w") as file:
            file.write(str(max_triptime))
        with open(path_app + "static/max_triptime.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var max_triptime = \n" + old)  # assign the "var name" in the .geojson file

        #################################################################################################
        ##-------- mean breaktime_s (stop time) within the grid  ----------------------------------######
        #################################################################################################
        cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                crs=gdf.crs)
        cell.loc[dissolve.index, 'p_after'] = dissolve_means.p_after.values
        ## ---->> save GRIDDED data ------------#####
        centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
        centroids = pd.DataFrame(centroids, columns=["x", "y"])
        gridded_data_breaktime = pd.DataFrame({'x': centroids.x,
                                               'y': centroids.y,
                                               'z': cell.p_after})
        ## remove none values
        gridded_data_breaktime = gridded_data_breaktime[gridded_data_breaktime['z'].notna()]
        gridded_data_breaktime.z = (gridded_data_breaktime.z) / 60  ## triptime ---> minutes
        gridded_data_breaktime = gridded_data_breaktime[gridded_data_breaktime.z < 2800]  ## max 48 hour stoptime
        gridded_data_breaktime['z'] = round(gridded_data_breaktime.z, 0)
        gridded_data_breaktime['z'] = gridded_data_breaktime.z.astype('Int64')

        lista = []
        for i in range(len(gridded_data_breaktime)):
            # print(centroids.x.iloc[i])
            stringa = str(
                "{lat:" + str(gridded_data_breaktime.y.iloc[i]) + ", lng:" + str(
                    gridded_data_breaktime.x.iloc[i]) + ", stoptime:" + str(
                    gridded_data_breaktime.z.iloc[i]) + "}")
            # print(stringa)
            lista.append(stringa)
        joined_lista = (",".join(lista))
        joined_lista = str("[" + joined_lista + "]")

        session["stoptime_destination"] = joined_lista
        # print(session["stoptime_destination"])

        ## save file
        with open(path_app + "static/gridded_stoptime_destination.txt", "w") as file:
            file.write(str(joined_lista))
        with open(path_app + "static/gridded_stoptime_destination.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gridded_destination_stoptime = \n" + old)  # assign the "var name" in the .geojson file

        min_stoptime = min(gridded_data_breaktime.z)  ## minutes
        max_stoptime = max(gridded_data_breaktime.z)  ## minutes

        session["min_stoptime"] = min_stoptime
        session["max_stoptime"] = max_stoptime

        with open(path_app + "static/min_stoptime.txt", "w") as file:
            file.write(str(min_stoptime))
        with open(path_app + "static/min_stoptime.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var min_stoptime = \n" + old)  # assign the "var name" in the .geojson file
        with open(path_app + "static/max_stoptime.txt", "w") as file:
            file.write(str(max_stoptime))
        with open(path_app + "static/max_stoptime.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var max_stoptime = \n" + old)  # assign the "var name" in the .geojson file

        #################################################################################################
        ##-------- mean tripdistance_m within the grid  -------------------------------------------######
        #################################################################################################
        cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                crs=gdf.crs)
        cell.loc[dissolve.index, 'dist'] = dissolve_means.dist.values
        ## ---->> save GRIDDED data ------------#####
        centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
        centroids = pd.DataFrame(centroids, columns=["x", "y"])
        gridded_data_tripdistance = pd.DataFrame({'x': centroids.x,
                                                  'y': centroids.y,
                                                  'z': cell.dist})
        ## remove none values
        gridded_data_tripdistance = gridded_data_tripdistance[gridded_data_tripdistance['z'].notna()]
        gridded_data_tripdistance.z = (gridded_data_tripdistance.z) / 1000  ## triditance ---> km
        gridded_data_tripdistance['z'] = round(gridded_data_tripdistance.z, 0)
        gridded_data_tripdistance['z'] = gridded_data_tripdistance.z.astype('Int64')

        lista = []
        for i in range(len(gridded_data_tripdistance)):
            # print(centroids.x.iloc[i])
            stringa = str(
                "{lat:" + str(gridded_data_tripdistance.y.iloc[i]) + ", lng:" + str(
                    gridded_data_tripdistance.x.iloc[i]) + ", tripdistance:" + str(
                    gridded_data_tripdistance.z.iloc[i]) + "}")
            # print(stringa)
            lista.append(stringa)
        joined_lista = (",".join(lista))
        joined_lista = str("[" + joined_lista + "]")

        session["tripdistance_destination"] = joined_lista
        # print(session["tripdistance_destination"])

        ## save file
        with open(path_app + "static/gridded_tripdistance_destination.txt", "w") as file:
            file.write(str(joined_lista))
        with open(path_app + "static/gridded_tripdistance_destination.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var gridded_destination_tripdistance = \n" + old)  # assign the "var name" in the .geojson file

        min_tripdistance = min(gridded_data_tripdistance.z)  ## minutes
        max_tripdistance = max(gridded_data_tripdistance.z)  ## minutes

        session["min_tripdistance"] = min_tripdistance
        session["max_tripdistance"] = max_tripdistance

        with open(path_app + "static/min_tripdistance.txt", "w") as file:
            file.write(str(min_tripdistance))
        with open(path_app + "static/min_tripdistance.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var min_tripdistance = \n" + old)  # assign the "var name" in the .geojson file
        with open(path_app + "static/max_tripdistance.txt", "w") as file:
            file.write(str(max_tripdistance))
        with open(path_app + "static/max_tripdistance.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var max_tripdistance = \n" + old)  # assign the "var name" in the .geojson file

        return render_template("index_heatmaps_FCD_selected.html",
                               session_n_vehicles_destination=session["n_vehicles_destination"],
                               session_triptime_destination=session["triptime_destination"],
                               session_stoptime_destination=session["stoptime_destination"],
                               session_tripdistance_destination=session["tripdistance_destination"])





from folium.plugins import HeatMap, HeatMapWithTime


@app.route('/timeline_heatmaps/', methods=['GET', 'POST'])
def timeline_heatmaps():
    return render_template("timeline_heatmaps_FCD.html")

@app.route('/timeline_heatmaps_hourly/', methods=['GET', 'POST'])
def animated_heatmaps():
    if request.method == "POST":
        ## declare a global variable
        global selected_FCD_heatmap_day
        selected_FCD_heatmap_day = datetime.datetime.strptime(
            request.form["FCD_day"], '%Y-%m-%d')

        selected_FCD_heatmap_day = selected_FCD_heatmap_day.strftime('%Y-%m-%d')
        selected_FCD_heatmap_day = str(selected_FCD_heatmap_day)
        print("selected_FCD_day:", selected_FCD_heatmap_day)

        ### set default day
        print("selected_FCD_day:", selected_FCD_heatmap_day)

        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool
        import matplotlib.pyplot as plt
        import shapely
        import numpy as np

        engine = create_engine("postgresql://postgres:superuser@192.168.134.36:5432/HAIG_ROMA")
        from sqlalchemy.sql import text

        query_destination = text('''WITH data AS(
                                        SELECT  
                                           idtrace_o, idtrace_d, breaktime_s, triptime_s, timedate_o, route_cinque.geom, route_cinque.idtrajectory, route_cinque.tripdistance_m,
                                           dataraw.latitude, dataraw.longitude, dataraw.idterm, dataraw.vehtype
                                           FROM route_cinque
                                           LEFT JOIN dataraw 
                                                       ON route_cinque.idtrace_d = dataraw.id      
                                                        WHERE date(route_cinque.timedate_o) = :x          
                                                         /*limit 1000*/
                                      )
                                        SELECT idterm, vehtype, timedate_o, idtrajectory,  latitude, longitude, triptime_s, breaktime_s, tripdistance_m,
                                        date_part('hour', timedate_o) as hour, geom,
                                        TO_CHAR(timedate_o::DATE, 'dd-mm-yyyy') as day
                                        from data     
                                        WHERE extract(hour from timedate_o) = :y ''')

        hour_index = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00', '08:00', '09:00', '10:00',
                      '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00',
                      '22:00', '23:00']

        ##--> initialize an empty list
        lista_N_vehicles = []
        lista_triptime = []
        lista_stoptime = []
        lista_tripdistance = []
        ### loop over the 24 hours------#########
        for i in range(24):
            print(i)
            stmt = query_destination.bindparams(x=str(selected_FCD_heatmap_day), y=str(i))
            with engine.connect() as conn:
                res = conn.execute(stmt).all()
            routes_destination = pd.DataFrame(res)
            geometry = [Point(xy) for xy in zip(routes_destination.longitude, routes_destination.latitude)]
            geo_destination_routes = GeoDataFrame(routes_destination, geometry=geometry, crs="EPSG:4326")  # CRS:3857
            gdf = geo_destination_routes.drop(columns=['geom'])
            gdf = geo_destination_routes.drop(columns=['longitude', 'latitude'])
            ## find the extents of the map
            xmin, ymin, xmax, ymax = geo_destination_routes.total_bounds
            # cell_size = 0.005 ## 500 meters
            cell_size = 0.01  ## 1 km (0.01)
            grid_cells = []
            for x0 in np.arange(xmin, xmax + cell_size, cell_size):
                for y0 in np.arange(ymin, ymax + cell_size, cell_size):
                    # bounds
                    x1 = x0 - cell_size
                    y1 = y0 + cell_size
                    grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))
            cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                    crs=gdf.crs)

            merged_full = gpd.sjoin(gdf, cell, how='left', op='within')
            ## remove geom
            merged = merged_full[['idterm', 'vehtype', 'idtrajectory', 'triptime_s',
                                  'breaktime_s', 'tripdistance_m', 'hour', 'geometry',
                                  'index_right']]
            # make a simple count variable that we can sum
            merged['n_vehicles'] = 1
            # Compute stats per grid cell -- aggregate number of vehicles to grid cells with dissolve
            dissolve = merged.dissolve(by="index_right", aggfunc="count")
            # aggregate by mean value the triptime, tripdistance and breaktime
            dissolve_means = merged.dissolve(by="index_right", aggfunc="mean")
            # put this into cells
            ## total number of vehicles within the grid
            cell.loc[dissolve.index, 'n_vehicles'] = dissolve.n_vehicles.values
            ## ---->> save GRIDDED data ------------#####
            centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
            centroids = pd.DataFrame(centroids, columns=["x", "y"])
            gridded_data = pd.DataFrame({'y': centroids.y,
                                         'x': centroids.x,
                                         'z': cell.n_vehicles})
            ## remove none values
            gridded_data = gridded_data[gridded_data['z'].notna()]

            data_vehicles = geo_destination_routes
            data_vehicles.latitude = round(data_vehicles.latitude, 2)  ## 1 km round
            data_vehicles.longitude = round(data_vehicles.longitude, 2)
            N_vehicles = data_vehicles.groupby(
                routes_destination[['longitude', 'latitude']].columns.tolist(),
                sort=False).size().reset_index().rename(columns={0: 'counts'})

            gridded_data = pd.DataFrame(
                {'y': N_vehicles['latitude'], 'x': N_vehicles['longitude'],
                 'z': N_vehicles['counts']})
            sub_lista_N_vehicles = gridded_data.values.tolist()
            lista_N_vehicles.append(sub_lista_N_vehicles)

            ########## ------------------------------ #######################
            ##########--- TRIP TIME ------------------#######################
            cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                    crs=gdf.crs)
            cell.loc[dissolve.index, 'triptime_s'] = dissolve_means.triptime_s.values
            ## ---->> save GRIDDED data ------------#####
            centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
            centroids = pd.DataFrame(centroids, columns=["x", "y"])
            gridded_data_triptime = pd.DataFrame({'y': centroids.y,
                                                  'x': centroids.x,
                                                  'z': cell.triptime_s})

            gridded_data_triptime = pd.DataFrame(geo_destination_routes[['latitude', 'longitude', 'triptime_s']])
            gridded_data_triptime = gridded_data_triptime[gridded_data_triptime['triptime_s'].notna()]
            gridded_data_triptime.triptime_s = (gridded_data_triptime.triptime_s) / 60
            gridded_data_triptime['triptime_s'] = round(gridded_data_triptime.triptime_s, 0)
            gridded_data_triptime['triptime_s'] = gridded_data_triptime.triptime_s.astype('Int64')
            gridded_data_triptime = pd.DataFrame(
                {'y': gridded_data_triptime['latitude'], 'x': gridded_data_triptime['longitude'],
                 'z': gridded_data_triptime['triptime_s']})

            sub_list_triptime = gridded_data_triptime.values.tolist()
            lista_triptime.append(sub_list_triptime)

            ########## ------------------------------ #######################
            ##########--- TRIP DISTANCE---------------#######################
            cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                    crs=gdf.crs)
            cell.loc[dissolve.index, 'tripdistance_m'] = dissolve_means.tripdistance_m.values
            ## ---->> save GRIDDED data ------------#####
            centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
            centroids = pd.DataFrame(centroids, columns=["x", "y"])
            gridded_data_tripdistance = pd.DataFrame({'y': centroids.y,
                                                      'x': centroids.x,
                                                      'z': cell.tripdistance_m})

            gridded_data_tripdistance = pd.DataFrame(
                geo_destination_routes[['latitude', 'longitude', 'tripdistance_m']])
            gridded_data_tripdistance = gridded_data_tripdistance[gridded_data_tripdistance['tripdistance_m'].notna()]
            gridded_data_tripdistance.triptime_s = (gridded_data_tripdistance.tripdistance_m) / 1000
            gridded_data_tripdistance['triptime_s'] = round(gridded_data_tripdistance.tripdistance_m, 0)
            gridded_data_tripdistance['triptime_s'] = gridded_data_tripdistance.tripdistance_m.astype('Int64')
            gridded_data_tripdistance = pd.DataFrame(
                {'y': gridded_data_tripdistance['latitude'], 'x': gridded_data_tripdistance['longitude'],
                 'z': gridded_data_tripdistance['tripdistance_m']})

            sub_list_tripdistance = gridded_data_tripdistance.values.tolist()
            lista_tripdistance.append(sub_list_tripdistance)

            ########## ------------------------------ #######################
            ##########--- STOP TIME ------------------#######################
            cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'],
                                    crs=gdf.crs)
            cell.loc[dissolve.index, 'breaktime_s'] = dissolve_means.breaktime_s.values
            ## ---->> save GRIDDED data ------------#####
            centroids = np.column_stack((cell.centroid.x, cell.centroid.y))
            centroids = pd.DataFrame(centroids, columns=["x", "y"])
            gridded_data_breaktime = pd.DataFrame({'y': centroids.y,
                                                   'x': centroids.x,
                                                   'z': cell.breaktime_s})

            gridded_data_breaktime = pd.DataFrame(geo_destination_routes[['latitude', 'longitude', 'breaktime_s']])
            gridded_data_breaktime = gridded_data_breaktime[gridded_data_breaktime['breaktime_s'].notna()]
            gridded_data_breaktime.breaktime_s = (gridded_data_breaktime.breaktime_s) / 60
            gridded_data_breaktime['breaktime_s'] = round(gridded_data_breaktime.breaktime_s, 0)
            gridded_data_breaktime['breaktime_s'] = gridded_data_breaktime.breaktime_s.astype('Int64')
            gridded_data_breaktime = pd.DataFrame(
                {'y': gridded_data_breaktime['latitude'], 'x': gridded_data_breaktime['longitude'],
                 'z': gridded_data_breaktime['breaktime_s']})

            sub_list_stoptime = gridded_data_breaktime.values.tolist()
            lista_stoptime.append(sub_list_stoptime)

        #################################################################################
        #################################################################################
        # create basemap ROMA N_Vehicles
        ave_LAT = 41.90368331095105
        ave_LON = 12.487932714627279
        my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                            tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
        #################################################################################

        HeatMapWithTime(lista_N_vehicles,
                        index=hour_index,
                        radius=25,
                        auto_play=True,
                        use_local_extrema=True
                        ).add_to(my_map)

        my_map.save(path_app + "templates/hourly_heatmap_ROMA_N_vehicles.html")

        #################################################################################
        #################################################################################
        # create basemap ROMA triptime
        ave_LAT = 41.90368331095105
        ave_LON = 12.487932714627279
        my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                            tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
        #################################################################################

        HeatMapWithTime(lista_triptime,
                        index=hour_index,
                        radius=40,
                        auto_play=True,
                        use_local_extrema=True
                        ).add_to(my_map)

        my_map.save(path_app + "templates/hourly_heatmap_ROMA_triptime.html")

        #################################################################################
        #################################################################################
        # create basemap ROMA tripdistance
        ave_LAT = 41.90368331095105
        ave_LON = 12.487932714627279
        my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                            tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
        #################################################################################

        HeatMapWithTime(lista_tripdistance,
                        index=hour_index,
                        radius=40,
                        auto_play=True,
                        use_local_extrema=True
                        ).add_to(my_map)

        my_map.save(path_app + "templates/hourly_heatmap_ROMA_tripdistance.html")

        #################################################################################
        #################################################################################
        # create basemap ROMA stoptime
        ave_LAT = 41.90368331095105
        ave_LON = 12.487932714627279
        my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11,
                            tiles='cartodbpositron')  # tiles='cartodbpositron',#'cartodbpositron', stamentoner , 'OpenStreetMap'
        #################################################################################

        HeatMapWithTime(lista_stoptime,
                        index=hour_index,
                        radius=50,
                        auto_play=True,
                        use_local_extrema=True
                        ).add_to(my_map)

        my_map.save(path_app + "templates/hourly_heatmap_ROMA_stoptime.html")

        #############################-----------------------------------------------------###########################
        ###### ------ modify html page for Number of Vehicles -------------------- ##################################
        with open(path_app + "templates/hourly_heatmap_ROMA_N_vehicles.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[32] = str(
                'header, nav { left: 2%; top: 85%; z-index: 700; position: absolute; text-align: center; margin: 20px 0; padding: 10px;}') + \
                       str(
                           'nav a {text-decoration: none; background: #000000;  border-radius: 5px;font-size: 1.2em; color: white;padding: 3px 8px;}') + \
                       str('nav .col_home {background-color: #6b0000;}') + \
                       str('nav .col_privata { background-color: #4CAF50;}') + \
                       str('nav .col_collettivo { background-color: #0000ff ;}') + \
                       str('nav .col_scenari { background-color: #ffa500 ;}') + \
                       str('nav .col_impatti { background-color: #76a5af ;}') + \
                       str(
                           " main {background-color: rgba(51, 170, 51, .3); left: 2%;	top: 10%; z-index: 700;	position: absolute;	margin: 2px 0;padding: 5px;	text-overflow:ellipsis; overflow:hidden; width: 280px;  height: 300px}") + \
                       str("main div { background: transparent;  color: white;  padding: 1px;  margin: 5px auto;}") + \
                       str("main div:nth-child(1) {width: 0px; height: 0px;  background: transparent;}") + \
                       str("main div:nth-child(3) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(4) {width: 270px;  background: red;	}") + \
                       str("main div:nth-child(5) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(6) { width: 270px; background: blue;}") + \
                       str("main div:nth-child(7) {width: 270px; background: blue;}") + \
                       str("main div:nth-child(10) {width: 270px;background: blue;}") + \
                       str(".inline-block-center {text-align: center;}") + \
                       str(".flex-center {display: flex;justify-content: center;}") + \
                       str("h2 {margin: 0; padding: 0;}") + \
                       str("h3 {margin: 0;padding: 0;font-family: Arial, Helvetica, sans-serif;font-weight: bold;}") + \
                       str(".animation_link {font-size: 130%;color: blue;font-weight: bold;} </style>")

        with open(path_app + 'templates/hourly_heatmap_ROMA_N_vehicles.html', 'w') as file:
            file.writelines(data)

        with open(path_app + "templates/hourly_heatmap_ROMA_N_vehicles.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[33] = str('<main class="inline-block-center"> \n') + \
                       str("<p><h3>Timeline Heatmaps</h3></p> \n") + \
                       str('<form method="POST" action="/animated_number_vehicles/">  \n') + \
                       str('<input class="animation_link" type="submit" value="Number of Vehicles" ></p> \n') + \
                       str('</form> \n') + \
                       str('<h3><i style="color:Tomato;">Spatial distribution of Number of Vehicles</i></h3> \n') + \
                       str('<br>') + \
                       str('<form method="POST" action="/animated_triptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip time"  ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_tripdistance/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip distance" ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_stoptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Stop time"></p> \n') + \
                       str('</form> \n') + \
                       str('</main>') + \
                       str("<nav role='navigation'>  \n") + \
                       str('<a class="col_home" href="/home_page/">Home</a> \n') + \
                       str(
                           '<a class="col_privata" href="/mob_privata_page/" style="color:#ffffff;">Private Mobility</a> \n') + \
                       str('<a class="col_collettivo" href="/public_transport_page/">Public Transport</a> \n') + \
                       str('<a class="col_scenari" href="/TRIP_LEGS/">Scenari</a> \n') + \
                       str('<a href="/charging_infrastructure_OSM/">Charging Profile</a> \n') + \
                       str('<a class="col_impatti" href="/public_transport_page/">Impatti</a> \n') + \
                       str('</nav> \n') + \
                       str(
                           '<script src="https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js"></script> \n')
        with open(path_app + 'templates/hourly_heatmap_ROMA_N_vehicles.html', 'w') as file:
            file.writelines(data)

        #############################-----------------------------------------------------###########################
        ###### ------ generate html page for trip time --------------------------- ##################################
        with open(path_app + "templates/hourly_heatmap_ROMA_triptime.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[32] = str(
                'header, nav { left: 2%; top: 85%; z-index: 700; position: absolute; text-align: center; margin: 20px 0; padding: 10px;}') + \
                       str(
                           'nav a {text-decoration: none; background: #000000;  border-radius: 5px;font-size: 1.2em; color: white;padding: 3px 8px;}') + \
                       str('nav .col_home {background-color: #6b0000;}') + \
                       str('nav .col_privata { background-color: #4CAF50;}') + \
                       str('nav .col_collettivo { background-color: #0000ff ;}') + \
                       str('nav .col_scenari { background-color: #ffa500 ;}') + \
                       str('nav .col_impatti { background-color: #76a5af ;}') + \
                       str(
                           " main {background-color: rgba(51, 170, 51, .3); left: 2%;	top: 10%; z-index: 700;	position: absolute;	margin: 2px 0;padding: 5px;	text-overflow:ellipsis; overflow:hidden; width: 280px;  height: 300px}") + \
                       str("main div { background: transparent;  color: white;  padding: 1px;  margin: 5px auto;}") + \
                       str("main div:nth-child(1) {width: 0px; height: 0px;  background: transparent;}") + \
                       str("main div:nth-child(3) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(4) {width: 270px;  background: red;	}") + \
                       str("main div:nth-child(5) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(6) { width: 270px; background: blue;}") + \
                       str("main div:nth-child(7) {width: 270px; background: blue;}") + \
                       str("main div:nth-child(10) {width: 270px;background: blue;}") + \
                       str(".inline-block-center {text-align: center;}") + \
                       str(".flex-center {display: flex;justify-content: center;}") + \
                       str("h2 {margin: 0; padding: 0;}") + \
                       str("h3 {margin: 0;padding: 0;font-family: Arial, Helvetica, sans-serif;font-weight: bold;}") + \
                       str(".animation_link {font-size: 130%;color: blue;font-weight: bold;} </style>")

        with open(path_app + 'templates/hourly_heatmap_ROMA_triptime.html', 'w') as file:
            file.writelines(data)

        with open(path_app + "templates/hourly_heatmap_ROMA_triptime.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[33] = str('<main class="inline-block-center"> \n') + \
                       str("<p><h3>Timeline Heatmaps</h3></p> \n") + \
                       str('<form method="POST" action="/animated_number_vehicles/">  \n') + \
                       str('<input class="animation_link" type="submit" value="Number of Vehicles" ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_triptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip time"  ></p> \n') + \
                       str('</form> \n') + \
                       str('<h3><i style="color:Tomato;">Spatial distribution of mean Triptime</i></h3> \n') + \
                       str('<br>') + \
                       str('<form method="POST" action="/animated_tripdistance/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip distance" ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_stoptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Stop time"></p> \n') + \
                       str('</form> \n') + \
                       str('</main>') + \
                       str("<nav role='navigation'>  \n") + \
                       str('<a class="col_home" href="/home_page/">Home</a> \n') + \
                       str(
                           '<a class="col_privata" href="/mob_privata_page/" style="color:#ffffff;">Private Mobility</a> \n') + \
                       str('<a class="col_collettivo" href="/public_transport_page/">Public Transport</a> \n') + \
                       str('<a class="col_scenari" href="/TRIP_LEGS/">Scenari</a> \n') + \
                       str('<a href="/charging_infrastructure_OSM/">Charging Profile</a> \n') + \
                       str('<a class="col_impatti" href="/public_transport_page/">Impatti</a> \n') + \
                       str('</nav> \n') + \
                       str(
                           '<script src="https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js"></script> \n')
        with open(path_app + 'templates/hourly_heatmap_ROMA_triptime.html', 'w') as file:
            file.writelines(data)

        #############################-----------------------------------------------------###########################
        ###### ------ generate html page for trip distance ----------------------- ##################################
        with open(path_app + "templates/hourly_heatmap_ROMA_tripdistance.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[32] = str(
                'header, nav { left: 2%; top: 85%; z-index: 700; position: absolute; text-align: center; margin: 20px 0; padding: 10px;}') + \
                       str(
                           'nav a {text-decoration: none; background: #000000;  border-radius: 5px;font-size: 1.2em; color: white;padding: 3px 8px;}') + \
                       str('nav .col_home {background-color: #6b0000;}') + \
                       str('nav .col_privata { background-color: #4CAF50;}') + \
                       str('nav .col_collettivo { background-color: #0000ff ;}') + \
                       str('nav .col_scenari { background-color: #ffa500 ;}') + \
                       str('nav .col_impatti { background-color: #76a5af ;}') + \
                       str(
                           "main {background-color: rgba(51, 170, 51, .3); left: 2%;	top: 10%; z-index: 700;	position: absolute;	margin: 2px 0;padding: 5px;	text-overflow:ellipsis; overflow:hidden; width: 280px;  height: 300px}") + \
                       str("main div { background: transparent;  color: white;  padding: 1px;  margin: 5px auto;}") + \
                       str("main div:nth-child(1) {width: 0px; height: 0px;  background: transparent;}") + \
                       str("main div:nth-child(3) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(4) {width: 270px;  background: red;	}") + \
                       str("main div:nth-child(5) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(6) { width: 270px; background: blue;}") + \
                       str("main div:nth-child(7) {width: 270px; background: blue;}") + \
                       str("main div:nth-child(10) {width: 270px;background: blue;}") + \
                       str(".inline-block-center {text-align: center;}") + \
                       str(".flex-center {display: flex;justify-content: center;}") + \
                       str("h2 {margin: 0; padding: 0;}") + \
                       str("h3 {margin: 0;padding: 0;font-family: Arial, Helvetica, sans-serif;font-weight: bold;}") + \
                       str(".animation_link {font-size: 130%;color: blue;font-weight: bold;} </style>")

        with open(path_app + 'templates/hourly_heatmap_ROMA_tripdistance.html', 'w') as file:
            file.writelines(data)

        with open(path_app + "templates/hourly_heatmap_ROMA_tripdistance.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[33] = str('<main class="inline-block-center"> \n') + \
                       str("<p><h3>Timeline Heatmaps</h3></p> \n") + \
                       str('<form method="POST" action="/animated_number_vehicles/">  \n') + \
                       str('<input class="animation_link" type="submit" value="Number of Vehicles" ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_triptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip time"  ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_tripdistance/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip distance" ></p> \n') + \
                       str('</form> \n') + \
                       str('<h3><i style="color:Tomato;">Spatial distribution of mean Tripdistance</i></h3> \n') + \
                       str('<br>') + \
                       str('<form method="POST" action="/animated_stoptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Stop time"></p> \n') + \
                       str('</form> \n') + \
                       str('</main>') + \
                       str("<nav role='navigation'>  \n") + \
                       str('<a class="col_home" href="/home_page/">Home</a> \n') + \
                       str(
                           '<a class="col_privata" href="/mob_privata_page/" style="color:#ffffff;">Private Mobility</a> \n') + \
                       str('<a class="col_collettivo" href="/public_transport_page/">Public Transport</a> \n') + \
                       str('<a class="col_scenari" href="/TRIP_LEGS/">Scenari</a> \n') + \
                       str('<a href="/charging_infrastructure_OSM/">Charging Profile</a> \n') + \
                       str('<a class="col_impatti" href="/public_transport_page/">Impatti</a> \n') + \
                       str('</nav> \n') + \
                       str(
                           '<script src="https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js"></script> \n')
        with open(path_app + 'templates/hourly_heatmap_ROMA_tripdistance.html', 'w') as file:
            file.writelines(data)

        #############################-----------------------------------------------------###########################
        ###### ------ generate html page for stop time  -------------------------- ##################################
        with open(path_app + "templates/hourly_heatmap_ROMA_stoptime.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[32] = str(
                'header, nav { left: 2%; top: 85%; z-index: 700; position: absolute; text-align: center; margin: 20px 0; padding: 10px;}') + \
                       str(
                           'nav a {text-decoration: none; background: #000000;  border-radius: 5px;font-size: 1.2em; color: white;padding: 3px 8px;}') + \
                       str('nav .col_home {background-color: #6b0000;}') + \
                       str('nav .col_privata { background-color: #4CAF50;}') + \
                       str('nav .col_collettivo { background-color: #0000ff ;}') + \
                       str('nav .col_scenari { background-color: #ffa500 ;}') + \
                       str('nav .col_impatti { background-color: #76a5af ;}') + \
                       str(
                           "main {background-color: rgba(51, 170, 51, .3); left: 2%;	top: 10%; z-index: 700;	position: absolute;	margin: 2px 0;padding: 5px;	text-overflow:ellipsis; overflow:hidden; width: 280px;  height: 300px}") + \
                       str("main div { background: transparent;  color: white;  padding: 1px;  margin: 5px auto;}") + \
                       str("main div:nth-child(1) {width: 0px; height: 0px;  background: transparent;}") + \
                       str("main div:nth-child(3) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(4) {width: 270px;  background: red;	}") + \
                       str("main div:nth-child(5) { width: 270px; background: transparent;	}") + \
                       str("main div:nth-child(6) { width: 270px; background: blue;}") + \
                       str("main div:nth-child(7) {width: 270px; background: blue;}") + \
                       str("main div:nth-child(10) {width: 270px;background: blue;}") + \
                       str(".inline-block-center {text-align: center;}") + \
                       str(".flex-center {display: flex;justify-content: center;}") + \
                       str("h2 {margin: 0; padding: 0;}") + \
                       str("h3 {margin: 0;padding: 0;font-family: Arial, Helvetica, sans-serif;font-weight: bold;}") + \
                       str(".animation_link {font-size: 130%;color: blue;font-weight: bold;} </style>")

        with open(path_app + 'templates/hourly_heatmap_ROMA_stoptime.html', 'w') as file:
            file.writelines(data)

        with open(path_app + "templates/hourly_heatmap_ROMA_stoptime.html", 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            data[33] = str('<main class="inline-block-center"> \n') + \
                       str("<p><h3>Timeline Heatmaps</h3></p> \n") + \
                       str('<form method="POST" action="/animated_number_vehicles/">  \n') + \
                       str('<input class="animation_link" type="submit" value="Number of Vehicles" ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_triptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip time"  ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_tripdistance/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Trip distance" ></p> \n') + \
                       str('</form> \n') + \
                       str('<form method="POST" action="/animated_stoptime/"> \n') + \
                       str('<input class="animation_link" type="submit" value="Stop time"></p> \n') + \
                       str('</form> \n') + \
                       str('<h3><i style="color:Tomato;">Spatial distribution of mean Stoptime</i></h3> \n') + \
                       str('<br>') + \
                       str('</main>') + \
                       str("<nav role='navigation'>  \n") + \
                       str('<a class="col_home" href="/home_page/">Home</a> \n') + \
                       str(
                           '<a class="col_privata" href="/mob_privata_page/" style="color:#ffffff;">Private Mobility</a> \n') + \
                       str('<a class="col_collettivo" href="/public_transport_page/">Public Transport</a> \n') + \
                       str('<a class="col_scenari" href="/TRIP_LEGS/">Scenari</a> \n') + \
                       str('<a href="/charging_infrastructure_OSM/">Charging Profile</a> \n') + \
                       str('<a class="col_impatti" href="/public_transport_page/">Impatti</a> \n') + \
                       str('</nav> \n') + \
                       str(
                           '<script src="https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js"></script> \n')
        with open(path_app + 'templates/hourly_heatmap_ROMA_stoptime.html', 'w') as file:
            file.writelines(data)

        data_timeline = [{
            'FCD_day': selected_FCD_heatmap_day,
            'hour': 'choose hour'
        }]

        ##### render timeline heatmap @ first interrogation.....
        return render_template("hourly_heatmap_ROMA_N_vehicles.html", data_timeline=data_timeline)


@app.route('/animated_number_vehicles/', methods=['GET', 'POST'])
def animated_number_vehicles():
    data_number_vehicles = [{
        'FCD_day': selected_FCD_heatmap_day,
        'hour': 'choose hour'
    }]
    return render_template("hourly_heatmap_ROMA_N_vehicles.html", data_number_vehicles=data_number_vehicles)


@app.route('/animated_triptime/', methods=['GET', 'POST'])
def animated_triptime():
    data_triptime = [{
        'FCD_day': selected_FCD_heatmap_day,
        'hour': 'choose hour'
    }]
    return render_template("hourly_heatmap_ROMA_triptime.html", data_triptime=data_triptime)


@app.route('/animated_tripdistance/', methods=['GET', 'POST'])
def animated_tripdistance():
    data_tripdistance = [{
        'FCD_day': selected_FCD_heatmap_day,
        'hour': 'choose hour'
    }]
    return render_template("hourly_heatmap_ROMA_tripdistance.html", data_tripdistance=data_tripdistance)


@app.route('/animated_stoptime/', methods=['GET', 'POST'])
def animated_stoptime():
    data_stoptime = [{
        'FCD_day': selected_FCD_heatmap_day,
        'hour': 'choose hour'
    }]
    return render_template("hourly_heatmap_ROMA_stoptime.html", data_stoptime=data_stoptime)


###################################################################################
###################################################################################
###################################################################################
########### Charging Infrastructure ###############################################
####-------- real time data from Open Charge Map -------------#####################

@app.route('/charging_infrastructure_OSM/', methods=['GET', 'POST'])
def charging_infrastructure_OSM():

    import glob

    session['dow_type'] = 13
    session["emission_type"] = 13 ### nox
    session["costs_type"] = 113
    session["external_type"] = 211
    session["fleet_type"] = 21

    stored_dow_files = glob.glob(path_app + "static/params/selected_DOW_*.txt")
    stored_dow_files.sort(key=os.path.getmtime)
    stored_dow_file = stored_dow_files[len(stored_dow_files) - 1]
    with open(stored_dow_file) as file:
        selected_dow = file.read()
    print("selected_dow-------I AM HERE-----------: ", selected_dow)
    session["dow_type"] = selected_dow
    print(session["dow_type"])

    return render_template("index_zmu_recharge_select_day.html")





@app.route('/dow_selector/', methods=['GET', 'POST'])
def dow_selector():
    import glob

    # selected_dow = 11

    if request.method == "POST":
        session["dow_type"] = request.form.get("dow_type")
        selected_dow = session["dow_type"]
        print("selected_dow:", selected_dow)
        selected_dow = str(selected_dow)
        print("i am here")

        selected_dow = int(selected_dow)
        if selected_dow == 17:
            dow = "0"
            print("Sunday")
        elif selected_dow == 11:
            dow = "1"
            print("Monday")
        elif selected_dow == 12:
            dow = "2"
            print("Tuesday")
        elif selected_dow == 13:
            dow = "3"
            print("Wednesday")
        elif selected_dow == 14:
            dow = "4"
            print("Thursday")
        elif selected_dow == 15:
            dow = "5"
            print("Friday")
        elif selected_dow == 16:
            dow = "6"
            print("Saturday")

        print("day of the week------:", selected_dow)

        with open(path_app + "static/params/selected_DOW_" + session.sid + ".txt", "w") as file:
            file.write(str(selected_dow))

        ### -----> make QUERY of RECHARGE DATA --- or read input data ----##############################
        #### ------------------------ ###############
        ## switch to table.........TRIPS----FCD data
        from sqlalchemy import create_engine
        from sqlalchemy import exc
        import sqlalchemy as sal
        from sqlalchemy.pool import NullPool

        engine = create_engine("postgresql://federico:pippo75@192.168.132.222:5432/RSM_Oct_Nov_2022")
        from sqlalchemy.sql import text

        query_recharge_profiles_fcd = text(''' SELECT * FROM recharge.recharge_profiles_fcd
                                                     WHERE dow = :yy ''')

        stmt = query_recharge_profiles_fcd.bindparams(yy=str(dow))

        with engine.connect() as conn:
            res = conn.execute(stmt).all()
        df_steps_recharge = pd.DataFrame(res)

        ### ---> save .csv file
        df_steps_recharge.to_csv(path_app + 'static/recharge_steps_' +  session.sid + '.csv')

        ### ------- >>> aggregate by zones <<<<--- #####################################################
        ## ---->>> make aggregation by ENERGY and zmu <<<<--------- ################################
        aggr_steps_recharge = df_steps_recharge[['zmu', 'energy', 'index_zmu']].groupby(['zmu', 'index_zmu'],
                                                 sort=False).sum().reset_index()
        aggr_steps_recharge['energy'] = round(aggr_steps_recharge.energy, ndigits=4)


        ## function to transform Geometry from text to LINESTRING
        def wkb_tranformation(line):
            return wkb.loads(line.geom, hex=True)


        ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
        ZMU_ROMA = gpd.GeoDataFrame(ZMU_ROMA)
        aggr_steps_recharge = pd.merge(aggr_steps_recharge, ZMU_ROMA, on=['zmu', 'index_zmu'], how='left')
        aggr_steps_recharge['index_zmu'] = aggr_steps_recharge.index_zmu.astype('int')
        aggr_steps_recharge = aggr_steps_recharge[['zmu','energy', 'index_zmu',
                        'POP_TOT_ZMU', 'nome_comun', 'quartiere', 'geometry']]

        try:
            aggr_steps_recharge = gpd.GeoDataFrame(aggr_steps_recharge)
        except IndexError:
            abort(404)

        ## save as .geojson file
        ### ---- RECHARGE  <---- ##############
        aggr_steps_recharge.to_file(filename=path_app + 'static/steps_recharge.geojson',
                                        driver='GeoJSON')

        ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
        with open(path_app + "static/steps_recharge.geojson", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var aggregated_recharge_zmu = \n" + old)  # assign the "var name" in the .geojson file

        ##### --->>>>>> make the sessions data...<<<------------############################################
        ### convert Geodataframe into .geojson...
        session["aggregated_recharge"] = aggr_steps_recharge.to_json()

        return render_template("index_zmu_recharge_select_dow.html")





##--->> HISTOGRAMS for RECHARGE ------ ####################################################
@app.route('/figure30')
def figure_plotly30():
    import plotly.express as px
    ##---->>> make time series plotly.....-------------#######################
    ### ---> get filtered data of ZMU from csv file  <--- ###########################
    df_steps_recharge = pd.read_csv(path_app + 'static/recharge_steps_' + session.sid + '.csv')

    ##----> filter by day and ZMU zone....
    ## read back zmu index
    with open(path_app + "static/params/index_zmu_" + session.sid + ".txt") as f:
        lines = f.readlines()

    """   
    #### ----- to use in LINUX (Apache 2) ----------##########
    line = ((lines[0]).split(':'))[1]
    import re
    line = re.sub('}\n', '', line)
    selected_index_zmu = line
    #### ----------------------------------------- ###########
    """
    ## string split and get value....

    selected_index_zmu = ((lines[1]).split())[1]
    print("selected_index_zmu: ", selected_index_zmu)
    selected_index_zmu = int(float(selected_index_zmu))

    filtered_ZMU = df_steps_recharge[(df_steps_recharge.index_zmu == selected_index_zmu)]
    filtered_ZMU.sort_values('time_steps', ascending=True, inplace=True)

    fig = px.bar(filtered_ZMU, x='time_steps', y="power", color="power_type", labels={"power": "power(kW)"} ,
                 color_discrete_map={
                     'Ot': 'yellow',
                     'Hm': 'blue',
                     'Hs': 'red'
                 },
                 title="Power Temporal Profile (kW)")


    fig.update_yaxes(range=[0, 2*max(filtered_ZMU.power)])
    ##----> delete files within the folder "/templates/plotly_plots. ---######
    import os
    import glob
    files_to_remove = glob.glob(path_app + 'templates/plotly_recharge/*')
    for f in files_to_remove:
        os.remove(f)
    import random
    x = random.randint(0, 10000)
    fig.write_html(path_app + 'templates/plotly_recharge/hourly_steps' + str(x) + '_recharge.html')
    return render_template('plotly_recharge/hourly_steps' + str(x) + '_recharge.html')




@app.route('/download_charging_infrastructure_OSM/', methods=['GET', 'POST'])
def download_charging_stations():
    # link_OCM_full_data_IT = "https://api.openchargemap.io/v3/poi?key=72622769-c655-4c2a-b18f-e58eef38c0f3/output=json&countrycode=IT&maxresults=300000&compact=true&verbose=false&includecomments=true"
    link_OCM_full_data_IT = "https://api.openchargemap.io/v3/poi/?output=json&countrycode=IT&maxresults=3000000&compact=true&verbose=false&includecomments=true?key=72622769-c655-4c2a-b18f-e58eef38c0f3"

    link = link_OCM_full_data_IT
    f = requests.get(link)
    open(path_app + "static/CI_Italy_OCM_full.json", "wb").write(f.content)

    json_data = open(path_app + 'static/CI_Italy_OCM_full.json', encoding="utf8")
    data_json = json.load(json_data)
    len(data_json)

    ### initialize an empty dataframe
    chargers = pd.DataFrame([])

    for idx, data in enumerate(data_json):
        # print(idx)
        ## add according the number of points
        for i in range((len(data["Connections"]))):
            # try:
            # print(i)
            Lat = data["AddressInfo"]['Latitude']
            Lon = data["AddressInfo"]['Longitude']
            try:
                city = data["AddressInfo"]['Town']
            except KeyError:
                city = "not avaialble"
            ID = data["AddressInfo"]['ID']
            try:
                Operator = data["AddressInfo"]['Title']
            except TypeError:
                Operator = "not avaialble"
            try:
                points = data["NumberOfPoints"]
            except KeyError:
                points = "not avaialble"
            if (len(data["Connections"])) == 1:
                Connection_ID = data["Connections"][0]["ID"]
                Connection_TypeID = data["Connections"][0]["ConnectionTypeID"]
                # Connection_Type = data["Connections"][0]["ConnectionType"]
                try:
                    Power = data["Connections"][0]["PowerKW"]
                except KeyError:
                    Power = "not available"
            else:
                Connection_ID = data["Connections"][i]["ID"]
                Connection_TypeID = data["Connections"][i]["ConnectionTypeID"]
                # Connection_Type = data["Connections"][i]["ConnectionType"]
                try:
                    Power = data["Connections"][i]["PowerKW"]
                except KeyError:
                    Power = "not available"

            ## build a dataframe
            df_charger = pd.DataFrame({'OperatorInfo': [Operator],
                                       'NumberOfPoints': [points],
                                       'ID': [ID],
                                       'latitude': [Lat],
                                       'longitude': [Lon],
                                       'city': [city],
                                       'Connection_TypeID': [Connection_TypeID],
                                       # 'Connection_Type': [Connection_Type],
                                       'Connection_ID': [Connection_ID],
                                       'Power': [Power],
                                       })
            # chargers = chargers.append(df_charger)
            chargers = pd.concat([chargers, df_charger])
            # except IndexError:
            #    pass

    ## make a Geodataframe....
    geometry = [Point(xy) for xy in zip(chargers.longitude, chargers.latitude)]
    crs = {'init': 'epsg:4326'}
    chargers_gdf = GeoDataFrame(chargers, crs=crs, geometry=geometry)
    # save first as geojson file
    chargers_gdf.to_file(filename=path_app + 'static/chargers_OCM.geojson', driver='GeoJSON')
    chargers_gdf.to_file(filename=path_app + 'static/chargers_OCM_for_routing.geojson', driver='GeoJSON')

    ## add "var name" in front of the .geojson file, in order to properly load it into the index.html file
    with open(path_app + "static/chargers_OCM.geojson", "r+", encoding="utf8") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var EV_chargers_OCM = \n" + old)  # assign the "var name" in the .geojson file

    ## ---->>> make intersection with ZMUs
    # get ZMU containing the all AMENITY locations
    # ZMU_ROMA = gpd.read_file(path_app + "static/zmu_roma_index.geojson")
    ZMU_ROMA = gpd.read_file(path_app + "static/zmu_aggregated_POP_ROMA_2015_new.geojson")
    ZMU_ROMA = ZMU_ROMA.set_crs('epsg:4326')
    chargers_gdf = chargers_gdf.set_crs('epsg:4326', allow_override=True)
    chargers_gdf['charging_stations'] = 1
    chargers_ZMU = gpd.sjoin(ZMU_ROMA, chargers_gdf, how='inner',
                             predicate='intersects')
    chargers_ZMU = pd.DataFrame(chargers_ZMU)

    chargers_ZMU.to_csv(path_app + 'static/network_chargers_ZMU.csv')

    ##---> group by charging points and ZMUs
    ## get number of charging stations by ZMU zone

    ## ---> find list of "lines" or "routes" passy by each "stop_id"
    def agg(g):
        return pd.Series({
            'Available_Power': [*g['Power'].unique()],
            'n_charging_stations': g.groupby('zmu').size().reset_index()
        })

    aggr_chargers_ZMU = chargers_ZMU.groupby(['zmu']).apply(agg)
    aggr_chargers_ZMU = aggr_chargers_ZMU.reset_index()

    list_charging_stations = []
    df_aggr_chargers_ZMU = pd.DataFrame(aggr_chargers_ZMU.n_charging_stations)
    for i in range(len(df_aggr_chargers_ZMU)):
        # print(aggr_chargers_ZMU.n_charging_stations[i][0][0])
        list_charging_stations.append(aggr_chargers_ZMU.n_charging_stations[i][0][0])
    aggr_chargers_ZMU['n_charging_stations'] = list_charging_stations

    ## merge with ZMU_ROMA
    aggr_chargers_ZMU = pd.merge(aggr_chargers_ZMU, ZMU_ROMA, on=['zmu'], how='right')
    aggr_chargers_ZMU.to_csv(path_app + 'static/aggr_network_chargers_ZMU.csv')
    ## save to .geojson file
    aggr_chargers_ZMU = gpd.GeoDataFrame(aggr_chargers_ZMU)
    ## save .geojson file
    with open(path_app + 'static/charging_stations_ZMU.geojson', 'w') as f:
        f.write(aggr_chargers_ZMU.to_json())
    ## add "var name" in front of the .geojson file, in order to properly loat it into the index.html file
    with open(path_app + "static/charging_stations_ZMU.geojson", "r+") as f:
        old = f.read()  # read everything in the file
        f.seek(0)  # rewind
        f.write("var charging_data = \n" + old)  # assign the "var name" in the .geojson file

    return render_template("index_EV_chargers.html")


@app.route('/coords_OSM/', methods=['GET', 'POST'])
def coords_OSM():
    if request.method == 'POST':
        # Then get the data from the form
        tag = request.form['tag']
        lat = request.form['lat']
        lng = request.form['lng']
        print("input:", tag)
        print("lat, lon---->:", lat, lng)
        markers = [
            {
                'lat': lng,
                'lon': lat,
                'popup': tag
            }
        ]
        print(markers)
        # return(lat, lng)
        return render_template("index_EV_chargers.html", longitude=lng, latitude=lat)




#######################################################################################################
#######################################################################################################
############# ----------- SIMULATE Origin ---> Destination PATH for private Vehicles ---- #############
###########////////////////////////////////////////////////////////////////////////////////############


@app.route('/OD_path_vehicle/', methods=['GET', 'POST'])
def OD_path_vehicle():

    return render_template("index_OD_path_vehicles_OD_names.html")


##--->>>*** insert the NAME of THE LOCATION as ORIGIN
@app.route('/insert_ORIGIN_name/', methods=['GET', 'POST'])
def insert_ORIGIN_name():
    session["name_ORIGIN_location"] = request.form.get("name_ORIGIN_location")
    print("name---->:", session["name_ORIGIN_location"])
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="MyApp")
    geolocator = Nominatim(user_agent="my_request")
    try:
        location = geolocator.geocode(session["name_ORIGIN_location"] + ",Roma Capitale, Lazio, 00187, Italia")
    except:
        location = geolocator.geocode(session["name_ORIGIN_location"] + ",Roma Capitale, Lazio, Italia")
    print("----ORIGIN LOCATION:", location)
    if location == None:
        abort(404)
    print("-----------The latitude of the ORIGIN location is: ", location.latitude)
    print("-----------The longitude of the ORIGIN location is: ", location.longitude)
    session["lat_ORIGIN"] = location.latitude
    session["lon_ORIGIN"] = location.longitude
    print("lat_ORIGIN, lon_ORIGIN:", session["lat_ORIGIN"], session["lon_ORIGIN"])

    ## make a .geojson file with the ORIGIN location POINT (see below...)
    df_ORIGIN_point = pd.DataFrame({'latitude': [session["lat_ORIGIN"]],
                                    'longitude': [session["lon_ORIGIN"]]
                                    })

    ####-----> make a Geodataframe....with ORIGIN POINT
    geometry = [Point(xy) for xy in zip(df_ORIGIN_point.longitude, df_ORIGIN_point.latitude)]
    crs = {'init': 'epsg:4326'}
    gdf_df_ORIGIN_point = GeoDataFrame(df_ORIGIN_point, crs=crs, geometry=geometry)
    ## transform geodataframeo into .geojson
    ORIGIN_point_json = gdf_df_ORIGIN_point.to_json()
    # print("ORIGIN_point_json:", ORIGIN_point_json)

    data_location_ORIGIN = [{
        'Origin': session["name_ORIGIN_location"],
        'Destination': '--choose destination--'
    }]

    session["ORIGIN_point"] = ORIGIN_point_json
    # print(session["ORIGIN_point"])

    return render_template("index_OD_path_vehicles_ORIGIN_point.html", data_location_ORIGIN=data_location_ORIGIN,
                           session_ORIGIN_point=session["ORIGIN_point"])


##à--->>>*** insert the NAME of THE LOCATION as DESTINATION
@app.route('/insert_DESTINATION_name/', methods=['GET', 'POST'])
def insert_DESTINATION_name():
    try:
        name_ORIGIN_location = session["name_ORIGIN_location"]
        print("name_ORIGIN_location:", name_ORIGIN_location)
    except AttributeError:
        abort(404)

    session["name_DESTINATION_location"] = request.form.get("name_DESTINATION_location")
    print("name---->:", session['name_DESTINATION_location'])
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="MyApp")
    try:
        location = geolocator.geocode(session["name_DESTINATION_location"] + ",Roma Capitale, Lazio, 00187, Italia")
    except:
        location = geolocator.geocode(session["name_DESTINATION_location"] + ",Roma Capitale, Lazio, Italia")
    print("----DESTINATION LOCATION:", location)
    if location == None:
        abort(404)
    print("-----------The latitude of the DESTINATION location is: ", location.latitude)
    print("-----------The longitude of the DESTINATION location is: ", location.longitude)

    session["lat_DESTINATION"] = location.latitude
    session["lon_DESTINATION"] = location.longitude
    print("lat_DESTINATION, lon_DESTINATION:", session["lat_DESTINATION"], session["lon_DESTINATION"])

    ## make a .geojson file with the DESTINATION location POINT (see below...)
    df_DESTINATION_point = pd.DataFrame({'latitude': [session["lat_DESTINATION"]],
                                         'longitude': [session["lon_DESTINATION"]]
                                         })

    ####-----> make a Geodataframe....with ORIGIN POINT
    geometry = [Point(xy) for xy in zip(df_DESTINATION_point.longitude, df_DESTINATION_point.latitude)]
    crs = {'init': 'epsg:4326'}
    gdf_df_DESTINATION_point = GeoDataFrame(df_DESTINATION_point, crs=crs, geometry=geometry)
    ## transform geodataframeo into .geojson
    DESTINATION_point_json = gdf_df_DESTINATION_point.to_json()
    # print("ORIGIN_point_json:", ORIGIN_point_json)

    ## make a .geojson file with the DESTINATION location POINT (see below...)

    data_location_DESTINATION = [{
        'Origin': session["name_ORIGIN_location"],
        'Destination': session["name_DESTINATION_location"]
    }]

    session["DESTINATION_point"] = DESTINATION_point_json

    return render_template("index_OD_path_vehicles_DESTINATION_point.html",
                           data_location_DESTINATION=data_location_DESTINATION,
                           session_ORIGIN_point=session["ORIGIN_point"],
                           session_DESTINATION_point=session["DESTINATION_point"])


@app.route('/OD_path_vehicle_dijkstra/', methods=['GET', 'POST'])
def OD_path_vehicle_select():
    from center_map import center, cost_assignment, get_pos
    import time

    try:
        name_ORIGIN_location = session["name_ORIGIN_location"]
        print("name_ORIGIN_location:", name_ORIGIN_location)
    except AttributeError:
        abort(404)

    try:
        name_DESTINATION_location = session["name_DESTINATION_location"]
        print("name_DESTINATION_location:", name_DESTINATION_location)
    except AttributeError:
        abort(404)

    try:
        lat_ORIGIN = session["lat_ORIGIN"]
        print("lat_ORIGIN:", lat_ORIGIN)
    except AttributeError:
        abort(404)

    try:
        lon_ORIGIN = session["lon_ORIGIN"]
        print("lon_ORIGIN:", lon_ORIGIN)
    except AttributeError:
        abort(404)

    try:
        lat_DESTINATION = session["lat_DESTINATION"]
        print("lat_DESTINATION:", lat_DESTINATION)
    except AttributeError:
        abort(404)

    try:
        lon_DESTINATION = session["lon_DESTINATION"]
        print("lon_DESTINATION:", lon_DESTINATION)
    except AttributeError:
        abort(404)

    try:
        if (lat_ORIGIN != lat_DESTINATION) & (lon_ORIGIN != lon_DESTINATION):
            # lat_ORIGIN = 41.9580
            # lon_ORIGIN = 12.4585

            # lat_DESTINATION = 41.8399
            # lon_DESTINATION = 12.6858

            ## get extent of data
            ext = 0.025
            ## bottom-left corner
            p1 = Point(min(lon_ORIGIN, lon_DESTINATION) - ext, min(lat_ORIGIN, lat_DESTINATION) - ext)
            ## bottom-right corner
            p2 = Point(max(lon_ORIGIN, lon_DESTINATION) + ext, min(lat_ORIGIN, lat_DESTINATION) - ext)
            ## top-right corner
            p3 = Point(max(lon_ORIGIN, lon_DESTINATION) + ext, max(lat_ORIGIN, lat_DESTINATION) + ext)
            ## top-left corner
            p4 = Point(min(lon_ORIGIN, lon_DESTINATION) - ext, max(lat_ORIGIN, lat_DESTINATION) + ext)

            def polygon():
                poly = Polygon([(min(lon_ORIGIN, lon_DESTINATION) - ext, min(lat_ORIGIN, lat_DESTINATION) - ext),
                                (max(lon_ORIGIN, lon_DESTINATION) + ext, min(lat_ORIGIN, lat_DESTINATION) - ext),
                                (max(lon_ORIGIN, lon_DESTINATION) + ext, max(lat_ORIGIN, lat_DESTINATION) + ext),
                                (min(lon_ORIGIN, lon_DESTINATION) - ext, max(lat_ORIGIN, lat_DESTINATION) + ext)])
                return poly

            polygon()
            time.sleep(2)
            ## set a session state of the "grafo" to be available in all pages
            grafo = ox.graph_from_polygon(polygon(), network_type='drive')
        cost_assignment(grafo)
        ## get geodataframes for nodes and edges
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(grafo)
        ## get nearest node to the Origin & Destination points
        nearest_node_ORIGIN, distance_ORIGIN = ox.nearest_nodes(grafo, lon_ORIGIN, lat_ORIGIN,
                                                                return_dist=True)
        nearest_node_DESTINATION, distance_DESTINATION = ox.nearest_nodes(grafo, lon_DESTINATION,
                                                                          lat_DESTINATION,
                                                                          return_dist=True)

        try:
            ## find shortest path based on the "cost" (time)
            init_shortest_OD_path_cost = nx.shortest_path(grafo, nearest_node_ORIGIN,
                                                          nearest_node_DESTINATION,
                                                          weight='cost')  # using cost (time)
            path_edges = list(zip(init_shortest_OD_path_cost, init_shortest_OD_path_cost[1:]))
            lr = nx.shortest_path_length(grafo, nearest_node_ORIGIN, nearest_node_DESTINATION,
                                         weight='cost')  ## this is a time
            lunghezza = []
            if lr != 0:
                for l in path_edges:
                    lunghezza.append(grafo[l[0]][l[1]][0][
                                         'length'])  # get only the length for each arch between 2 path edges, [0] it the key = 0

                LENGTH = round(sum(lunghezza) / 1000, 2)
                TRAVEL_TIME = round(lr / 3600, 2)
                MEAN_SPEED = round(sum(lunghezza) / 1000 / lr * 3600, 2)
                session['path_length'] = LENGTH
                session['travel_time'] = TRAVEL_TIME
                session['mean_speed'] = MEAN_SPEED
                print("### Length(km):{0:.3f} - Travel time(h):{1:.3f} - Mean Speed(km/h):{2:.0f}".format(LENGTH,
                                                                                                          TRAVEL_TIME,
                                                                                                          MEAN_SPEED))
                ## update MAP with paths
                df_nodes = pd.DataFrame(path_edges)
                df_nodes.columns = ['u', 'v']
                ## merge 'df_nodes' with 'gdf_edges'
                edges_shortest_route_cost = pd.merge(df_nodes, gdf_edges, on=['u', 'v'],
                                                     how='left')
                edges_shortest_route_cost = gpd.GeoDataFrame(edges_shortest_route_cost)
                edges_shortest_route_cost.drop_duplicates(['u', 'v'], inplace=True)
                edges_shortest_route_cost = edges_shortest_route_cost[['geometry']]

                ## save "edges_shortest_route_cost" as geojson file:
                edges_shortest_route_cost_gdf = gpd.GeoDataFrame(edges_shortest_route_cost)

                ## transform geodataframeo into .geojson
                edges_shortest_route_cost_json = edges_shortest_route_cost.to_json()
                # print("edges_shortest_route_cost_gdf_json:", edges_shortest_route_cost_gdf_json)

                session["route_cost"] = edges_shortest_route_cost_json
                print("------route_cost-----------:", session["route_cost"])

                edges_shortest_route_cost['LENGTH'] = LENGTH
                edges_shortest_route_cost['TRAVEL_TIME'] = TRAVEL_TIME
                edges_shortest_route_cost['MEAN_SPEED'] = MEAN_SPEED

                ####################################################################################
                ### create basemap (Roma)
                ave_LAT = 41.888009265234906
                ave_LON = 12.500281904062206
                my_map = folium.Map([ave_LAT, ave_LON], zoom_start=11, tiles='cartodbpositron')
                ####################################################################################
                # save first as geojson file
                edges_shortest_route_cost_gdf.geometry.to_file(filename=path_app + 'static/OD_path_vehicle.geojson',
                                                               driver='GeoJSON')
                folium.GeoJson(path_app + 'static/OD_path_vehicle.geojson').add_to((my_map))
                my_map.save(path_app + "static/OD_path_vehicle.html")

                my_map.save(path_app + "static/OD_path_vehicle.html")

        except (nx.NodeNotFound, nx.exception.NetworkXNoPath):
            print('O-->D NodeNotFound', 'Origin:', nearest_node_ORIGIN, 'Destination:', nearest_node_DESTINATION)

    except IndexError:
        pass
    except NameError:
        st.write("### ---> choose an Origin and Destination")

    data_path = [{
        'Journey_length': session["path_length"],
        'Travel_time': session["travel_time"],
        'Mean_speed': session["mean_speed"]
    }]

    return render_template("index_OD_vehicle_PATH.html",
                           session_ORIGIN_point=session["ORIGIN_point"],
                           session_DESTINATION_point=session["DESTINATION_point"],
                           session_route_cost=session["route_cost"],
                           session_path_length=session['path_length'],
                           sesison_travel_time=session['travel_time'],
                           session_mean_speed=session['mean_speed'],
                           data_path=data_path)


##################################################################################################################
##################################################################################################################
##################################################################################################################
#####----- CONNECTION SCAN ALGORITHM (CSA) ----------------------------------------###############################
##################################################################################################################


@app.route('/plan_trip_CSA/', methods=['GET', 'POST'])
def plan_trip_CSA():
    return render_template("index_OD_path_TPL_names.html")


##--->>>*** insert the NAME of THE LOCATION as ORIGIN
@app.route('/insert_ORIGIN_name_CSA/', methods=['GET', 'POST'])
def insert_ORIGIN_name_CSA():
    session["name_ORIGIN_location"] = request.form.get("name_ORIGIN_location")
    print("name---->:", session["name_ORIGIN_location"])
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="MyApp")
    geolocator = Nominatim(user_agent="my_request")
    try:
        location = geolocator.geocode(session["name_ORIGIN_location"] + ",Roma Capitale, Lazio, 00187, Italia")
    except:
        location = geolocator.geocode(session["name_ORIGIN_location"] + ",Roma Capitale, Lazio, Italia")
    print("----ORIGIN LOCATION:", location)
    if location == None:
        abort(404)

    print("-----------The latitude of the ORIGIN location is: ", location.latitude)
    print("-----------The longitude of the ORIGIN location is: ", location.longitude)

    session["lat_ORIGIN"] = location.latitude
    session["lon_ORIGIN"] = location.longitude

    print("lat_ORIGIN, lon_ORIGIN:", session["lat_ORIGIN"], session["lon_ORIGIN"])

    ## make a .geojson file with the ORIGIN location POINT (see below...)
    df_ORIGIN_point = pd.DataFrame({'latitude': [session["lat_ORIGIN"]],
                                    'longitude': [session["lon_ORIGIN"]]
                                    })

    ####-----> make a Geodataframe....with ORIGIN POINT
    geometry = [Point(xy) for xy in zip(df_ORIGIN_point.longitude, df_ORIGIN_point.latitude)]
    crs = {'init': 'epsg:4326'}
    gdf_df_ORIGIN_point = GeoDataFrame(df_ORIGIN_point, crs=crs, geometry=geometry)
    ## transform geodataframeo into .geojson
    ORIGIN_point_json = gdf_df_ORIGIN_point.to_json()
    # print("ORIGIN_point_json:", ORIGIN_point_json)

    data_location_ORIGIN_TPL = [{
        'Origin': session["name_ORIGIN_location"],
        'Destination': '--choose destination--'
    }]

    session["ORIGIN_point"] = ORIGIN_point_json
    # print(session["ORIGIN_point"])

    return render_template("index_OD_path_TPL_ORIGIN_point.html",
                           data_location_ORIGIN_TPL=data_location_ORIGIN_TPL,
                           session_ORIGIN_point=session["ORIGIN_point"])


##--->>>*** insert the NAME of THE LOCATION as DESTINATION
@app.route('/insert_DESTINATION_name_CSA/', methods=['GET', 'POST'])
def insert_DESTINATION_name_CSA():
    if request.method == "POST":
        try:
            name_ORIGIN_location = session["name_ORIGIN_location"]
            print("name_ORIGIN_location:", name_ORIGIN_location)
        except AttributeError:
            abort(404)

        session["name_DESTINATION_location"] = request.form.get("name_DESTINATION_location")
        print("name---->:", session['name_DESTINATION_location'])
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="MyApp")
        try:
            location = geolocator.geocode(session["name_DESTINATION_location"] + ",Roma Capitale, Lazio, 00187, Italia")
        except:
            location = geolocator.geocode(session["name_DESTINATION_location"] + ",Roma Capitale, Lazio, Italia")
        print("----DESTINATION LOCATION:", location)
        if location == None:
            abort(404)
        print("-----------The latitude of the DESTINATION location is: ", location.latitude)
        print("-----------The longitude of the DESTINATION location is: ", location.longitude)

        session["lat_DESTINATION"] = location.latitude
        session["lon_DESTINATION"] = location.longitude
        print("lat_DESTINATION, lon_DESTINATION:", session["lat_DESTINATION"], session["lon_DESTINATION"])

        ## make a .geojson file with the DESTINATION location POINT (see below...)
        df_DESTINATION_point = pd.DataFrame({'latitude': [session["lat_DESTINATION"]],
                                             'longitude': [session["lon_DESTINATION"]]
                                             })

        ####-----> make a Geodataframe....with ORIGIN POINT
        geometry = [Point(xy) for xy in zip(df_DESTINATION_point.longitude, df_DESTINATION_point.latitude)]
        crs = {'init': 'epsg:4326'}
        gdf_df_DESTINATION_point = GeoDataFrame(df_DESTINATION_point, crs=crs, geometry=geometry)
        ## transform geodataframeo into .geojson
        DESTINATION_point_json = gdf_df_DESTINATION_point.to_json()
        # print("ORIGIN_point_json:", ORIGIN_point_json)

        ## make a .geojson file with the DESTINATION location POINT (see below...)

        data_location_DESTINATION_TPL = [{
            'Origin': session["name_ORIGIN_location"],
            'Destination': session["name_DESTINATION_location"]
        }]

        session["DESTINATION_point"] = DESTINATION_point_json

        session["gtfs"] = '2023_04_05'
        print("-------- GTFS data file------------:", session["gtfs"])

        return render_template("index_OD_path_TPL_DESTINATION_point.html",
                               data_location_DESTINATION_TPL=data_location_DESTINATION_TPL,
                               session_ORIGIN_point=session["ORIGIN_point"],
                               session_DESTINATION_point=session["DESTINATION_point"],
                               session_GTFS=session["gtfs"])  #


@app.route('/GTFS_selector_CSA/', methods=['GET', 'POST'])
def GTFS_selector_CSA():
    if request.method == "POST":
        ## declare a global variable

        session["gtfs"] = '2023_04_05'
        ## TRY if session exists
        try:
            session["gtfs"] = request.form.get("gtfs")
            selected_GTFS_data = session["gtfs"]
            print("selected_GTFS_data within session:", selected_GTFS_data)
            selected_GTFS_data = str(selected_GTFS_data)
        except:
            session["gtfs"] = '2023_04_05'
            selected_GTFS_data = session["gtfs"]
            print("using stored variable: ", session["gtfs"])

        print("selected_GTFS_data:", selected_GTFS_data)

        path = path_app + "static/GTFS"
        ## list all files in the directory
        list_GTFS_files = listdir(path)

        readable_day_GTFS = []
        for element in list_GTFS_files:
            # print(element)
            year_GTFS = element[:4]
            month_GTFS = element[4:6]
            day_GTFS = element[6:9]
            full_day_GTFS = year_GTFS + "_" + month_GTFS + "_" + day_GTFS
            # print(full_day_GTFS)
            readable_day_GTFS.append(full_day_GTFS)

            ## ----->> make a dictionary (for each id GTFS file associate a date):
            GTFS_dict = {}
            keys = list(readable_day_GTFS)

            for idx, u in enumerate(keys):
                # print(idx, u)
                GTFS_dict[u] = list_GTFS_files[idx]

        ## add empty element in front of the list
        readable_day_GTFS.insert(0, 'select day (GTFS)')

        ## save the list into a .txt file
        with open(path_app + "static/GTFS_files.txt", "w") as file:
            file.write(str(readable_day_GTFS))
        with open(path_app + "static/GTFS_files.txt", "r+") as f:
            old = f.read()  # read everything in the file
            f.seek(0)  # rewind
            f.write("var list_GTFS_files = \n" + old)  # assign the "var name" in the .geojson file

        # selected_GTFS_data = "2023_01_23"
        try:
            day = GTFS_dict[selected_GTFS_data]
        except KeyError:
            day = "20230123"

        # day = selected_GTFS_data
        print("GTFS day:", selected_GTFS_data)
        print("day:", day)


        #### ---- retrieve ORIGIN - DESTINATION data --------------- ################################
        try:
            name_ORIGIN_location = session["name_ORIGIN_location"]
            print("name_ORIGIN_location:", name_ORIGIN_location)
        except AttributeError:
            abort(404)

        try:
            name_DESTINATION_location = session["name_DESTINATION_location"]
            print("name_DESTINATION_location:", name_DESTINATION_location)
        except AttributeError:
            abort(404)

        # session["gtfs"] = '2023_04_05'
        print("-------- GTFS data file------------:", session["gtfs"])

        selected_year_GTFS = day[:4]
        selected_month_GTFS = day[4:6]
        selected_day_GTFS = day[6:9]
        selected_CSA_day = selected_year_GTFS + "-" + selected_month_GTFS + "-" + selected_day_GTFS
        session["CSA_day"] = selected_CSA_day

        data_location_DESTINATION_TPL = [{
            'Origin': session["name_ORIGIN_location"],
            'Destination': session["name_DESTINATION_location"]
        }]

        datum_CSA_day = [{
            'day': selected_CSA_day,
            'hour': 'choose hour'
        }]

        return render_template("index_OD_path_TPL_DESTINATION_point_select_hour.html",
                               datum_CSA_day=datum_CSA_day,
                               session_ORIGIN_point=session["ORIGIN_point"],
                               session_DESTINATION_point=session["DESTINATION_point"],
                               data_location_DESTINATION_TPL=data_location_DESTINATION_TPL,
                               session_GTFS=session["gtfs"],
                               session_selected_CSA_day=session["CSA_day"])


@app.route('/CSA_hour_selector/', methods=['GET', 'POST'])
def CSA_hour_selector():
    if request.method == "POST":

        selected_CSA_hour = 7
        selected_CSA_day = '2020-10-02'

        try:
            selected_CSA_day = session["CSA_day"]
            print("selected_CSA_day:.....", selected_CSA_day)
        except AttributeError:
            abort(404)

        session["CSA_hour"] = request.form["CSA_hour"]
        print("selected_CSA_hour....:", session["CSA_hour"])
        print("selected_CSA_day.....:", session["CSA_day"])
        selected_CSA_hour = str(session["CSA_hour"])

        #### ---- retrieve ORIGIN - DESTINATION data --------------- ################################
        try:
            name_ORIGIN_location = session["name_ORIGIN_location"]
            print("name_ORIGIN_location:", name_ORIGIN_location)
        except AttributeError:
            abort(404)

        try:
            name_DESTINATION_location = session["name_DESTINATION_location"]
            print("name_DESTINATION_location:", name_DESTINATION_location)
        except AttributeError:
            abort(404)

        data_location_DESTINATION_TPL = [{
            'Origin': session["name_ORIGIN_location"],
            'Destination': session["name_DESTINATION_location"]
        }]

        datum_CSA_day = [{
            'day': selected_CSA_day,
            'hour': selected_CSA_hour
        }]

        return render_template("index_OD_path_TPL_DESTINATION_point_select_hour.html",
                               session_ORIGIN_point=session["ORIGIN_point"],
                               session_DESTINATION_point=session["DESTINATION_point"],
                               data_location_DESTINATION_TPL=data_location_DESTINATION_TPL,
                               datum_CSA_day=datum_CSA_day,
                               selected_CSA_day=session["CSA_day"],
                               selected_CSA_hour=session["CSA_hour"])


@app.route('/OD_path_TPL_CSA/', methods=['GET', 'POST'])
def OD_path_TPL_CSA():
    from center_map import center, cost_assignment, get_pos
    import time
    import csa
    from datetime import datetime
    from prepare_timetable_GTFS import PreCsa
    # import osmNw

    #########################################################
    #########################################################

    ###---->>> CREATE TIMETABLE FROM gtfs FILE
    selected_CSA_day = session["CSA_day"]
    selected_CSA_hour = session["CSA_hour"]
    print("---------selected_CSA_day------------:", selected_CSA_day)
    print("---------selected_CSA_hour------------:", selected_CSA_hour)

    # selected_CSA_day = "2020-10-02"
    # selected_CSA_hour = 9

    if len(selected_CSA_day) == 8:
        selected_GTFS_data = selected_CSA_day
    else:
        selected_year_GTFS = selected_CSA_day[:4]
        selected_month_GTFS = selected_CSA_day[5:7]
        selected_day_GTFS = selected_CSA_day[8:10]
        selected_GTFS_data = selected_year_GTFS + selected_month_GTFS + selected_day_GTFS

    session["CSA_day"] = selected_GTFS_data

    # selected_GTFS_data = "20201002"
    path = path_app + "static/GTFS/" + selected_GTFS_data + "/"
    graph_path = path_app + "static/GTFS/gtfs_osmnet/"
    fn = 'walknet_epgs4326.graphml'

    ## create timetable (.csv file)
    print(selected_GTFS_data)
    body = PreCsa(path, graph_path, selected_GTFS_data)
    body.path_graph = graph_path
    try:
        body.create_timetable()
    except:
        abort(404)

    #######################################################################
    #######################################################################

    # selected_CSA_hour = "09:30"

    hour = int(selected_CSA_hour.split(":")[0])
    minutes = int(selected_CSA_hour.split(":")[1])
    # selected_csa_hour = 9
    # hour = 8
    # min = 0
    # sec = 0
    total_seconds = hour * 60 * 60 + minutes * 60

    def convert(seconds):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    deptime = convert(total_seconds)

    print("-----------selected_GTFS_data-------------:", session["CSA_day"])
    print("-------------deptime-----------:", deptime)

    ## retrieve Origin & Destiantion coordinates
    lat_ORIGIN = session["lat_ORIGIN"]
    lon_ORIGIN = session["lon_ORIGIN"]

    lat_DESTINATION = session["lat_DESTINATION"]
    lon_DESTINATION = session["lon_DESTINATION"]

    try:
        startLocation = [lat_ORIGIN, lon_ORIGIN]
        endLocation = [lat_DESTINATION, lon_DESTINATION]

        import csa
        c = csa.Csa(path_app + "/static/GTFS/" + selected_GTFS_data + "/", selected_GTFS_data)
        c.load_timetable()
        c.load_stops()
        print('loading footpath between adjacent stops....')
        print('loading stopToStop shape....')
        print("---list of foothpaths-------")
        c.load_walknetstopsfootpath()
        c.run(startLocation, endLocation, deptime)
        try:
            c.showMapPath(startLocation, endLocation)
        except:
            abort(404)

        TRAVEL_TIME = c.showMapPath(startLocation, endLocation)[0]
        TRAVEL_SPEED = c.showMapPath(startLocation, endLocation)[1]
        WALKING_DISTANCE = c.showMapPath(startLocation, endLocation)[2]
        TRANSFERS = c.showMapPath(startLocation, endLocation)[3]
        WAITING_TIME = c.showMapPath(startLocation, endLocation)[4]

    except NameError:
        abort(404)

    ##################################################################################
    #### build path on the map......
    new_poline_list = []

    stops = pd.read_csv(path_app + '/static/GTFS/' + selected_GTFS_data + '/' + 'stops.txt')
    trips = pd.read_csv(path_app + '/static/GTFS/' + selected_GTFS_data + '/' + 'trips.txt')
    shapes = pd.read_csv(path_app + '/static/GTFS/' + selected_GTFS_data + '/' + 'shapes.txt')

    timetable = pd.read_csv(path_app + '/static/' + 'final_timetable.csv')
    for element in timetable.itertuples(index=True):
        print(element)
        ###-->> check for FIRST walking path ----------------------------------------------------#################
        ##########################################################################################################
        if ((element.line_number == '1fp') & (element.trip_id == 'footpath')):
            first_footpath_start = element.stop1_code
            x = first_footpath_start.split("_")
            LAT_first_fp = float(x[0])
            LON_first_fp = float(x[1])

            stop_name = element.stop
            stop2_code = str(element.stop2_code)

            LAT_next = stops[stops['stop_name'] == stop_name]
            LAT_next = stops[stops['stop_id'] == stop2_code]['stop_lat']
            LAT_next = pd.DataFrame(LAT_next)
            LAT_next = LAT_next.reset_index(drop=True)
            LAT_next = LAT_next[['stop_lat']]
            LAT_next = LAT_next['stop_lat'][0]
            LAT_next = float(LAT_next)
            LON_next = stops[stops['stop_name'] == stop_name]
            LON_next = stops[stops['stop_id'] == stop2_code]['stop_lon']
            LON_next = pd.DataFrame(LON_next)
            LON_next = LON_next.reset_index(drop=True)
            LON_next = LON_next[['stop_lon']]
            LON_next = LON_next['stop_lon'][0]
            LON_next = float(LON_next)

            ext = 0.005

            def polygon():
                if (LAT_first_fp != LAT_next) & (LON_first_fp != LON_next):
                    poly = Polygon([(min(LON_first_fp, LON_next) - ext, min(LAT_first_fp, LAT_next) - ext),
                                    (max(LON_first_fp, LON_next) + ext, min(LAT_first_fp, LAT_next) - ext),
                                    (max(LON_first_fp, LON_next) + ext, max(LAT_first_fp, LAT_next) + ext),
                                    (min(LON_first_fp, LON_next) - ext, max(LAT_first_fp, LAT_next) + ext)])
                    return poly

            polygon()

            grafo = ox.graph_from_polygon(polygon(), network_type='walk')
            gdf_nodes, gdf_edges = ox.graph_to_gdfs(grafo)
            ## get nearest node to the Origin & Destination points
            nearest_node_ORIGIN, distance_ORIGIN = ox.nearest_nodes(grafo, LON_first_fp, LAT_first_fp,
                                                                    return_dist=True)
            nearest_node_DESTINATION, distance_DESTINATION = ox.nearest_nodes(grafo, LON_next,
                                                                              LAT_next,
                                                                              return_dist=True)
            ## find shortest path
            shortest_OD_walk = nx.shortest_path(grafo, nearest_node_ORIGIN,
                                                nearest_node_DESTINATION,
                                                weight='length')
            ### associate lat, lon to each node
            shortest_OD_walk_df = gdf_nodes.loc[shortest_OD_walk]
            poline_walk_1sp = [[x, y] for (x, y) in zip(shortest_OD_walk_df.x, shortest_OD_walk_df.y)]
            new_poline_list.append(poline_walk_1sp)

        ###################################################################################################
        ####-->> check for walking path.........LAST footpath.......................#######################
        if ((element.line_number == 'lastfp') & (element.trip_id == 'footpath')):
            stop_name = element.start
            stop1_code = str(element.stop1_code)
            # LAT_next = stops[stops['stop_name'].str.contains(r'(?:\s|^)' + stop_name + '(?:,\s|$)')]
            LAT_next = stops[stops['stop_name'] == stop_name]
            LAT_next = stops[stops['stop_id'] == stop1_code]['stop_lat']
            LAT_next = pd.DataFrame(LAT_next)
            LAT_next = LAT_next.reset_index(drop=True)
            LAT_next = LAT_next[['stop_lat']]
            LAT_next = LAT_next['stop_lat'][0]
            LAT_next = float(LAT_next)

            LON_next = stops[stops['stop_name'] == stop_name]
            LON_next = stops[stops['stop_id'] == stop1_code]['stop_lon']
            LON_next = pd.DataFrame(LON_next)
            LON_next = LON_next.reset_index(drop=True)
            LON_next = LON_next[['stop_lon']]
            LON_next = LON_next['stop_lon'][0]
            LON_next = float(LON_next)

            last_footpath_end = element.stop2_code
            x = last_footpath_end.split("_")
            LAT_last_fp = float(x[0])
            LON_last_fp = float(x[1])

            ext = 0.005

            def polygon():
                poly = Polygon([(min(LON_last_fp, LON_next) - ext, min(LAT_last_fp, LAT_next) - ext),
                                (max(LON_last_fp, LON_next) + ext, min(LAT_last_fp, LAT_next) - ext),
                                (max(LON_last_fp, LON_next) + ext, max(LAT_last_fp, LAT_next) + ext),
                                (min(LON_last_fp, LON_next) - ext, max(LAT_last_fp, LAT_next) + ext)])
                return poly

            polygon()

            grafo = ox.graph_from_polygon(polygon(), network_type='walk')
            gdf_nodes, gdf_edges = ox.graph_to_gdfs(grafo)
            ## get nearest node to the Origin & Destination points
            nearest_node_ORIGIN, distance_ORIGIN = ox.nearest_nodes(grafo, LON_next, LAT_next,
                                                                    return_dist=True)
            nearest_node_DESTINATION, distance_DESTINATION = ox.nearest_nodes(grafo, LON_last_fp,
                                                                              LAT_last_fp,
                                                                              return_dist=True)
            ## find shortest path
            shortest_OD_walk = nx.shortest_path(grafo, nearest_node_ORIGIN,
                                                nearest_node_DESTINATION,
                                                weight='length')
            ### associate lat, lon to each node
            shortest_OD_walk_df = gdf_nodes.loc[shortest_OD_walk]
            poline_walk_last = [[x, y] for (x, y) in zip(shortest_OD_walk_df.x, shortest_OD_walk_df.y)]
            new_poline_list.append(poline_walk_last)

        #################################################################################################
        ####-->> check for walking path.........INTERMEDIATE footpath.......................#############
        if ((element.line_number == 'fp') & (element.trip_id == 'footpath')):
            # break

            stop1_name = element.start
            stop1_code = str(element.stop1_code)
            LAT_next1 = stops[stops['stop_name'] == stop1_name]
            LAT_next1 = LAT_next1[LAT_next1['stop_id'] == stop1_code]['stop_lat']
            LAT_next1 = pd.DataFrame(LAT_next1)
            LAT_next1 = LAT_next1.reset_index(drop=True)
            LAT_next1 = LAT_next1[['stop_lat']]
            LAT_next1 = LAT_next1['stop_lat'][0]
            LAT_next1 = float(LAT_next1)
            LON_next1 = stops[stops['stop_name'] == stop1_name]
            LON_next1 = LON_next1[LON_next1['stop_id'] == stop1_code]['stop_lon']
            LON_next1 = pd.DataFrame(LON_next1)
            LON_next1 = LON_next1.reset_index(drop=True)
            LON_next1 = LON_next1[['stop_lon']]
            LON_next1 = LON_next1['stop_lon'][0]
            LON_next1 = float(LON_next1)

            stop2_name = element.stop
            stop2_code = str(element.stop2_code)
            LAT_next2 = stops[stops['stop_name'] == stop2_name]
            LAT_next2 = LAT_next2[LAT_next2['stop_id'] == stop2_code]['stop_lat']
            LAT_next2 = pd.DataFrame(LAT_next2)
            LAT_next2 = LAT_next2.reset_index(drop=True)
            LAT_next2 = LAT_next2[['stop_lat']]
            LAT_next2 = LAT_next2['stop_lat'][0]
            LAT_next2 = float(LAT_next2)
            LON_next2 = stops[stops['stop_name'] == stop2_name]
            LON_next2 = LON_next2[LON_next2['stop_id'] == stop2_code]['stop_lon']
            LON_next2 = pd.DataFrame(LON_next2)
            LON_next2 = LON_next2.reset_index(drop=True)
            LON_next2 = LON_next2[['stop_lon']]
            LON_next2 = LON_next2['stop_lon'][0]
            LON_next2 = float(LON_next2)

            ext = 0.005

            def polygon():
                poly = Polygon([(min(LON_next2, LON_next1) - ext, min(LAT_next2, LAT_next1) - ext),
                                (max(LON_next2, LON_next1) + ext, min(LAT_next2, LAT_next1) - ext),
                                (max(LON_next2, LON_next1) + ext, max(LAT_next2, LAT_next1) + ext),
                                (min(LON_next2, LON_next1) - ext, max(LAT_next2, LAT_next1) + ext)])
                return poly

            polygon()

            grafo = ox.graph_from_polygon(polygon(), network_type='walk')
            gdf_nodes, gdf_edges = ox.graph_to_gdfs(grafo)
            ## get nearest node to the Origin & Destination points
            nearest_node_ORIGIN, distance_ORIGIN = ox.nearest_nodes(grafo, LON_next1, LAT_next1,
                                                                    return_dist=True)
            nearest_node_DESTINATION, distance_DESTINATION = ox.nearest_nodes(grafo, LON_next2,
                                                                              LAT_next2,
                                                                              return_dist=True)
            ## find shortest path
            shortest_OD_walk = nx.shortest_path(grafo, nearest_node_ORIGIN,
                                                nearest_node_DESTINATION,
                                                weight='length')
            ### associate lat, lon to each node
            shortest_OD_walk_df = gdf_nodes.loc[shortest_OD_walk]
            poline_walk_intermediate = [[x, y] for (x, y) in zip(shortest_OD_walk_df.x, shortest_OD_walk_df.y)]
            new_poline_list.append(poline_walk_intermediate)

        #################################################################################################
        ### check TPL ONLY path --------------------#####################################################
        if (element.trip_id != 'footpath'):
            # trip1_id = '1906-4'
            trip1_id = str(element.trip_id)
            shape_ID = trips[trips['trip_id'] == trip1_id]['shape_id']
            shape_ID = pd.DataFrame(shape_ID)
            shape_ID = shape_ID.reset_index(drop=True)
            shape_ID = shape_ID[['shape_id']]
            shape_ID = shape_ID['shape_id'][0]
            try:
                shape_ID = int(shape_ID)
            except ValueError:
                pass
            except TypeError:
                pass
            except NameError:
                pass
                trip1_id = str(element.trip_id)
                shape_ID = trips[trips['trip_id'] == trip1_id]['shape_id']
                shape_ID = pd.DataFrame(shape_ID)
                shape_ID = shape_ID.reset_index(drop=True)
                shape_ID = shape_ID[['shape_id']]
                shape_ID = shape_ID['shape_id'][0]

            ## get all lat lon....

            shape_path = shapes[shapes['shape_id'] == shape_ID]
            if len(shape_path) < 1:
                shape_path = shapes[shapes['shape_id'] == str(shape_ID)]

            stop1_code = str(element.stop1_code)
            road_1_LAT = stops[stops['stop_id'] == stop1_code]['stop_lat']
            road_1_LAT = pd.DataFrame(road_1_LAT)
            road_1_LAT = road_1_LAT.reset_index(drop=True)
            road_1_LAT = road_1_LAT[['stop_lat']]
            road_1_LAT = road_1_LAT['stop_lat'][0]

            road_1_LON = stops[stops['stop_id'] == stop1_code]['stop_lon']
            road_1_LON = pd.DataFrame(road_1_LON)
            road_1_LON = road_1_LON.reset_index(drop=True)
            road_1_LON = road_1_LON[['stop_lon']]
            road_1_LON = road_1_LON['stop_lon'][0]

            stop2_code = str(element.stop2_code)
            road_2_LAT = stops[stops['stop_id'] == stop2_code]['stop_lat']
            road_2_LAT = pd.DataFrame(road_2_LAT)
            road_2_LAT = road_2_LAT.reset_index(drop=True)
            road_2_LAT = road_2_LAT[['stop_lat']]
            road_2_LAT = road_2_LAT['stop_lat'][0]
            road_2_LON = stops[stops['stop_id'] == stop2_code]['stop_lon']
            road_2_LON = pd.DataFrame(road_2_LON)
            road_2_LON = road_2_LON.reset_index(drop=True)
            road_2_LON = road_2_LON[['stop_lon']]
            road_2_LON = road_2_LON['stop_lon'][0]

            try:
                ## get fraction of shape_path from lat, lon from Road1 to Road2
                seq1_LAT_start = shape_path[(shape_path['shape_pt_lat']) == round(road_1_LAT, 6)]['shape_pt_sequence']
                seq1_LAT_start = pd.DataFrame(seq1_LAT_start)
                seq1_LAT_start = seq1_LAT_start.reset_index(drop=True)
                seq1_LAT_start = seq1_LAT_start[['shape_pt_sequence']]
                seq_start = seq1_LAT_start['shape_pt_sequence'][0]
                # print("-----------seq_start:------------", seq_start)
            except KeyError:
                pass

            try:
                seq2_LAT_stop = shape_path[shape_path['shape_pt_lat'] == round(road_2_LAT, 6)]['shape_pt_sequence']
                seq2_LAT_stop = pd.DataFrame(seq2_LAT_stop)
                seq2_LAT_stop = seq2_LAT_stop.reset_index(drop=True)
                seq2_LAT_stop = seq2_LAT_stop[['shape_pt_sequence']]
                seq_stop = seq2_LAT_stop['shape_pt_sequence'][0]

                shape_path_LEG = shape_path[
                    (shape_path['shape_pt_sequence'] >= seq_start) & (shape_path['shape_pt_sequence'] <= seq_stop)]
                # make a polyline:
                TPL_poline = [[x, y] for (x, y) in zip(shape_path_LEG.shape_pt_lon, shape_path_LEG.shape_pt_lat)]
            except KeyError:
                TPL_poline = [[road_1_LON, road_1_LAT], [road_2_LON, road_2_LAT]]

            new_poline_list.append(TPL_poline)

        ###---------------> ###################################################################################
        ##### flattering a list----------------------------------------########################################
        flat_list = [item for sublist in new_poline_list for item in sublist]

        ## calculate distance
        distance = []
        for previous, current in zip(flat_list, flat_list[1:]):
            # print(tuple(previous), tuple(current))
            dist = hs.haversine(tuple(previous), tuple(current), unit=Unit.KILOMETERS)
            distance.append(dist)
        total_distance = sum(distance)  # distance in kilometers

        ####------flatten list----------------------------------------------####
        geom = LineString(flat_list)
        poline_gdf = gpd.GeoDataFrame(geometry=[geom])
        # poline_gdf.plot()
        #### save into geojson file....................
        ## set crs first
        poline_gdf = poline_gdf.set_crs('epsg:4326')

        ## save "poline_gdf" as geojson file:
        ## transform geodataframeo into .geojson
        path_TPL_CSA = poline_gdf.to_json()

        with open(path_app + 'static/path_TPL_CSA.geojson', 'w') as f:
            f.write(poline_gdf.to_json())

        with open(path_app + 'static/path_TPL_CSA_' + session.sid + '.geojson', 'w') as f:
            f.write(poline_gdf.to_json())

        session["path_TPL_CSA"] = path_TPL_CSA
        # print("----path_TPL_CSA-----------------------:",   session["path_TPL_CSA"])

    DISTANZA = total_distance
    # print("Travelled distance -------------->:", DISTANZA)
    # print("TRAVEL_TIME, TRAVEL_SPEED, WALKING_DISTANCE, TRANSFERS, WAITING_TIME:", TRAVEL_TIME, TRAVEL_SPEED, WALKING_DISTANCE, TRANSFERS, WAITING_TIME)

    session['travel_time'] = TRAVEL_TIME
    session['travel_speed'] = TRAVEL_SPEED
    session['walking_distance'] = WALKING_DISTANCE
    session['transfers'] = TRANSFERS
    session['waiting_time'] = round(WAITING_TIME / 60, 2)
    session['total_distance'] = DISTANZA

    data_path_TPL_CSA = [{
        'n_transfers': session['transfers'],
        'Travel_time': session["travel_time"],
        'Waiting_time': session['waiting_time']
    }]

    data_location_DESTINATION_TPL = [{
        'Origin': session["name_ORIGIN_location"],
        'Destination': session["name_DESTINATION_location"]
    }]

    datum_CSA_day = [{
        'day': selected_CSA_day,
        'hour': selected_CSA_hour
    }]

    return render_template("index_OD_TPL_CSA_PATH.html",
                           session_ORIGIN_point=session["ORIGIN_point"],
                           session_DESTINATION_point=session["DESTINATION_point"],
                           data_location_DESTINATION_TPL=data_location_DESTINATION_TPL,
                           session_trave_time=session['travel_time'],
                           session_travel_speed=session['travel_speed'],
                           session_transfers=session['transfers'],
                           session_waiting_time=session['waiting_time'],
                           session_total_distance=session["total_distance"],
                           session_path_TPL_CSA=session["path_TPL_CSA"],
                           selected_CSA_day=session["CSA_day"],
                           selected_CSA_hour=session["CSA_hour"],
                           data_path_TPL_CSA=data_path_TPL_CSA,
                           datum_CSA_day=datum_CSA_day)


@app.route('/simulated_path_CSA/', methods=['GET', 'POST'])
def simulated_path_CSA():
    selected_GTFS_data = session["CSA_day"]
    print(selected_GTFS_data)
    # selected_GTFS_data = "20201002"
    df_stops_and_times = pd.read_csv(path_app + "static/final_timetable.csv")
    ## use the short_name for the 'line_number'
    df_stops_and_times.reset_index(inplace=True)
    df_stops_and_times = df_stops_and_times[['line_number', 'trip_id', 'stop1_code', 'start',
                                             'stop2_code', 'stop', 'start_time', 'end_time', 'distance(m)']]
    CSA_timetable_to_show = df_stops_and_times[
        ['line_number', 'start', 'stop', 'start_time', 'end_time', 'distance(m)']]

    ## convert to html with the vanilla structure
    CSA_timetable_to_show = CSA_timetable_to_show.to_html()
    #### render directly from string:
    resp_CSA = make_response(render_template_string(CSA_timetable_to_show))
    return resp_CSA


##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##### --------------------- BEST --------------------------- #####################################
###### by Matteo 20230922 -----------------------------------#####################################
##################################################################################################

@app.route('/best_page/', methods=['GET', 'POST'])
def best():
  import glob
  if os.path.isfile(path_app +'static/best/gtfsdata.csv'):
      print('gtfsdata.csv already exists')
      allgtfs = pd.read_csv(path_app +'static/best/gtfsdata.csv')
  else:
      allgtfs = pd.DataFrame(data={'file': ['','','','','',''], 'data': ['','','','','','']})
      allgtfs.to_csv(path_app +'static/best/gtfsdata.csv',index=False)

  # List all gtfs files and write them on txt file
  gtfslist1 = [allgtfs['file'].values[0]] + glob.glob('./static/best/gtfs/*.zip')
  file = open('./static/best/gtfslist1.txt', 'w'); file.write('var gtfs_zip1 = ' + str(gtfslist1)); file.close()
  gtfslist2 = [allgtfs['file'].values[1]] + glob.glob('./static/best/gtfs/*.zip')
  file = open('./static/best/gtfslist2.txt', 'w'); file.write('var gtfs_zip2 = ' + str(gtfslist2)); file.close()
  gtfslist3 = [allgtfs['file'].values[2]] + glob.glob('./static/best/gtfs/*.zip')
  file = open('./static/best/gtfslist3.txt', 'w'); file.write('var gtfs_zip3 = ' + str(gtfslist3)); file.close()
  gtfslist4 = [allgtfs['file'].values[3]] + glob.glob('./static/best/gtfs/*.zip')
  file = open('./static/best/gtfslist4.txt', 'w'); file.write('var gtfs_zip4 = ' + str(gtfslist4)); file.close()
  gtfslist5 = [allgtfs['file'].values[4]] + glob.glob('./static/best/gtfs/*.zip')
  file = open('./static/best/gtfslist5.txt', 'w'); file.write('var gtfs_zip5 = ' + str(gtfslist5)); file.close()
  gtfslist6 = [allgtfs['file'].values[5]] + glob.glob('./static/best/gtfs/*.zip')
  file = open('./static/best/gtfslist6.txt', 'w'); file.write('var gtfs_zip6 = ' + str(gtfslist6)); file.close()

  file = open('./static/best/dswlist.txt', 'w');file.write('var seldate1 = ["'+str(allgtfs['data'].values[0])+'"]');file.close()
  file = open('./static/best/dsplist.txt', 'w');file.write('var seldate2 = ["'+str(allgtfs['data'].values[1])+'"]');file.close()
  file = open('./static/best/dshlist.txt', 'w');file.write('var seldate3 = ["'+str(allgtfs['data'].values[2])+'"]');file.close()
  file = open('./static/best/dwwlist.txt', 'w');file.write('var seldate4 = ["'+str(allgtfs['data'].values[3])+'"]');file.close()
  file = open('./static/best/dwplist.txt', 'w');file.write('var seldate5 = ["'+str(allgtfs['data'].values[4])+'"]');file.close()
  file = open('./static/best/dwhlist.txt', 'w');file.write('var seldate6 = ["'+str(allgtfs['data'].values[5])+'"]');file.close()

  if os.path.isfile('./static/best/city.csv'):
      with open('./static/best/city.csv', "r") as text_file:
          old_city = text_file.read()
  else:
      old_city = 'Select city'
  with open('./static/best/citylist.txt', "w") as text_file:
      cityl = [old_city] + ['Rome', 'Varese']
      text_file.write('selcity = ' + str(cityl))

  # if it doesn't exists create an empty json file to be plotted on the map
  if not os.path.isfile('./static/best/best_stops.geojson'):
      file = open('./static/best/best_stops.geojson', 'w')
      file.write('var stop_best_bus = {"type": "FeatureCollection", "features": []}'); file.close()

  # return render_template("index_censuary_and_public_transport.html")
  return render_template("index_best.html")

@app.route('/GTFS_chooser/<which>', methods=['GET', 'POST'])
def GTFS_chooser(which):
    import glob
    if request.method == "POST":
        if which == '<sumw>': rf = 'gtfs1'
        if which == '<sump>': rf = 'gtfs2'
        if which == '<sumh>': rf = 'gtfs3'
        if which == '<winw>': rf = 'gtfs4'
        if which == '<winp>': rf = 'gtfs5'
        if which == '<winh>': rf = 'gtfs6'

        selected_GTFS_data = request.form[rf]
        print("selected_GTFS:", selected_GTFS_data)
        print('which: ', which)
        allgtfs = pd.read_csv('./static/best/gtfsdata.csv')
        if which == '<sumw>': allgtfs.iloc[0,0] = selected_GTFS_data; primadata = allgtfs.iloc[0,1]
        if which == '<sump>': allgtfs.iloc[1,0] = selected_GTFS_data; primadata = allgtfs.iloc[1,1]
        if which == '<sumh>': allgtfs.iloc[2,0] = selected_GTFS_data; primadata = allgtfs.iloc[2,1]
        if which == '<winw>': allgtfs.iloc[3,0] = selected_GTFS_data; primadata = allgtfs.iloc[3,1]
        if which == '<winp>': allgtfs.iloc[4,0] = selected_GTFS_data; primadata = allgtfs.iloc[4,1]
        if which == '<winh>': allgtfs.iloc[5,0] = selected_GTFS_data; primadata = allgtfs.iloc[5,1]
        allgtfs.to_csv('./static/best/gtfsdata.csv', index=False)
        # List all gtfs files and write them on txt file
        gtfslist1 = [allgtfs['file'].values[0]] + glob.glob('./static/best/gtfs/*.zip')
        file = open('./static/best/gtfslist1.txt', 'w');
        file.write('var gtfs_zip1 = ' + str(gtfslist1));
        file.close()
        gtfslist2 = [allgtfs['file'].values[1]] + glob.glob('./static/best/gtfs/*.zip')
        file = open('./static/best/gtfslist2.txt', 'w');
        file.write('var gtfs_zip2 = ' + str(gtfslist2));
        file.close()
        gtfslist3 = [allgtfs['file'].values[2]] + glob.glob('./static/best/gtfs/*.zip')
        file = open('./static/best/gtfslist3.txt', 'w');
        file.write('var gtfs_zip3 = ' + str(gtfslist3));
        file.close()
        gtfslist4 = [allgtfs['file'].values[3]] + glob.glob('./static/best/gtfs/*.zip')
        file = open('./static/best/gtfslist4.txt', 'w');
        file.write('var gtfs_zip4 = ' + str(gtfslist4));
        file.close()
        gtfslist5 = [allgtfs['file'].values[4]] + glob.glob('./static/best/gtfs/*.zip')
        file = open('./static/best/gtfslist5.txt', 'w');
        file.write('var gtfs_zip5 = ' + str(gtfslist5));
        file.close()
        gtfslist6 = [allgtfs['file'].values[5]] + glob.glob('./static/best/gtfs/*.zip')
        file = open('./static/best/gtfslist6.txt', 'w');
        file.write('var gtfs_zip6 = ' + str(gtfslist6));
        file.close()

        # Create list of dates
        #feed = ptg.load_feed(selected_GTFS_data)

        ## shapely.__version__
        ## shapely version == 1.8.4
        # pip install shapely==1.8.5

        import osmnx
        import gtfs_functions
        from gtfs_functions import Feed
        feed = Feed(selected_GTFS_data,busiest_date=False)
        sibyd = feed.get_dates_service_id()
        print(sibyd.keys().to_list())
        sibydl = sibyd.keys().to_list()
        sibydl = [datetime.datetime.strptime(d,'%Y-%m-%d').strftime('%Y%m%d') for d in sibydl]
        #sibydl = ['select date'] + sibydl
        sibydl = [primadata] + sibydl
        if which == '<sumw>': file = open('./static/best/dswlist.txt', 'w'); file.write('var seldate1 = ' + str(sibydl)); file.close()
        if which == '<sump>': file = open('./static/best/dsplist.txt', 'w'); file.write('var seldate2 = ' + str(sibydl)); file.close()
        if which == '<sumh>': file = open('./static/best/dshlist.txt', 'w'); file.write('var seldate3 = ' + str(sibydl)); file.close()
        if which == '<winw>': file = open('./static/best/dwwlist.txt', 'w'); file.write('var seldate4 = ' + str(sibydl)); file.close()
        if which == '<winp>': file = open('./static/best/dwplist.txt', 'w'); file.write('var seldate5 = ' + str(sibydl)); file.close()
        if which == '<winh>': file = open('./static/best/dwhlist.txt', 'w'); file.write('var seldate6 = ' + str(sibydl)); file.close()

        return render_template("index_best.html")

@app.route('/date_chooser/<which>', methods=['GET', 'POST'])
def date_chooser(which):
    import ast
    if request.method == "POST":
        if which == '<datesw>': rf = 'datesw'
        if which == '<datesp>': rf = 'datesp'
        if which == '<datesh>': rf = 'datesh'
        if which == '<dateww>': rf = 'dateww'
        if which == '<datewp>': rf = 'datewp'
        if which == '<datewh>': rf = 'datewh'

        selected_date_data = request.form[rf]
        print("selected_data:", selected_date_data)
        print('which: ', which)
        allgtfs = pd.read_csv('./static/best/gtfsdata.csv')
        if which == '<datesw>': allgtfs.iloc[0,1] = selected_date_data
        if which == '<datesp>': allgtfs.iloc[1,1] = selected_date_data
        if which == '<datesh>': allgtfs.iloc[2,1] = selected_date_data
        if which == '<dateww>': allgtfs.iloc[3,1] = selected_date_data
        if which == '<datewp>': allgtfs.iloc[4,1] = selected_date_data
        if which == '<datewh>': allgtfs.iloc[5,1] = selected_date_data
        allgtfs.to_csv('./static/best/gtfsdata.csv', index=False)
        if which == '<datesw>': file = open('./static/best/dswlist.txt', 'r'); sibydl = ast.literal_eval(file.read().split('= ')[-1]); sibydl[0] = selected_date_data; file = open('./static/best/dswlist.txt', 'w'); file.write('var seldate1 = ' + str(sibydl)); file.close()
        if which == '<datesp>': file = open('./static/best/dsplist.txt', 'r'); sibydl = ast.literal_eval(file.read().split('= ')[-1]); sibydl[0] = selected_date_data; file = open('./static/best/dsplist.txt', 'w'); file.write('var seldate2 = ' + str(sibydl)); file.close()
        if which == '<datesh>': file = open('./static/best/dshlist.txt', 'r'); sibydl = ast.literal_eval(file.read().split('= ')[-1]); sibydl[0] = selected_date_data; file = open('./static/best/dshlist.txt', 'w'); file.write('var seldate3 = ' + str(sibydl)); file.close()
        if which == '<dateww>': file = open('./static/best/dwwlist.txt', 'r'); sibydl = ast.literal_eval(file.read().split('= ')[-1]); sibydl[0] = selected_date_data; file = open('./static/best/dwwlist.txt', 'w'); file.write('var seldate4 = ' + str(sibydl)); file.close()
        if which == '<datewp>': file = open('./static/best/dwplist.txt', 'r'); sibydl = ast.literal_eval(file.read().split('= ')[-1]); sibydl[0] = selected_date_data; file = open('./static/best/dwplist.txt', 'w'); file.write('var seldate5 = ' + str(sibydl)); file.close()
        if which == '<datewh>': file = open('./static/best/dwhlist.txt', 'r'); sibydl = ast.literal_eval(file.read().split('= ')[-1]); sibydl[0] = selected_date_data; file = open('./static/best/dwhlist.txt', 'w'); file.write('var seldate6 = ' + str(sibydl)); file.close()

        return render_template("index_best.html")

@app.route('/city_chooser/', methods=['GET', 'POST'])
def city_chooser():
    if request.method == "POST":
        selected_city = request.form['citysel']
        with open('./static/best/city.csv', "w") as text_file:
            text_file.write(selected_city)
        old_city = selected_city
        with open('./static/best/citylist.txt', "w") as text_file:
            cityl = [old_city] + ['Rome', 'Varese']
            text_file.write('selcity = ' + str(cityl))
    return render_template("index_best.html")

@app.route('/best_prep/', methods=['GET', 'POST'])
def best_prep():
    # Prepare lists of available fields from database.
    # input
    from pathlib import Path
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    mydb = DB()
    mydb.refresh()
    # return render_template("index_censuary_and_public_transport.html")
    return render_template("index_prep.html")

@app.route('/launch_gtfs2enea/', methods=['GET', 'POST'])
def best_gtfs2enea():
    print('gtfs2enea!!')
    allgtfs = pd.read_csv('./static/best/gtfsdata.csv')
    with open('./static/best/city.csv', "r") as text_file:
        mycity = text_file.read()
    # launch six gtfs2enea
    import sys
    sys.path.insert(0, './static/best/swt')
    import gtfs2eneamain
    for idate in range(6):
        gtfs2eneamain.main(mycity, int(str(allgtfs['data'].values[idate])[0:4]), int(str(allgtfs['data'].values[idate])[4:6]), int(str(allgtfs['data'].values[idate])[6:8]), str(allgtfs['file'].values[idate]))

    return render_template("index_prep.html")

@app.route('/launch_input/', methods=['GET', 'POST'])
def best_input():
    print('bestcore')
    print(request.form.getlist('filtercap'))
    filterterminal = False
    if request.form.getlist('filtercap')[0] == 'True': filterterminal = True

    allgtfs = pd.read_csv('./static/best/gtfsdata.csv')
    with open('./static/best/city.csv', "r") as text_file:
        mycity = text_file.read()
    import sys
    sys.path.insert(0, './static/best/swt')
    import bestmain
    bestmain.bestcore(mycity,
                      'mytrips_' + mycity + '_' + str(allgtfs['data'].values[0])[0:4] + '-' + str(allgtfs['data'].values[0])[4:6] + '-' + str(allgtfs['data'].values[0])[6:8] + '.csv',
                      'mytrips_' + mycity + '_' + str(allgtfs['data'].values[1])[0:4] + '-' + str(allgtfs['data'].values[1])[4:6] + '-' + str(allgtfs['data'].values[1])[6:8] + '.csv',
                      'mytrips_' + mycity + '_' + str(allgtfs['data'].values[2])[0:4] + '-' + str(allgtfs['data'].values[2])[4:6] + '-' + str(allgtfs['data'].values[2])[6:8] + '.csv',
                      'mytrips_' + mycity + '_' + str(allgtfs['data'].values[3])[0:4] + '-' + str(allgtfs['data'].values[3])[4:6] + '-' + str(allgtfs['data'].values[3])[6:8] + '.csv',
                      'mytrips_' + mycity + '_' + str(allgtfs['data'].values[4])[0:4] + '-' + str(allgtfs['data'].values[4])[4:6] + '-' + str(allgtfs['data'].values[4])[6:8] + '.csv',
                      'mytrips_' + mycity + '_' + str(allgtfs['data'].values[5])[0:4] + '-' + str(allgtfs['data'].values[5])[4:6] + '-' + str(allgtfs['data'].values[5])[6:8] + '.csv',
                      filterterminal)

    return render_template("index_prep.html")

@app.route('/salva_nel_database/<which>', methods=['GET', 'POST'])
def salvaindb(which):
    from pathlib import Path
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    mydb = DB()
    if request.method == "POST":
        connection = mydb.conn()
        retpage = "index_prep.html"
        if which == '<input>':
            print('Saving input to database')
            name = request.form['fname']
            if name == '':
                print('You have to write a name to save it to database. Retry')
            else:
                fileout = Path('static/best/swt/Out/input_new.xlsx')
                mydatih = pd.read_excel(fileout,sheet_name='dati_orari')
                mydatid = pd.read_excel(fileout,sheet_name='dati_giorno')
                mydatiyt = pd.read_excel(fileout,sheet_name='dati_anno_tecnologia')
                mydatiyl = pd.read_excel(fileout,sheet_name='dati_anno_linea')
                #print(mydatiyl)
                mydatih['version'] = str(name)
                mydatid['version'] = str(name)
                mydatiyt['version'] = str(name)
                mydatiyl['version'] = str(name)
                ### connect to the DB and upload your table (the whole table)
                mydatih.to_sql("dati_orari", con=connection, schema="public",if_exists='append',index=False)
                mydatid.to_sql("dati_giorno", con=connection, schema="public",if_exists='append',index=False)
                mydatiyt.to_sql("dati_anno_tecnologia", con=connection, schema="public",if_exists='append',index=False)
                mydatiyl.to_sql("dati_anno_linea", con=connection, schema="public",if_exists='append',index=False)

        if which == '<gtfs>':
            print('Saving enea gtfs to database')
            name = request.form['gname']
            if name == '':
                print('You have to write a name to save it to database. Retry')
            else:
                allgtfs = pd.read_csv('./static/best/gtfsdata.csv')
                with open('./static/best/city.csv', "r") as text_file:
                    mycity = text_file.read()

                fileout0 = Path('static/best/swt/Out/mytrips_' + mycity + '_' + str(allgtfs['data'].values[0])[0:4] + '-' + str(allgtfs['data'].values[0])[4:6] + '-' + str(allgtfs['data'].values[0])[6:8] + '.csv')
                fileout1 = Path('static/best/swt/Out/mytrips_' + mycity + '_' + str(allgtfs['data'].values[1])[0:4] + '-' + str(allgtfs['data'].values[1])[4:6] + '-' + str(allgtfs['data'].values[1])[6:8] + '.csv')
                fileout2 = Path('static/best/swt/Out/mytrips_' + mycity + '_' + str(allgtfs['data'].values[2])[0:4] + '-' + str(allgtfs['data'].values[2])[4:6] + '-' + str(allgtfs['data'].values[2])[6:8] + '.csv')
                fileout3 = Path('static/best/swt/Out/mytrips_' + mycity + '_' + str(allgtfs['data'].values[3])[0:4] + '-' + str(allgtfs['data'].values[3])[4:6] + '-' + str(allgtfs['data'].values[3])[6:8] + '.csv')
                fileout4 = Path('static/best/swt/Out/mytrips_' + mycity + '_' + str(allgtfs['data'].values[4])[0:4] + '-' + str(allgtfs['data'].values[4])[4:6] + '-' + str(allgtfs['data'].values[4])[6:8] + '.csv')
                fileout5 = Path('static/best/swt/Out/mytrips_' + mycity + '_' + str(allgtfs['data'].values[5])[0:4] + '-' + str(allgtfs['data'].values[5])[4:6] + '-' + str(allgtfs['data'].values[5])[6:8] + '.csv')
                mydati0 = pd.read_csv(fileout0)
                mydati1 = pd.read_csv(fileout1)
                mydati2 = pd.read_csv(fileout2)
                mydati3 = pd.read_csv(fileout3)
                mydati4 = pd.read_csv(fileout4)
                mydati5 = pd.read_csv(fileout5)
                # print(mydatiyl)
                mydati0['version'] = str(name);mydati0['year'] = str(allgtfs['data'].values[0])[0:4];mydati0['month'] = str(allgtfs['data'].values[0])[4:6];mydati0['day'] = str(allgtfs['data'].values[0])[6:8]
                mydati1['version'] = str(name);mydati1['year'] = str(allgtfs['data'].values[1])[0:4];mydati1['month'] = str(allgtfs['data'].values[1])[4:6];mydati1['day'] = str(allgtfs['data'].values[1])[6:8]
                mydati2['version'] = str(name);mydati2['year'] = str(allgtfs['data'].values[2])[0:4];mydati2['month'] = str(allgtfs['data'].values[2])[4:6];mydati2['day'] = str(allgtfs['data'].values[2])[6:8]
                mydati3['version'] = str(name);mydati3['year'] = str(allgtfs['data'].values[3])[0:4];mydati3['month'] = str(allgtfs['data'].values[3])[4:6];mydati3['day'] = str(allgtfs['data'].values[3])[6:8]
                mydati4['version'] = str(name);mydati4['year'] = str(allgtfs['data'].values[4])[0:4];mydati4['month'] = str(allgtfs['data'].values[4])[4:6];mydati4['day'] = str(allgtfs['data'].values[4])[6:8]
                mydati5['version'] = str(name);mydati5['year'] = str(allgtfs['data'].values[5])[0:4];mydati5['month'] = str(allgtfs['data'].values[5])[4:6];mydati5['day'] = str(allgtfs['data'].values[5])[6:8]

                ### connect to the DB and upload your table (the whole table)
                mydati0.to_sql("gtfs_summer_w", con=connection, schema="public", if_exists='append', index=False)
                mydati1.to_sql("gtfs_summer_p", con=connection, schema="public", if_exists='append', index=False)
                mydati2.to_sql("gtfs_summer_h", con=connection, schema="public", if_exists='append', index=False)
                mydati3.to_sql("gtfs_winter_w", con=connection, schema="public", if_exists='append', index=False)
                mydati4.to_sql("gtfs_winter_p", con=connection, schema="public", if_exists='append', index=False)
                mydati5.to_sql("gtfs_winter_h", con=connection, schema="public", if_exists='append', index=False)

        if which == '<output>':
            print('Saving output to database')
            name = request.form['fname']
            retpage = "index_bestrun.html"
            if name == '':
                print('You have to write a name to save it to database. Retry')
            else:
                ### also create this kind of connection to the DB to load data into the DB
                fileout1 = Path('static/best/swt/Out', 'output_economici.xlsx')
                outeco = pd.read_excel(fileout1, sheet_name='output_economici')
                outeco['version'] = str(name)
                fileout2 = Path('static/best/swt/Out', 'output_tecnici.xlsx')
                outtec = pd.read_excel(fileout2, sheet_name='output_tecnici')
                outtec['version'] = str(name)
                fileout3 = Path('static/best/swt/Out', 'cp_dati_anno_linea.xlsx')
                outcpal = pd.read_excel(fileout3, sheet_name='cp_dati_anno_linea')
                outcpal['version'] = str(name)
                fileout4 = Path('static/best/swt/Out', 'dati_orari_rete.xlsx')
                outdore = pd.read_excel(fileout4, sheet_name='dati_orari_rete')
                outdore['version'] = str(name)
                fileout5 = Path('static/best/swt/Out', 'cp_dati_orari_cap.xlsx')
                outcap = pd.read_excel(fileout5, sheet_name='cp_dati_orari_cap')
                outcap['version'] = str(name)

                ### connect to the DB and upload your table (the whole table)
                connection = mydb.conn()
                outeco.to_sql("output_economici", con=connection, schema="public", if_exists='append', index=False)
                outtec.to_sql("output_tecnici", con=connection, schema="public", if_exists='append', index=False)
                outcpal.to_sql('cp_dati_anno_linea', con=connection, schema="public", if_exists='append', index=False)
                outdore.to_sql('dati_orari_rete', con=connection, schema="public", if_exists='append', index=False)
                outcap.to_sql('cp_dati_orari_cap', con=connection, schema="public", if_exists='append', index=False)

        print(name)
        mydb.refresh()
        connection.close()

    return render_template(retpage)

@app.route('/carica_da_db/<which>', methods=['GET', 'POST'])
def caricadadb(which):
    from sqlalchemy.sql import text
    from pathlib import Path
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    mydb = DB()
    if request.method == "POST":
        connection = mydb.conn()
        retpage = "index_prep.html"
        if which == '<input>':
            print('Loading from database')
            name = request.form['fselect']
            ### read data from the DB
            query1 = 'SELECT * FROM dati_orari WHERE version=\''+ name + '\' '
            query2 = 'SELECT * FROM dati_giorno WHERE version=\'' + name + '\''
            query3 = 'SELECT * FROM dati_anno_tecnologia WHERE version = \'' + name + '\''
            query4 = 'SELECT * FROM dati_anno_linea WHERE version = \'' + name + '\''
            fileout1 = pd.read_sql_query(text(query1),connection)
            fileout2 = pd.read_sql_query(text(query2),connection)
            fileout3 = pd.read_sql_query(text(query3),connection)
            fileout4 = pd.read_sql_query(text(query4),connection)
            fileout1.drop(columns=['version'],inplace=True)
            fileout2.drop(columns=['version'],inplace=True)
            fileout3.drop(columns=['version'],inplace=True)
            fileout4.drop(columns=['version'],inplace=True)
            writer = pd.ExcelWriter(Path('static/best/swt/Out/input_new.xlsx'), engine='xlsxwriter')
            fileout1.to_excel(writer, sheet_name='dati_orari',index=False)
            fileout2.to_excel(writer, sheet_name='dati_giorno',index=False)
            fileout3.to_excel(writer, sheet_name='dati_anno_tecnologia',index=False)
            fileout4.to_excel(writer, sheet_name='dati_anno_linea',index=False)

            # Close the Pandas Excel writer and output the Excel file.
            writer.close()

        if which == '<gtfs>':
            print('Loading from database')
            name = request.form['gselect']
            ### read data from the DB
            query0 = 'SELECT * FROM gtfs_summer_w WHERE version=\'' + name + '\' '
            query1 = 'SELECT * FROM gtfs_summer_p WHERE version=\'' + name + '\' '
            query2 = 'SELECT * FROM gtfs_summer_h WHERE version=\'' + name + '\' '
            query3 = 'SELECT * FROM gtfs_winter_w WHERE version=\'' + name + '\' '
            query4 = 'SELECT * FROM gtfs_winter_p WHERE version=\'' + name + '\' '
            query5 = 'SELECT * FROM gtfs_winter_h WHERE version=\'' + name + '\' '

            fileout0 = pd.read_sql_query(text(query0), connection)
            fileout1 = pd.read_sql_query(text(query1), connection)
            fileout2 = pd.read_sql_query(text(query2), connection)
            fileout3 = pd.read_sql_query(text(query3), connection)
            fileout4 = pd.read_sql_query(text(query4), connection)
            fileout5 = pd.read_sql_query(text(query5), connection)
            connection.close()

            fileout0.drop(columns=['version', 'year', 'month', 'day'], inplace=True)
            fileout1.drop(columns=['version', 'year', 'month', 'day'], inplace=True)
            fileout2.drop(columns=['version', 'year', 'month', 'day'], inplace=True)
            fileout3.drop(columns=['version', 'year', 'month', 'day'], inplace=True)
            fileout4.drop(columns=['version', 'year', 'month', 'day'], inplace=True)
            fileout5.drop(columns=['version', 'year', 'month', 'day'], inplace=True)

        if which == '<output>':
            print('Loading from database')
            name = request.form['fselect']
            ### read data from the DB
            query1 = 'SELECT * FROM "output_economici" WHERE version=\''+ name + '\' '
            query2 = 'SELECT * FROM "output_tecnici" WHERE version=\'' + name + '\''
            query3 = 'SELECT * FROM "cp_dati_anno_linea" WHERE version = \'' + name + '\''
            query4 = 'SELECT * FROM "dati_orari_rete" WHERE version = \'' + name + '\''
            query5 = 'SELECT * FROM "cp_dati_orari_cap" WHERE version = \'' + name + '\''
            #print(query1)

            #query = 'SELECT * FROM routecheck'
            fileout1 = pd.read_sql_query(text(query1),connection)
            fileout2 = pd.read_sql_query(text(query2),connection)
            fileout3 = pd.read_sql_query(text(query3),connection)
            fileout4 = pd.read_sql_query(text(query4),connection)
            fileout5 = pd.read_sql_query(text(query5),connection)

            fileout1.drop(columns=['version'],inplace=True)
            fileout2.drop(columns=['version'],inplace=True)
            fileout3.drop(columns=['version'],inplace=True)
            fileout4.drop(columns=['version'],inplace=True)
            fileout5.drop(columns=['version'],inplace=True)

            writer = pd.ExcelWriter(Path('static/best/swt/Out/output_economici.xlsx'), engine='xlsxwriter')
            fileout1.to_excel(writer, sheet_name='output_economici',index=False)
            writer.close()
            writer = pd.ExcelWriter(Path('static/best/swt/Out/output_tecnici.xlsx'), engine='xlsxwriter')
            fileout2.to_excel(writer, sheet_name='output_tecnici',index=False)
            writer.close()
            writer = pd.ExcelWriter(Path('static/best/swt/Out/cp_dati_anno_linea.xlsx'), engine='xlsxwriter')
            fileout3.to_excel(writer, sheet_name='cp_dati_anno_linea',index=False)
            writer.close()
            writer = pd.ExcelWriter(Path('static/best/swt/Out/dati_orari_rete.xlsx'), engine='xlsxwriter')
            fileout4.to_excel(writer, sheet_name='dati_orari_rete',index=False)
            writer.close()
            writer = pd.ExcelWriter(Path('static/best/swt/Out/cp_dati_orari_cap.xlsx'), engine='xlsxwriter')
            fileout5.to_excel(writer, sheet_name='cp_dati_orari_cap',index=False)
            writer.close()
            retpage = "index_bestrun.html"

        connection.close()

    return render_template(retpage)

@app.route('/cancella_da_db/<which>', methods=['GET', 'POST'])
def cancdadb(which):
    from sqlalchemy.sql import text
    from pathlib import Path
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    mydb = DB()
    if request.method == "POST":
        retpage = "index_prep.html"
        if which == '<input>':
            name = request.form['fselect1']
            print('Deleting ' + name + ' input from database')
            connection = mydb.conn()
            ### read data from the DB
            query1 = 'DELETE FROM dati_orari WHERE version=\'' + name + '\''
            query2 = 'DELETE FROM dati_giorno WHERE version=\'' + name + '\''
            query3 = 'DELETE FROM dati_anno_tecnologia WHERE version = \'' + name + '\''
            query4 = 'DELETE FROM dati_anno_linea WHERE version = \'' + name + '\''
            print(query1)
            connection.execute(text(query1))
            connection.execute(text(query2))
            connection.execute(text(query3))
            connection.execute(text(query4))
        if which == '<gtfs>':
            name = request.form['gselect1']
            print('Deleting ' + name + ' gtfs from database')
            connection = mydb.conn()
            ### read data from the DB
            query0 = 'DELETE FROM gtfs_summer_w WHERE version=\''+ name + '\''
            query1 = 'DELETE FROM gtfs_summer_w WHERE version=\''+ name + '\''
            query2 = 'DELETE FROM gtfs_summer_w WHERE version=\''+ name + '\''
            query3 = 'DELETE FROM gtfs_summer_w WHERE version=\''+ name + '\''
            query4 = 'DELETE FROM gtfs_summer_w WHERE version=\''+ name + '\''
            query5 = 'DELETE FROM gtfs_summer_w WHERE version=\''+ name + '\''
            connection.execute(text(query0))
            connection.execute(text(query1))
            connection.execute(text(query2))
            connection.execute(text(query3))
            connection.execute(text(query4))
            connection.execute(text(query5))
        if which == '<output>':
            name = request.form['fselect1']
            print('Deleting ' + name + ' output from database')
            connection = mydb.conn()
            ### read data from the DB
            query1 = 'DELETE FROM "output_economici" WHERE version=\''+ name + '\' '
            query2 = 'DELETE FROM "output_tecnici" WHERE version=\'' + name + '\''
            query3 = 'DELETE FROM "cp_dati_anno_linea" WHERE version = \'' + name + '\''
            query4 = 'DELETE FROM "dati_orari_rete" WHERE version = \'' + name + '\''
            query5 = 'DELETE FROM "cp_dati_orari_cap" WHERE version = \'' + name + '\''
            connection.execute(text(query1))
            connection.execute(text(query2))
            connection.execute(text(query3))
            connection.execute(text(query4))
            connection.execute(text(query5))
            retpage = "index_bestrun.html"

        connection.commit()
        mydb.refresh()
        connection.close()

    return render_template(retpage)

@app.route('/launch_best/', methods=['GET', 'POST'])
def launch_best():
    print('best!!')
    DB_input = pd.read_excel('./static/best/swt/out/input_new.xlsx', sheet_name=None)
    import sys
    sys.path.insert(0, './static/best/swt')
    from BEST_2022 import BEST
    best = BEST(DB_input=DB_input)
    # lancio l'esecuzione di best
    DB_output = best.run()
    DB_output["dati_orari_rete"].to_excel('./static/best/swt/out/dati_orari_rete.xlsx', sheet_name='dati_orari_rete', index=False)
    DB_output["cp_dati_anno_linea"].to_excel('./static/best/swt/out/cp_dati_anno_linea.xlsx', sheet_name='cp_dati_anno_linea',
                                             index=False)
    DB_output["output_tecnici"].to_excel('./static/best/swt/out/output_tecnici.xlsx', sheet_name='output_tecnici', index=False)
    DB_output["output_economici"].to_excel('./static/best/swt/out/output_economici.xlsx', sheet_name='output_economici',
                                           index=False)
    DB_output["cp_dati_orari_cap"].to_excel('./static/best/swt/out/cp_dati_orari_cap.xlsx', sheet_name='cp_dati_orari_cap',
                                            index=False)

    # return render_template("index_censuary_and_public_transport.html")
    return render_template("index_bestrun.html")

@app.route('/best_run/', methods=['GET', 'POST'])
def best_run():
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    mydb = DB()
    mydb.refresh()
    return render_template("index_bestrun.html")

@app.route('/best_draw/', methods=['GET', 'POST'])
def best_draw():
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    mydb = DB()
    mydb.refresh()
    return render_template("index_bestdraw.html")

@app.route('/capolinea/', methods=['GET', 'POST'])
def capolinea():
    seldata = 1
    import sys
    sys.path.insert(0, './static/best/swt')
    from dbclass import DB
    from plclass import PL
    mydb = DB()
    draw = PL()
    mycity = request.form['cselect']
    name = request.form['fselect']
    draw.mapdrawcap(mycity, mydb, name, seldata)
    return render_template("index_bestdraw.html")




if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True, threaded=True, use_reloader=False)

# ---------------------------------------- #
############################################

##----> to deploy the application run:
###---> python main_2022.py

############################################
# ---------------------------------------- #
