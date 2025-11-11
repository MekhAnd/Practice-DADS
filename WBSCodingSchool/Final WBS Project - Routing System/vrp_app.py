import streamlit as st
import pandas as pd
import numpy as np 
from streamlit_folium import st_folium
from streamlit_mermaid import st_mermaid
from routing_utils import *




if 'final_routes_' not in st.session_state: 
    st.session_state.final_routes_ = None
if "geo_points_df_" not in st.session_state:
    st.session_state.geo_points_df_ = None
if "BALANCED" not in st.session_state:
    st.session_state.BALANCED = None
if "DBSCAN" not in st.session_state:
    st.session_state.DBSCAN = None
if "SPCL" not in st.session_state:
    st.session_state.SPCL = None
if "HDBSCAN" not in st.session_state:
    st.session_state.HDBSCAN = None


try:
    API_GEO_KEY = st.secrets["GEO_CODE_API"]
    ORS_API_KEY = st.secrets["ORS_API_KEY"]
except KeyError:
    API_GEO_KEY = None
    st.error("API key was not found!")

@st.cache_data
def routing_workflow(customer_base, API_GEO_KEY, ROUTES, START_POINT_LON_WAREHOUSE, 
                        START_POINT_LAT_WAREHOUSE, WORKING_DAYS,ORS_API_KEY,
                        _columns_data_type = columns_data_type, 
                        _isna_indexes_list = isna_indexes_list, 
                        _check_zero_geo = check_zero_geo, 
                        _get_geo_data=get_geo_data, 
                        _distance_duration_inventor = distance_duration_inventor,
                        _get_geometry = get_geometry, 
                        _drawing_route = drawing_route, 
                        _final_table_constructor = final_table_constructor,
                        
                        # _kmeans_model = kmeans_model 
                    ):
    
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

    if "Unnamed: 0.1" in customer_base.columns:
        customer_base = customer_base.drop(columns=["Unnamed: 0.1"])

    if "Unnamed: 0" in customer_base.columns:
        customer_base = customer_base.drop(columns=["Unnamed: 0"])

    customer_base_BALANCED = customer_base.copy()
    customer_base_DBSCAN = customer_base.copy()
    customer_base_SPCL = customer_base.copy()
    customer_base_HDBSCAN = customer_base.copy()

        
    routes_labels = kmeans_model(customer_base, ROUTES)
    customer_base["ROUTES"] = routes_labels

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

    column_order = ["day","rout",	"key_start","StartPoint", "key_finish","FinishPoint","distance","duration"]
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
        for day in range(WORKING_DAYS):
            
            route_mask = final_routes_geometry["rout"] == route
            day_mask = final_routes_geometry["day"] == day
            tmp_table = final_routes_geometry.loc[route_mask&day_mask]
            route_day_lon_list = list(tmp_table["lon"])
            route_day_lat_list = list (tmp_table["lat"])
            locations_list = []
            for i in range(len(route_day_lon_list)):
                locations_list.append([route_day_lon_list[i], route_day_lat_list[i]])

            locations_list.append([route_day_lon_list[0], route_day_lat_list[0]])
            # print(f"ROUTE {route}, DAY {day}, pass location list len - {len(locations_list)}")
            points = get_geometry(locations_list, day, route, ORS_API_KEY)
            route_day_locations_list.append(locations_list)
            points_list.append(points)
            routes_list_.append(route)
            days_list_.append(day)
            

    points_df_ = pd.DataFrame(geometries_dict)
    final_routes_ = final_table_constructor(final_routes, customer_base, selected_geo_lat, selected_geo_lon)
    

    # fa_balanced_ = kmeans_model_balanced(customer_base_BALANCED, 5)
    # customer_base_BALANCED["Route"] = fa_balanced_[0]
    
    customer_base_DBSCAN["Route"] = dbscan_model(customer_base_DBSCAN)

    customer_base_SPCL["Route"] = spcl_model(customer_base_SPCL)
    customer_base_HDBSCAN["Route"] = hdbscan_model(customer_base_HDBSCAN)

    return final_routes_, points_df_, customer_base_BALANCED, customer_base_DBSCAN, customer_base_SPCL, customer_base_HDBSCAN



PAGE_ICON = "icons/route.png"

st.set_page_config(
    page_title="Vehicle routing problem",
    page_icon=PAGE_ICON,
    layout="wide",
    ) 

st.title("🚚 Routing optimisation and VRP")
st.sidebar.title("Navigation")

PAGES = [
    "Main",
    "Settings",
    "Tables",
    "Routes Maps",
    "Statistic",
    "Other UML and models",
    "About"
]

selection = st.sidebar.radio("Go To:", PAGES)

if selection == "Main":
    st.header("Main: Routing optimisation and VRP")
    image, markdown = st.columns([1,4])
    st.markdown("*Vehicle Routing Problem*")
    with image:
        st.image("icons\pixlr-image-generator-6909e4a52026e1eae1d94f64.png", width=250)
    with markdown:
        st.markdown("""
                    The vehicle routing problem (VRP) is a problem in combinatorial optimization, computer science, and integer programming that 
                    asks: “What is the optimal set of routes for a fleet of vehicles to deliver to a given group of customers?”
                    This problem, or the traveling salesman problem, was first mentioned in 1832 in the German book “Advice from an Old Traveling Salesman.”
                     In the 1930s, the mathematical problem was first formulated by Carl Menger, who called it the problem of the messenger, and later the 
                    problem was called the traveling salesman problem.
        
                    The problem then appeared as a truck dispatching problem in an article by George Dantzig and John Ramzer in 1959, 
                    where it was applied to gasoline delivery. Often, the context is the delivery of goods located in a central warehouse to 
                    customers who have ordered such goods.
        
                    However, variants of the problem consider, for example, the collection of solid waste and the transportation of elderly and
                     sick people to and from medical facilities. The standard goal of the TSP is to minimize the total cost of the route.
        
                    There are many options for setting up and solving the problem (including exhaustive search, greedy algorithm 
                    (nearest neighbor method), cheapest inclusion method, etc.).

                    For this project, I chose the greedy algorithm (but also tested several Python libraries with other solution options).
        
                    On this page you can find my approach to solving VRP       
        """)
    
    
elif selection == "Settings":
    st.header("Input data for calculation")
    st.markdown("""
        Upload a file with the customer address database and enter the data necessary for the calculation.
        Below, you can find a template for the database and a list of necessary fields and data types for each. 
    """)

    
    dict_tamplate_df = {
            "index" : [1, "int", "Necessary"],
            "CustomerCountry" : ["DE", "STRING", "NOT Necessary"],
            "CustomerCity" : ["Berlin", "STRING", "Necessary"],
            "CustomerStreet" : ["Ostallee",  "STRING", "Necessary"],
            "CustomerNumer" : ["12g", "STRING", "Necessary"],
            "CustomerLon" : [0.0, "float", "NOT Necessary"],
            "CustomerLat" : [50.1612172, "float", "NOT Necessary"],
            "Group" : [0, "float", "NOT Necessary"]
            }
        
    @st.cache_data
    def get_data():
        df = pd.DataFrame(dict_tamplate_df)
        return df

    @st.cache_data
    def convert_for_download(df):
        return df.to_csv().encode("utf-8")

    df = get_data()
    
    csv = convert_for_download(df)

    st.download_button(
        label="Download template CSV",
        data=csv,
        file_name="data.csv",
        mime="text/csv",
        icon=":material/download:",
    )
    
    col1, col2, col3 = st.columns(spec=3, gap="medium",  vertical_alignment="top", border=False, width="stretch")

    with col1:
        st.subheader("Customer DataBase")
        uploaded_file_customer_base = st.file_uploader("Upload Customer Base File (.csv)", type="csv")

        if uploaded_file_customer_base:
            customer_base = pd.read_csv(uploaded_file_customer_base)
            st.success("Successfully Uploaded!")
        else:
            st.info("Please Upload the Customer Base file")

    with col2:
        st.subheader("Other Parameters")
        
        selected_routes = st.number_input(label="Number of vehicles", min_value=1, step=1, format="%d")
        selected_routes = int(selected_routes)
        
        selected_days = st.number_input(label="Number of working days", min_value=1, step=1, format="%d")
        selected_days = int(selected_days)
    
    with col3:
        st.subheader("Geo coordinates")
        selected_geo_lat = st.number_input(label="Latitude", format="%0.6f", value=0.0)
        selected_geo_lon = st.number_input(label="Longtitude", format="%0.6f", value=0.0)
        
    start_button=st.button(label="Calculate", type="primary")

    if start_button:
        
        with st.spinner('Calculation started, wait for the result'):
            
            final_routes_df, points_df, fa_balanced, df_DBSCAN, df_SPCL, df_HDBSCAN = routing_workflow(customer_base, 
                    API_GEO_KEY, selected_routes, selected_geo_lon, 
                    selected_geo_lat, selected_days, ORS_API_KEY,columns_data_type, 
                    isna_indexes_list, check_zero_geo, get_geo_data, 
                    distance_duration_inventor, get_geometry, 
                    drawing_route, final_table_constructor)
            
            st.subheader("✅ Have Done")
            st.session_state.final_routes_ = final_routes_df
            st.session_state.geo_points_df_ = points_df
            st.session_state.BALANCED = fa_balanced
            st.session_state.DBSCAN = df_DBSCAN  
            st.session_state.SPCL = df_SPCL  
            st.session_state.HDBSCAN = df_HDBSCAN
            st.dataframe(final_routes_df)

    else:
        st.info("Please load file and input necessary information")

elif selection == "Tables":
    st.subheader("Here you will find Tables")

    if st.session_state.final_routes_ is None:
        st.warning("First things first, we should calculate all routes! So go back " \
        "to 'Settings' page and all the necessary information for calculations.")
    else:
        final_routes_df = st.session_state.final_routes_.copy()
        final_routes_df['Visit_Order'] = final_routes_df.groupby(['Route', 'Day']).cumcount() + 1

        st.subheader("Choose necessary parameters:")
        col_r, col_d = st.columns(2)

        with col_r:
            available_routes = sorted(final_routes_df["Route"].unique())
            display_routes = [r + 1 for r in available_routes]
            selected_route = st.selectbox("Choose the route, please:",
                options=display_routes)
            filter_route = selected_route-1

    
        with col_d:
            available_day = sorted(final_routes_df["Day"].unique())
            display_day =  [r + 1 for r in available_day]
            selected_day = st.selectbox(
                "Choose the day, please:",
                options=display_day
            )
            filter_day = selected_day-1
        
        day_route_table_df = final_routes_df[
            (final_routes_df["Route"] == filter_route) &
            (final_routes_df["Day"] == filter_day)
        ]

        try:
            display_cols = ["Visit_Order", "index", "distance", "duration", 
                            "CustomerFullAdd", "CustomerLat", "CustomerLon"]

            st.info(f"The Route for vehicle {filter_route} day {filter_day}")
            st.dataframe(
                day_route_table_df.loc[:, display_cols].rename(columns={
                    "Visit_Order":"#",
                    "index": "Next point of visit (ID)",
                    "CustomerFullAdd": "Customer Address",
                    "distance": "Distance (m)",
                    "duration": "Duration (sec)",
                    "CustomerLat": "Latitude",
                    "CustomerLon": "Longitude"
                }), 
                use_container_width=True, 
                hide_index=True
            )

            csv = day_route_table_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Route (.csv)",
                data=csv,
                file_name=f'route_{filter_route}_day_{filter_day}_table.csv',
                mime='text/csv',
            )
        except KeyError as error:
            st.error(f"Did not find something, can you ask me later?")

    
elif selection == "Routes Maps":
    if st.session_state.final_routes_ is None:
        st.warning("First things first, we should calculate all routes! So go back to 'Settings' page and all the necessary information for calculations.")
    else:
        st.subheader("Here you will find Routes Maps")
        geometry_df = st.session_state.geo_points_df_
        final_routes_df = st.session_state.final_routes_.copy()

        st.subheader("Choose necessary parameters:")
        col_r, col_d, col_all = st.columns(3)

        with col_r:
            available_routes = sorted(geometry_df["Route"].unique())
            display_routes = [r + 1 for r in available_routes]
            selected_route = st.selectbox("Choose the route, please:",
                options=display_routes)
            filter_route = selected_route-1


        with col_d:
            available_day = sorted(geometry_df["Day"].unique())
            display_day =  [r + 1 for r in available_day]
            selected_day = st.selectbox(
                "Choose the day, please:",
                options=display_day
            )
            filter_day = selected_day-1

        with col_all:
            all_points = st.checkbox("Show me everything!")
            if all_points:
                st.write("That's right, Sir! I'm drawing...")

        
        current_map_for = geometry_df[
                (geometry_df["Route"] == filter_route) &
                (geometry_df["Day"] == filter_day)
            ]

        if current_map_for.empty:
            st.error("Geometry for this route not found. Ask me later!")


        all_geometry_coords = current_map_for['points'].iloc[0]
        all_locations_list = current_map_for['locations'].iloc[0]
        
        if all_points:
            all_points_map = drawing_points_map(final_routes_df)
            
            st_folium(all_points_map,
                #   width=1600,
                use_container_width=True,
                height=600,
                key="route_map")
        else:
            route_map = drawing_route(all_locations_list, all_geometry_coords, filter_route, filter_day)
            st_folium(route_map,
                    #   width=1600,
                    use_container_width=True,
                    height=600,
                key="route_map")


elif selection == "Statistic":
    if st.session_state.final_routes_ is None:
        st.warning("First things first, we should calculate all routes! So go back to 'Settings' page and all the necessary information for calculations.")
    else:
        st.subheader("Here you will find statistics on calculated routes.")
        final_routes_df = st.session_state.final_routes_.copy()
        tab1, tab2 = st.tabs(["General overview", "KPI"])

        with tab1:
            st.header("General overview")
            general_overview_df = general_overview(final_routes_df) 
            
            st.dataframe(
                    general_overview_df, 
                    use_container_width=True, 
                    hide_index=True
                )

        with tab2:
            st.header("KPI")
            st.subheader("Setting the Service Time Duration")
            kpi_col1, kpi_col2 = st.columns(2)
            
            with kpi_col1:
                service_time_min = st.number_input(
                    "Service duration per stop (min)",
                    value=5,
                    step=5
                )
            with kpi_col2:
                available_routes = sorted(final_routes_df["Route"].unique())
                display_routes = [r + 1 for r in available_routes]
                selected_route = st.selectbox("Choose the route, please:",
                    options=display_routes)
                filter_route = selected_route-1    

            st.divider()

            route_kpi_df = final_routes_df.groupby(["Route", "Day"]).agg(
                Total_Distance_m = ("distance", "sum"),
                Total_Travel_Duration_sec = ("duration", "sum"),
                Total_Customers_Num = ("index", lambda x:(x != -1).sum())
            ).reset_index()

            total_stops = route_kpi_df["Total_Customers_Num"].sum()
            service_time_sec = service_time_min*60

            route_kpi_df["Total_Service_Duration_sec"] = route_kpi_df["Total_Customers_Num"]*service_time_sec
            route_kpi_df["Total_Route_Duration_sec"] = route_kpi_df["Total_Service_Duration_sec"]  + route_kpi_df["Total_Travel_Duration_sec"]

            route_kpi_df["Total_Route_Duration"] = route_kpi_df["Total_Route_Duration_sec"].apply(convert_sec)
            
            display_route_kpi = route_kpi_df.copy()
            display_route_kpi["Total Distance (km)"] = round(route_kpi_df["Total_Distance_m"]/1000,2)
            display_route_kpi["Total Travel Duration"] = route_kpi_df["Total_Travel_Duration_sec"].apply(convert_sec)
            display_route_kpi["Total Service Duration"] = route_kpi_df["Total_Route_Duration_sec"].apply(convert_sec)
            display_route_kpi["Total Duration"] =(display_route_kpi["Total_Travel_Duration_sec"] +  display_route_kpi["Total_Route_Duration_sec"]).apply(convert_sec)
            
            st.subheader("KPI Detailing by Route")

            display_route_kpi = display_route_kpi[(route_kpi_df["Route"] == filter_route)]

            try:
                display_cols = ["Day", "Total_Customers_Num", "Total Distance (km)", "Total Travel Duration", "Total Service Duration","Total Duration"]

                st.info(f"The Route for vehicle {filter_route}")
                st.dataframe(
                    display_route_kpi.loc[:, display_cols], 
                    use_container_width=True, 
                    hide_index=True
                )

            except KeyError as error:
                st.error(f"Did not find something, can you ask me later?")
elif selection =="Other UML and models":
    
    if st.session_state.BALANCED is None or st.session_state.DBSCAN is None or st.session_state.SPCL is None or st.session_state.HDBSCAN is None:
        st.warning("First things first, we should calculate all routes! So go back to 'Settings' page and all the necessary information for calculations.")
    else:
        MODELS = [
            "DBSCAN",
            "SpectralClustering",
            "HDBSCAN",
            # "KMeans with PuLP"
        ]
        st.divider()
        selection = st.sidebar.radio("Other Maps:", MODELS)

        
        if selection == "DBSCAN":
            df_DBSCAN = st.session_state.DBSCAN
            all_points_map = drawing_points_map(df_DBSCAN)
            st_folium(all_points_map,
                #   width=1600,
                use_container_width=True,
                height=600,
                key="route_map")
        elif selection == "SpectralClustering":
            df_SPCL = st.session_state.SPCL
            all_points_map = drawing_points_map(df_SPCL)
            st_folium(all_points_map,
                #   width=1600,
                use_container_width=True,
                height=600,
                key="route_map")
        elif selection == "HDBSCAN":
            df_HDBSCAN = st.session_state.HDBSCAN
            all_points_map = drawing_points_map(df_HDBSCAN)
            st_folium(all_points_map,
                #   width=1600,
                use_container_width=True,
                height=600,
                key="route_map")
        # elif selection == "KMeans with PuLP":
        #     df_balanced = st.session_state.BALANCED
        #     print(df_balanced)
        #     all_points_map = drawing_points_map(df_balanced)
            
        #     st_folium(all_points_map,
        #         #   width=1600,
        #         use_container_width=True,
        #         height=600,
        #         key="route_map")

elif selection == "About":
    PARTS = [
        "About Project",
        "Workflow"
    ]
    st.divider()
    selection = st.sidebar.radio("Additional information:", PARTS)
    if selection == "About Project":
        project_markdown = """
            # Project Summary: Vehicle Routing Problem (VRP)

            ## Project Summary and Goal

            
            **Credentials Used:** Openrouteservice (based on OpenStreetMap data: © OpenStreetMap contributors) and geocode.maps.co

            This project was developed as part of the **WBS Web Coding School** training program.


            **Project Goal:** To solve the **Traveling Salesman Problem (TSP)** and the **Vehicle Routing Problem (VRP)** using a combination of clustering and a greedy algorithm (Nearest Neighbor search). Additionally, the goal was to create a user interface for data upload, retrieval, and visualization.

            ---

            ## Project Workflow

            * **Receive Data:** Obtain data and instructions from the user (Web interface).

            * **Data Prep:** Data Cleaning (Pandas) and Data Verification (Pandas).

            * **Geolocation:** If data is incomplete, retrieve necessary data (WEB API).

            * **Clustering:** Data Clustering using Clustering Algorithms (K-Means, K-Means constrained, K-Means with PuLP, DBSCAN, HDBSCAN, Spectral Clustering).

            * **Route Calculation:** Obtain distance data between points (WEB API).

            * **Optimization:** Route generation (Greedy Algorithm, PyVRP).

            * **Output:** Formatting the resulting information, preparation of visualizations, and analytical data for the user (Pandas, Folium).

            * **Comparison:** Visualization of results from other algorithms for comparison.

            ---

            ## Conclusions

            Clustering Algorithms can be effectively utilized to solve the Traveling Salesman Problem, but with certain limitations:

            1. **Closely Located Points (VRP):** For building multiple routes with a large number of closely located points, **K-Means, K-Means constrained, and K-Means with PuLP** are recommended.

            2. **Distant Clusters:** For building multiple routes where points are grouped into distant clusters, **DBSCAN, HDBSCAN, and Spectral Clustering** can be used.

            **Constraint:** Clustering (excluding the K-Means constrained algorithm) demonstrates a significant **disproportion** in cluster sizes.

            ---

            ## Notes on API Service Limitations

            ### Openrouteservice Server Limitations

            * Maximum route distance (**100 km**).

            * Stop radius near a point (this parameter can be changed).

            * *Note:* If these limits are violated, the route will not be displayed on the map.

            ### geocode.maps.co API Service Limitations

            * **Rate limit:** No more than **1 request per second**.

            * *Note:* If the limits are violated, the service will block the user. For significant volumes of undefined geospatial coordinates, the retrieval process will take: **`(number of undefined coordinates) * 1 second`**.
            """

        
        text, logo, buttons = st.columns([12, 1, 2])
        with text:
            st.markdown(project_markdown, unsafe_allow_html=True)
        with logo:
            st.image("icons\WBSCS.png", width=60)
            st.image("icons\li.png", width=60)    
            st.image("icons\github.png", width=60)
        with buttons:
            st.link_button(label="WBS Coding School", url="https://www.wbscodingschool.com/", type= "primary")
            st.link_button(label="LinkedIn profile", url="https://www.linkedin.com/in/andriy-mekhanich/", type= "primary")
            st.link_button(label="GitHub profile", url="https://github.com/MekhAnd/Practice-DADS", type= "primary")
        
        
    elif selection == "Workflow":
        st.subheader("Visualizing the Data Flow")
        st.image("icons\workflow_.drawio.png", 
                 caption="Workflow", width="content")
