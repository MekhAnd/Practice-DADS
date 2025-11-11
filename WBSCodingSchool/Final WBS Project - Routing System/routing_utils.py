import os
import folium
import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import polyline

from folium import PolyLine
from time import sleep
from requests import RequestException
from io import StringIO
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import SpectralClustering
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import haversine_distances

from pulp import LpProblem, LpMinimize, LpVariable, LpStatus, value, lpSum
from scipy.spatial.distance import cdist



def columns_data_type(df):
    """ Checking if the dataframe has incorrect and string 'null', 'Null', 'NA'.\n 
        For Na values in some columns. And convert Lat and Lon into numeric.\n 
        Parameters: dataframe\n
        Output: Corrected dataframe
    """
    # str
    for col in ["CustomerCountry", "CustomerCity", "CustomerStreet", "CustomerNumer"]:
        df[col] = df[col].replace({'null': pd.NA, 'Null': pd.NA, '': pd.NA})
        df[col] = df[col].astype(str)

    # Group
        df["Group"] = df['Group'].fillna(0)

    # numeric
    for col in ["CustomerLon", "CustomerLat"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def isna_indexes_list(df):
    """ Checks for required fields in a data frame with NUll values.\n 
        Creates a log file with additional information.\n
        Parameters: dataframe\n
        Output: -
    """

    columns_name_list = []
    null_index_list = []
    messages_list = []


    for column in df.select_dtypes(exclude="number").columns:
        missing_mask = df[column].isna()
        missing_indexes = df.loc[missing_mask].index.tolist()

        if len(missing_indexes)>0:
            columns_name_list.append(column)
            null_index_list.extend(missing_indexes)
            messages_list.append(f"Column {column} has missing values at indexes {missing_indexes}")
        
            # print(f"{column} => {missing_indexes}")
    rows_to_drop = sorted(list(set(null_index_list)))

    df["CustomerLon"] = df['CustomerLon'].fillna(0)
    df["CustomerLat"] = df['CustomerLat'].fillna(0)
            

    
    if len(rows_to_drop)>0:
        df = df.drop(index=rows_to_drop)

        print(f"\nData Cleaning:\n Total rows deleted: {len(rows_to_drop)}\n Details:\n")
        for msg in messages_list: 
            print(f"- {msg} and was deleted \n")
    
    else:
        print(f"\nData Cleaning:\n **************************************\nPhase completed\
                            verified {df.shape[0]} rows\n**************************************\n")
    

def check_zero_geo(df):
    """ Checks for lat and lon coordinates. Creates a list with the indexes of rows where\n 
        these coordinates were not finden or were 0\n
        Parameters: dataframe\n
        Output: list of indexes\n
    """
    missing_indexes = []
    zero_mask = (df["CustomerLat"]==0) | (df["CustomerLon"]==0)
    missing_indexes = df.loc[zero_mask].index.tolist()
    

    return missing_indexes

def geoposition_geocode_api (city, str_name, num, GEOCODE_API):
    """ Using the API, it fills in the missing geospatial coordinates. !!!Take a 1 sec pause betwee each call!!!\n
        Parameters: city = city name (String), str_name = street name (String), num = hause number (String)\n
        Output: List of coordinates String [lat, lon]\n
    """

    geo_lat = 0
    geo_lon = 0
    
    sleep(1) # because of server restrictions
    
    url = f"https://geocode.maps.co/search?city={city}&street={num}+{str_name}&api_key={GEOCODE_API}"
    try:
        geo_response = requests.get(url)
        if geo_response.status_code == 200:
            geo_JSON = geo_response.json()  #{'error': {'code': 500, 'message': 'Could not get places for search terms.'}}
            if len(geo_JSON) == 0:
                lat = 0
                lon = 0
            else:
                lat = geo_JSON[0]["lat"]
                lon = geo_JSON[0]["lon"]
            geo_lat = lat
            geo_lon = lon
        else:
            print(geo_response.status_code)
        
    except RequestException:
        lat = geo_JSON[0]["lat"]
        lon = geo_JSON[0]["lon"]
        pass
    return geo_lat, geo_lon

def update_row_info(df, index, column, value):
    """ Update cell in certain df by index and column
    """
    df.loc[df["index"]==index, column] = value

def get_geo_data(df, GEOCODE_API): 
    """Using the geoposition_geocode_api and update_row_info functions, it fills in the missing geospatial coordinates in the table\n
       Parameters: dataframe\n
       Output: -
    """
   
    missing_geo_indexes = check_zero_geo(df)
    geo_table = df.loc[df["index"].isin(missing_geo_indexes)]

    index_list = list(geo_table["index"]) 
    city_list = list(geo_table["CustomerCity"])
    str_list = list(geo_table["CustomerStreet"])
    num_list = list(geo_table["CustomerNumer"])

    geo_lat_list = []
    geo_lon_list = []
    
    for i in range (geo_table.shape[0]):
        city = city_list[i].replace(" ", "+")
        str_name= str_list[i].replace(" ", "+")
        geo_lat_position, geo_lon_position = geoposition_geocode_api (city, str_name, num_list[i], GEOCODE_API)
        geo_lat_list.append(geo_lat_position)
        geo_lon_list.append(geo_lon_position)

    for i in range(len(geo_lat_list)):
        if geo_lat_list[i] != 0 and geo_lon_list[i] != 0:
            update_row_info(df, index_list[i], "CustomerLat", geo_lat_list[i] )
            update_row_info(df, index_list[i], "CustomerLon", geo_lon_list[i] )
            
        else:
            print(f"Errors in positioning index {index_list[i]}")
            

def distance_duration_inventor(lon_start, lat_start, lon_finish, lat_finish, ORS_API_KEY):
    """ Using the API, it takes distance and duration (according to the road network) between two positions\n
        Parameters: clon_start, lat_start, lon_finish, lat_finish\n
        Output: List of distance, duration [distance, duration]\n
    """
  
    url = "http://localhost:8082/ors/v2/directions/driving-car"
    #outer_url = "https://api.openrouteservice.org/v2/directions/driving-car" # for API endpoint

    payload = {
        "coordinates":[
            [lon_start, lat_start],
            [lon_finish, lat_finish]
        ],
    }

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        # 'Authorization': ORS_API_KEY, # for API endpoint
        'Content-Type': 'application/json; charset=utf-8'}

    try:
        response = requests.post(url, json=payload, timeout=10)
        # response = requests.post(outer_url, json=payload, headers=headers, timeout=120) # for API endpoint
        response.raise_for_status()
        data_routing = response.json()

        distance = data_routing["routes"][0]["summary"]["distance"]
        duration = data_routing["routes"][0]["summary"]["duration"]
        
        return distance, duration
         
    except requests.exceptions.RequestException as e:
        print(f"Error: Request is not seccessful.")
        print(f"Error: {e}")

        try:
            error_details = response.json()
            print("\nThe Error details (ORS):")
            print(json.dumps(error_details, indent=2, ensure_ascii=False)) 
        except json.JSONDecodeError:
            print("Server did not return JSON with Error details.")
        
    except requests.exceptions.RequestException as e:
        print(f"\nConnection Error: {e}")


def get_geometry(locations_list, day, route, ORS_API_KEY):
    """ Using the API, it takes list coordinates on the route (according to the road network) between two positions\n
        Parameters: list of lall locations on the road\n
        Output: List of distance, duration [distance, duration]\n
    """

    len_list = len(locations_list)
    
    radius_list = [50]*len_list
    payload = {
        "coordinates":locations_list,
        "profile": "driving-car",
        "radiuses": radius_list,
    }
    
    url = "http://localhost:8082/ors/v2/directions/driving-car/json" # for local inctance
    #outer_url = "https://api.openrouteservice.org/v2/directions/driving-car" # for API endpoint

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        # 'Authorization': ORS_API_KEY, # for API endpoint
        'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120) # for local inctance
        # response = requests.post(outer_url, json=payload, headers=headers, timeout=120) # for API endpoint
        response.raise_for_status()

        
        decode_geometry = response.json()["routes"][0]["geometry"]
        decoded_points = polyline.decode(decode_geometry)
        
        return decoded_points
    except requests.exceptions.RequestException as e:
        print(f"--- ORS FAIL FOR ROUTE {route}, DAY {day} ---")
    
        try:
            print(f"HTTP Status Code: {e.response.status_code}")
            print(f"ORS Response Content (Error Details): {e.response.text}")
        except:
            # Це спрацює, якщо помилка є чистим таймаутом або ConnectionError
            print(f"Error is likely a ReadTimeout or ConnectionError.")
            print(f"Full Error Type: {type(e)}")
        
        return None

def drawing_route(locations_list, points, route, day):
    """Draws daily routes on the map\n
       Parameters: locations_list:list with geospatial coordinates, points:list with route geometry,\n
       route number, day number
    """
    
    if points is None or not points:
        print(f"WARNING: Skipping map draw for Route {route} Day {day}. No valid geometry was returned.")

    map_location = [locations_list[0][1], locations_list[0][0]]
    
    daily_route_map = folium.Map(
        tiles="cartodb positron",
        location=map_location,
        zoom_start=11
    )
    counter = 0
    for i in locations_list:
        icon_color = 'darkred' if i != 0 else 'darkgreen'
        icon_type = 'circle' if i != 0 else 'flag'

        folium.Marker(
                    location=[i[1],i[0]],
                    popup=folium.Popup(f"Point {counter}", parse_html=True, max_width=100),
                    icon=folium.Icon(color=icon_color, icon=icon_type, prefix='fa')
                    ).add_to(daily_route_map)
        counter +=1
    
    if points:
        folium.PolyLine(
            points,
            color="darkblue",
            weight = 4,
            opacity = 0.8,
            tooltip=f"Route {route}, Day {day}").add_to(daily_route_map)
    return     daily_route_map


def drawing_points_map(df):
    colors = ['darkred', 'darkblue', 'gray', 'purple', 'blue', 'cadetblue', 'orange', 'darkpurple', 'black',  
              'darkgreen', 'lightblue', 'lightgreen','lightred', 'beige','lightgray','white', 'red','pink', 'green']
    
    avg_lat = list(df[["CustomerLat"]].mean())
    avg_lon = list(df[["CustomerLon"]].mean())
    map_folium_route = folium.Map(location=(avg_lat[0], avg_lon[0]), tiles="cartodb positron", zoom_start=11)

    for route in df["Route"].unique():
        tmprout_df = df.loc[df["Route"]==route]
                        
        lat_list = list(tmprout_df["CustomerLat"])
        lon_list = list(tmprout_df["CustomerLon"])

        for marker in range(len(lat_list)):
            folium.Marker(
                location = [lat_list[marker], lon_list[marker]],
                icon= folium.Icon(color=colors[tmprout_df.iloc[marker]["Route"]])
            ).add_to(map_folium_route)
    
    return map_folium_route

def final_table_constructor(final_routes, customer_base, START_POINT_LAT_WAREHOUSE, START_POINT_LON_WAREHOUSE):

    if final_routes.empty:
        print("UPS!")
        return pd.DataFrame()

    columns_to_select = ["rout", "day", "key_finish", "FinishPoint", "distance", "duration"]
    upadated_customer_info = final_routes[columns_to_select]
    upadated_customer_info = upadated_customer_info.rename(columns={"key_finish":"index","rout":"Route", "day":"Day", "FinishPoint":"CustomerFullAdd"})
    columns_order = ["Route", "Day",  "index", "distance","duration", "CustomerFullAdd"]
    upadated_customer_info = upadated_customer_info[columns_order]

    upadated_customer_info = upadated_customer_info.merge(
        customer_base.loc[:,["index", "CustomerLat", "CustomerLon"]],
        on="index",
        how = "left"
    )
    upadated_customer_info["CustomerLat"] = upadated_customer_info["CustomerLat"].fillna(START_POINT_LAT_WAREHOUSE)
    upadated_customer_info["CustomerLon"] = upadated_customer_info["CustomerLon"].fillna(START_POINT_LON_WAREHOUSE)


    return upadated_customer_info

def general_overview(df):
    general_overview_df = df.groupby("Route").agg(
        {   "index": "count",
            "distance": "sum",
            "duration":"sum",}
        )

    
    def convert_km(meters):
        km = meters/1000

        return round(km, 2)
    
    def convert_route(route):
        route_num = route + 1
        return route_num
    
    general_overview_df["duration"] = general_overview_df["duration"].apply(convert_sec) 
    general_overview_df["distance"] = general_overview_df["distance"].apply(convert_km) 
    general_overview_df["Route #"] = general_overview_df.index
    general_overview_df["Route #"] = general_overview_df["Route #"].apply(convert_route)


    general_overview_df = general_overview_df.rename(columns = {"index":"Number of Customers", "distance":"Distance (km)", "duration": "Duration"})
    general_overview_df = general_overview_df[["Route #", "Number of Customers", "Distance (km)", "Duration"]]

    return general_overview_df

def convert_sec(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)

def kmeans_model(df, n_clust):
    df = df.loc[:,["CustomerLon", "CustomerLat"]]
    kmeans_model = KMeans(
        n_clusters=n_clust,
        random_state=42
    )
    kmeans_model.fit(df)
    return kmeans_model.labels_

def solve_capacity_constrained_assignment(cost_matrix, size_min_R, size_max_R):
    # will not show on presentation!!!

    # print(f"\n--- Діагностика LP Моделі ---")
    # print(f"Кількість точок (N): {cost_matrix.shape[0]}")
    # print(f"Кількість кластерів (K): {cost_matrix.shape[1]}")
    # print(f"Обмеження потужності: [{size_min_R}, {size_max_R}]")
    avg_size = cost_matrix.shape[0] / cost_matrix.shape[1]
    # print(f"Середній розмір кластера: {avg_size:.2f}")
    prob = LpProblem("Capacity_Constrained_Assignment", LpMinimize)
    x= LpVariable.dicts("Assignment", ((i, j) for i in range(cost_matrix.shape[0]) for j in range(cost_matrix.shape[1])), cat='Binary')

    prob += lpSum(x[i, j] * cost_matrix[i, j] for i in range(cost_matrix.shape[0]) 
                    for j in range(cost_matrix.shape[1])), "Total Distance Cost"

    for i in range(cost_matrix.shape[0]):
            prob += lpSum(x[i, j] for j in range(cost_matrix.shape[1])) == 1, f"Point_{i}_Assigned_Once"

    for j in range(cost_matrix.shape[1]):
            prob += lpSum(x[i, j] for i in range(cost_matrix.shape[0])) >= size_min_R, f"Cluster_{j}_Min_Capacity"
            # Максимальна потужність
            prob += lpSum(x[i, j] for i in range(cost_matrix.shape[0])) <= size_max_R, f"Cluster_{j}_Max_Capacity"

    prob.solve() 
    if LpStatus[prob.status] == "Optimal":
        # 1. Отримання фінальних призначень
        final_assignments = np.zeros(cost_matrix.shape[0], dtype=int)
        for i in range(cost_matrix.shape[0]):
            assigned_j = -1
            for j in range(cost_matrix.shape[1]):
                # PuLP зберігає результат у varValue. Перевіряємо, чи змінна дорівнює 1.0
                # Якщо varValue близьке до 1.0, це означає, що точка i призначена кластеру j
                if x[i, j].varValue == 1.0: 
                    assigned_j = j
                    break
                final_assignments[i] = assigned_j

        # 2. Отримання мінімальної загальної вартості
        total_cost = value(prob.objective)

        print(f"\n✅ Модель LP вирішена. Статус: {LpStatus[prob.status]}")
        print(f"   Мінімальна загальна вартість: {total_cost:.2f}")
        
        print(len(final_assignments))
      
        return final_assignments, total_cost
    else:
        # print(f"\n❌ Модель LP не знайшла оптимального рішення. Статус: {LpStatus[prob.status]}")
        return None, None # Повертаємо None, якщо рішення не знайдено
    

def kmeans_model_balanced(df, n_clust):
    # will not present
    print(f"LINE 445 kmeans_model_balanced, n-clust = {n_clust}")
    df = df.loc[:, ["CustomerLon", "CustomerLat"]]

    kmeans_model = KMeans(
        n_clusters=n_clust,
        random_state=42
    )
    kmeans_model.fit_predict(df)

    centroids = kmeans_model.__dict__["cluster_centers_"]
    list_cast_lon = df["CustomerLon"]
    list_cast_lat = df["CustomerLat"]

    points = []

    for i in range(len(list_cast_lat)):
        points.append([list(list_cast_lat)[i], list(list_cast_lon)[i]])

    size_min_R = int((df.shape[0]/n_clust)-(df.shape[0]/n_clust)*0.1)
    size_max_R = int((df.shape[0]/n_clust)+(df.shape[0]/n_clust)*0.1)

    print(f"LP Параметри: N={df.shape[0]}, K={n_clust}, Min={size_min_R}, Max={size_max_R}")
    cost_matrix = cdist(points, centroids, metric="euclidean")
    print(len(cost_matrix))
    fa = solve_capacity_constrained_assignment(cost_matrix, size_min_R, size_max_R)

    return fa

def dbscan_model(df):
    df = df.loc[:, ["CustomerLon", "CustomerLat"]]
    clustering_DBSCAN = DBSCAN(eps=0.0119, min_samples=10)
    clustering_DBSCAN.fit(df)
    return clustering_DBSCAN.labels_

def spcl_model(df):
    df = df.loc[:, ["CustomerLon", "CustomerLat"]]
    clustering_SPCL = SpectralClustering(n_clusters=5, eigen_solver="arpack",  assign_labels='discretize', n_init = 20,random_state=42)
    clustering_SPCL.fit(df)
    return clustering_SPCL.labels_

def  hdbscan_model(df):
    df = df.loc[:, ["CustomerLon", "CustomerLat"]]
    clustering_HDBSCAN = HDBSCAN(min_cluster_size= 11, min_samples = 8)
    clustering_HDBSCAN.fit(df)
    return clustering_HDBSCAN.labels_