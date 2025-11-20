## About:
This project is closely related to a problem that humanity has been trying to solve for about 200 years, and almost every year brings us new solutions. More precisely, it is not a problem— it is a question that sounds something like this: What is the optimal route for delivering goods to a specific group of customers?

__Why is this so important for me?__
I have built routes for my sales teams dozens of times, and each time this procedure has been a huge headache for me and my colleagues. Here, I have tried to solve this problem with Python and Unsupervised Machine Learning algorithms. And the second important task for try to solve these questions with a minimum budget or even without any payment.

So my recipe below:


## Instalation:
__Phase 1: Running your own openrouteservice instance or use API enpoint__
Your first task will be to create a local instace of openrouteservice. Here you can find an exceptional instructions:

How to build [local inctace](https://giscience.github.io/openrouteservice/run-instance/).

Otherwise, create an account and take your API Key [here:](https://giscience.github.io/openrouteservice/run-instance/).

__!!!__ 
If you would like to use the API endpoint:
__Comment lines 176, 192, 232, 241__  and
__Uncomment lines 177, 188, 193, 233, 237, 242__
in routing_utils.py,  __but read API restrictions attentively before__

__Phase 2: Setup your server__
I used *.war solution. After downloading the solution, check [this site](https://download.geofabrik.de/) and download the necessary map for your project. Download the file, save it in your backend folder, then find `ors-config.yml`. In this file, insert the name of the downloaded map, like this:
```
    ors:
    engine:
        profile_default:
        build:
            source_file: YOUR_MAP_FILENAME_WITH.pbf_HERE
        profiles:
        driving-car:
            enabled: true

```

__Phase 3: Geocoding API__
Go [to](https://geocode.maps.co/) and take your API Key. This key will be necessary if your customer base does not have Geo Position coordinates. 

API restrictions - __not more than 1 request per 1 second__, considered in the code only for your attantion

__Phase 4: Create your env__

Crate and activate your environment:

`python3 -m venv venv`

Mac/Linux: `source venv/bin/activate`

Windows: `.\venv\Scripts\activate`

And install all dependencies:

`pip install -r requirements.txt`

__To start project__
python routing.py

__Note!__

Put into the root folder file "customer_base.csv". Necessary fields:
* "index" : "int"
* "CustomerCountry" : Srting
* "CustomerCity" : Srting
* "CustomerStreet" : Srting
* "CustomerNumer" : Srting
* "CustomerLon" : "float"
* "CustomerLat" : "float"
* "Group": not necessary


## How it should work

__After launch:__
1. Go to the "Settings" page
2. Download the template CSV and organise your dataset in the same way (Column names matter)
3. Upload your dataset file.
4. Add the number of Routes that you would like to split and the number of working days in "Other Parameters" 
5. Add your warehouse or office coordinates in "Geo Coordinates"
6. Push the Calculate button

__Behind the scenes script:__
1. Check column data types and convert them (if necessary).
2. Check missing addresses (if will find - drop these rows), coordinates, if will find - create a list with missing rows.
3. Look for these missing coordinates and update missing positions or return a message: 
"Errors in positioning index 'Customer_index'".
4. Based on the number of Routes and on the Customer geo coordinates, split the dataframe into clusters.
4. Based on the number of Days in each Route and on the Customer's geo coordinates, split the Route into Day clusters.
5. Based on the created clusters, construct a distance matrix for each Day, with each point in the cluster.
6. Through the "greedy algorithm", looking for nearest neighbours.
7. Based on the calculation, collect all daily routes.
8. Format all received routes to return 

__FYA__

For the local server instance, calculating the distance matrices for 500 customers took around 70-80 minutes


1. __All Routes__
After the calculation you can find:
 * A table with all routes and all points on these routes in all_routes.csv.
 * A table with all routes, all days and all points on these routes in all_routes_days.csv.
 * A table with all the routes` sequences in routes_sequences.csv.
 * Tables with short statistily information - general_ovwROUTE_NUMBER.csv

2. __Maps__
__FYA__
Your route won`t be drawn on the map if:

_Even for the local server_, openroutesservice has restriction for the length of the route (not more than 100 km) and for the stop point at the point on the route (line 225 in routing_utils.py contains 50 meters - if you would like, you can change it there).

In any case, in folder "Maps", you can find a visual representation of your routes. 
* all_points.html - All points that were in the  customer base will be pinned here
* all_points_routes.html - All points split by routes will be pinned here
* route_0_0.html - Daily route - "route_ROUTE_DAY.html"

Each pin - your customer, and each pin has a pop-up with the number of visits.

## Scenarios

A small number of examples
1. __Courier service:__ Number of couriers = number of routes, Working days = 1
2. __Repair service:__ Number of employees (masters) = number of routes, Working days = based on Service duration - you can play with theses parametres on Statistics page
3. __Salesman routes:__ Number of salesman = number of routes, Working days = ***


## Next Steps

Add:
- additional API points for determining geospatial coordinates
- the ability to use other routing algorithms (Google, PyVRP)
- the ability to calculate fuel consumption for each route (based on entered indicators or on information about the car)


## List of Tools and Technologies
Python, Pandas, API, Scikit-learn (K-Means constrained), Folium
