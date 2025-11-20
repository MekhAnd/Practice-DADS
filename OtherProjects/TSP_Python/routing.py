import os
from pathlib import Path
import pandas as pd
from utils import *

API_GEO_KEY = os.getenv("GEO_CODE_API")
ORS_API_KEY = os.getenv("ORS_API_KEY")

# 50.16390840075144
# 8.684188661755403

ROUTES = int(input("Enter number of vehicles: "))
WORKING_DAYS = int(input("Enter number of working days: "))
START_POINT_LAT_WAREHOUSE = float(input("Enter start/finish point latitude: "))
START_POINT_LON_WAREHOUSE = float(input("Enter start/finish point longitude: "))

local_path_tables = "./Tables/"
local_path_maps = "./Maps/"

if not os.path.exists(local_path_tables):
    os.makedirs(local_path_tables)
if not os.path.exists(local_path_maps):
    os.makedirs(local_path_maps)

customer_base = pd.read_csv("customer_db.csv")
customer_base = columns_data_type(customer_base)
log_txt = isna_indexes_list(customer_base)
missing_geo_indexes = check_zero_geo(customer_base)

customer_base = customer_base.reset_index()
geo_table = customer_base.loc[customer_base["index"].isin(missing_geo_indexes)]

if "Unnamed: 0.1" in customer_base.columns:
    customer_base = customer_base.drop(columns=["Unnamed: 0.1"])

if "Unnamed: 0" in customer_base.columns:
    customer_base = customer_base.drop(columns=["Unnamed: 0"])



get_geo_data(geo_table, API_GEO_KEY)

lon_null_mask = customer_base["CustomerLon"]==0
lat_null_mask = customer_base["CustomerLat"]==0
nan_mask = customer_base["CustomerLat"] == "NaN"

customer_base = customer_base.drop(index=customer_base.loc[lon_null_mask | lat_null_mask]["index"])
customer_base = customer_base.drop(index=customer_base.loc[nan_mask]["index"])

customer_base["CustomerLat"] = pd.to_numeric(customer_base["CustomerLat"], errors="coerce")
customer_base["CustomerLon"] = pd.to_numeric(customer_base["CustomerLon"], errors="coerce")

map_path_name = "./Maps/all_points.html"
map_drawing(customer_base, map_path_name)


if "Unnamed: 0.1" in customer_base.columns:
    customer_base = customer_base.drop(columns=["Unnamed: 0.1"])

if "Unnamed: 0" in customer_base.columns:
    customer_base = customer_base.drop(columns=["Unnamed: 0"])
  
routes_labels = kmeans_model(customer_base, ROUTES)
customer_base["ROUTES"] = routes_labels

customer_base.to_csv("./Tables/all_routes.csv")

map_path_name = "./Maps/all_points_routes.html"
map_drawing(customer_base, map_path_name)

day_info = []

for rout in range(ROUTES):
        routes_mask = customer_base["ROUTES"] == rout

        tmp_rout_df = customer_base.loc[routes_mask].select_dtypes(include="number").drop(columns=["index", "Group"])
        day_labels = kmeans_model(tmp_rout_df, WORKING_DAYS)
        tmp_rout_df["DAY"] = day_labels
  
        day_info.append(tmp_rout_df)

daily_routes = pd.concat(day_info)
daily_routes = daily_routes.drop(columns=["CustomerLon", "CustomerLat", "ROUTES"]).reset_index()
customer_base = customer_base.merge(
    daily_routes,
    on="index",
    how="left"
)

customer_base.to_csv("./Tables/all_routes_days.csv")

key_start_list = []
key_finish_list = []
distance_list = []
duration_list = []
# index_ = []# ??????
days_list = []
rout_list = []

distance_dict = {
    "day":days_list,
    "rout":rout_list,
    "key_start":key_start_list,
    "key_finish":key_finish_list,
    "distance":distance_list,
    "duration":duration_list
}

for rout in range(ROUTES):
    routes_mask = customer_base["ROUTES"]==rout
    one_rout_df = customer_base.loc[routes_mask]
    for day in range(WORKING_DAYS):
        day_mask = one_rout_df["DAY"]==day
        one_day_rout_df = one_rout_df.loc[day_mask]
        one_day_rout_df = one_day_rout_df.set_index("index")
        key_list = list(one_day_rout_df.index)
        lon_list = list(one_day_rout_df["CustomerLon"])
        lat_list = list(one_day_rout_df["CustomerLat"])
        day_list = list(one_day_rout_df["DAY"])
        routes_list = list(one_day_rout_df["ROUTES"])
        counter = 0

        while counter <= len(key_list):
            if counter == 0:
                for i in range(len(key_list)): 
                    days_list.append(day_list[i])
                    rout_list.append(routes_list[i])
                    key_start_list.append(-1)
                    key_finish_list.append(key_list[i])
                    distance, duration = distance_duration_inventor(START_POINT_LON_WAREHOUSE, 
                                                                START_POINT_LAT_WAREHOUSE, 
                                                                lon_list[i], lat_list[i],ORS_API_KEY)
                    distance_list.append(distance)
                    duration_list.append(duration)
            elif counter == len(key_list):
                for i in range(len(key_list)):   
                    days_list.append(day_list[i])
                    rout_list.append(routes_list[i])      
                    key_start_list.append(key_list[i])
                    key_finish_list.append(-1)
                    distance, duration = distance_duration_inventor(lon_list[i], lat_list[i], 
                                                                    START_POINT_LON_WAREHOUSE, 
                                                                    START_POINT_LAT_WAREHOUSE, ORS_API_KEY)
                    distance_list.append(distance)
                    duration_list.append(duration)
            else:
                for i in range(len(key_list)):  
                    for j in range(len(key_list)):
                        if key_list[j] != key_list[i]:
                            days_list.append(day_list[i])
                            rout_list.append(routes_list[i])
                            key_start_list.append(key_list[i])
                            key_finish_list.append(key_list[j])
                            distance, duration = distance_duration_inventor(lon_list[i], lat_list[i], 
                                                                            lon_list[j], lat_list[j], ORS_API_KEY)
                            distance_list.append(distance)
                            duration_list.append(duration)
            counter +=1    

distance_df = pd.DataFrame(distance_dict)
distance_df = distance_df.drop_duplicates() 
distance_df_copy = distance_df.copy()

key_start_list = []
key_finish_list = []
sequence_list = []

for route in range(ROUTES):
    route_mask = distance_df_copy["rout"]==route
    for day in range(WORKING_DAYS):
        day_mask = distance_df_copy["day"] == day
        route_day_table = distance_df_copy.loc[route_mask & day_mask]
        keys_list = list(set(route_day_table["key_start"]))
        start_point = -1
        for key in keys_list:
            start_mask = route_day_table["key_start"] == start_point
            route_day_table_start = route_day_table.loc[start_mask]

            if route_day_table.shape[0] > 1:
                not_warehouse_mask =  route_day_table_start["key_finish"] != -1
                route_day_table_start = route_day_table_start.loc[not_warehouse_mask]
                minimum_dist_mask = (route_day_table_start["distance"] == route_day_table_start["distance"].min()) 
                route_day_table_start = route_day_table_start.loc[minimum_dist_mask]
                next_point = route_day_table_start    
            else: 
                minimum_dist_mask = (route_day_table_start["distance"] == route_day_table_start["distance"].min()) 
                next_point = route_day_table_start.loc[minimum_dist_mask]
            
            sequence_list.append(next_point)
            finish_point = list(route_day_table_start.loc[minimum_dist_mask]["key_finish"])[0]
            finish_mask = route_day_table["key_finish"] == finish_point
            
            #### delete all key start points
            route_day_table = route_day_table.drop(index=route_day_table.loc[start_mask].index)
            route_day_table = route_day_table.drop(index=route_day_table.loc[finish_mask].index)
            start_point = finish_point
routes_df = pd.concat(sequence_list)

final_routes = routes_df.copy()
final_routes["StartPoint"]=""
final_routes["FinishPoint"]=""

for i in range(final_routes.shape[0]):

    key_start = final_routes.iloc[i, 2]
    key_finish = final_routes.iloc[i, 3]
    start_mask = customer_base["index"]  == key_start
    
    city_series = customer_base.loc[start_mask]["CustomerCity"]
    
    if not city_series.empty:
        city = city_series.squeeze()
        street = customer_base.loc[start_mask]["CustomerStreet"].squeeze()
        number = customer_base.loc[start_mask]["CustomerNumer"].squeeze()

        final_routes.iloc[i, 6] = (f"{city}, {street}, {number}")
    else:
        key_for_address = final_routes.iloc[i]["key_start"] 
        
        if key_for_address == -1:
            address_string = "Start/End Point: Warehouse"
            final_routes.iloc[i, 6] = address_string
        else:
            print("Error in adressing") 
    
    finish_mask = customer_base["index"] == key_finish
    city_series = customer_base.loc[finish_mask]["CustomerCity"]

    if not city_series.empty:
        city = city_series.squeeze()
        street = customer_base.loc[finish_mask]["CustomerStreet"].squeeze()
        number = customer_base.loc[finish_mask]["CustomerNumer"].squeeze()

        final_routes.iloc[i, 7] = (f"{city}, {street}, {number}")
    else:
        key_for_address = final_routes.iloc[i]["key_finish"] 
        if key_for_address == -1:
            address_string = "Start/End Point: Warehouse"
            final_routes.iloc[i, 7] = address_string
        else:
            print("Error in adressing")

column_order = ["day","rout", "key_start", "StartPoint", "key_finish", "FinishPoint", "distance", "duration"]
final_routes = final_routes.reindex(columns=column_order)

final_routes["distance_km"] = round(final_routes["distance"]/1000, 2)
final_routes["duration_min"] = round(final_routes["duration"]/60, 2)

final_routes_geometry = routes_df.copy()
final_routes_geometry["lon"] = 0.0 #4
final_routes_geometry["lat"] = 0.0 #5

for i in range(final_routes_geometry.shape[0]):
    key_start = final_routes_geometry.iloc[i, 2]

    start_mask = customer_base["index"] == key_start
    customer_loc = customer_base.loc[start_mask]["CustomerLon"] #.iloc[0]
    if not customer_loc.empty:
        start_mask = customer_base["index"] == key_start
        
        final_routes_geometry.iloc[i, 6] = customer_base.loc[start_mask]["CustomerLon"].iloc[0]
        final_routes_geometry.iloc[i, 7] = customer_base.loc[start_mask]["CustomerLat"].iloc[0]
    else:
        if key_for_address == -1:
            final_routes_geometry.iloc[i, 6] = START_POINT_LON_WAREHOUSE
            final_routes_geometry.iloc[i, 7] = START_POINT_LAT_WAREHOUSE
        else:
            print("Error in location") 

route_day_locations_list = []
points_list = []
routes_list_=[]
days_list_ = []

geometries_dict = {
    "Route":routes_list_,
    "Day": days_list_,
    "locations": route_day_locations_list,
    "points": points_list,
}

for route in range(ROUTES):
    route_mask = final_routes_geometry["rout"] == route

    for day in range(WORKING_DAYS):
        day_mask = final_routes_geometry["day"] == day
        tmp_table = final_routes_geometry.loc[route_mask&day_mask]
        route_day_lon_list = list(tmp_table["lon"])
        route_day_lat_list = list (tmp_table["lat"])
        locations_list = []
        for i in range(len(route_day_lon_list)):
            locations_list.append([route_day_lon_list[i], route_day_lat_list[i]])

        locations_list.append([route_day_lon_list[0], route_day_lat_list[0]])
        points = get_geometry(locations_list, day, route, ORS_API_KEY)
        route_day_locations_list.append(locations_list)
        points_list.append(points)
        routes_list_.append(route)
        days_list_.append(day)

        drawing_route(locations_list, points, route, day)
        general_overview(final_routes_geometry.loc[route_mask], route)
        

points_df_ = pd.DataFrame(geometries_dict)
final_routes_ = final_table_constructor(final_routes, customer_base, START_POINT_LAT_WAREHOUSE, START_POINT_LON_WAREHOUSE)

final_routes_.to_csv("./Tables/routes_sequences.csv")