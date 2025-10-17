# server/app.py
from elastic_transport import ObjectApiResponse
from flask import Flask, request, jsonify, json 
from flask_cors import CORS # Needed for local development

# packages to speak to  AppEEARS
import requests as r # post and get requests to database
import getpass, pprint, time, os, json # parsing JSON
import geopandas as gpd # data manipulation/analysis tool for geospatial 
from shapely.geometry import Point, mapping
import asyncio
from tools import LRUCache, input_parameters
import csv

# packages for elastic
from elasticsearch import Elasticsearch
from pprint import pprint # Used for cleaner printing of JSON responses
from dotenv import load_dotenv

from datetime import datetime
from threading import Thread

app = Flask(__name__)
CORS(app) # Enable CORS for all origins, necessary when Vite runs on a different port

api = 'https://appeears.earthdatacloud.nasa.gov/api/'  # Set the AρρEEARS API to a variable
TOKEN = None
HEADERS = None
TASK_ID = None
DOWNLOAD_DIR = 'cache_downloads'
cache = LRUCache(5)
client = None

def date_to_es_format(date: str) -> str:
    try:
        # Step 1: Parse the existing format
        date_obj = datetime.strptime(date, '%m-%d-%Y')
        # Step 2: Format to the standard Elasticsearch format
        es_date = date_obj.strftime('%Y-%m-%d') 
        return es_date
    except ValueError:
        print(f"Error: Input date '{date}' is not in MM-DD-YYYY format.")
        return None

#connect to elastic
def connect_to_elastic():
    """
    """
    global client
    load_dotenv()
    elastic_key = os.getenv("ELASTIC_API_KEY")
    try:
        client = Elasticsearch(
        "https://my-elasticsearch-project-b1ab41.es.us-central1.gcp.elastic.cloud:443",
        api_key=elastic_key
        )
        client.info() # Try to get cluster info
        print("Successfully connected to Elasticsearch!")
    except Exception as e:
        print(f"Connection failed: {e}")
        exit()
    
    client.options(ignore_status=400).indices.create(index="fire_hazards_data", mappings={
    "properties": {
      "location": {
        "type": "geo_point"
      }
    }
  })
    print(f"\nIndex 'fire_hazards_data' created (or already exists).")

def connect_to_api(username, password):
    global TOKEN, HEADERS
    token_response = r.post('{}login'.format(api), auth=(username, password)).json() # Insert API URL, call login service, provide credentials & return json
    del username, password                                                           # Remove user and password information
    TOKEN = token_response['token']
    HEADERS = {'Authorization': f"Bearer {TOKEN}"}
    # print("token response:\n", token_response)
    # print("----------------------------------------------")    
    # print('{}login'.format(api))

def elastic_insert(data: dict) -> None:
    """
    Purpose:

    Args:

    Returns:
    """
    print("\nIndexing documents...")
    print("DATA", json.dumps(data, indent=2))
    for i, order in enumerate(data):
        # We use a custom IDfor easy reference later (optional)
        order['location'] = {
            "type": "Point",
            "coordinates": [float(order['Latitude']), float(order['Longitude'])]
        } 
        
        #mapping(Point(float(order['Latitude']), float(order['Longitude'])))
        
        response = client.index(index="fire_hazards_data", id=i + 1, document=order)
        print(f"Indexed doc {i+1}: {response['result']}")

import json
from elasticsearch import Elasticsearch # Assuming you imported this previously

import math

def get_bounding_box(latitude: float, longitude: float, half_side_km: float = 0.5):
    """
    Calculates the bounding box coordinates for a square area around a central point.

    Args:
        latitude (float): The latitude of the center point.
        longitude (float): The longitude of the center point.
        half_side_km (float): Half the side length of the square in kilometers.
                              Default is 0.5 for a 1km x 1km box.

    Returns:
        dict: A dictionary containing the top-left and bottom-right coordinates.
    """
    assert half_side_km > 0

    # Angular radius of the Earth in kilometers
    EARTH_RADIUS_KM = 6371.0

    # Convert latitude to radians for trigonometric functions
    lat_rad = math.radians(latitude)

    # Calculate the change in latitude (north-south)
    lat_delta = math.degrees(half_side_km / EARTH_RADIUS_KM)

    # Calculate the change in longitude (east-west), which depends on the latitude
    lon_delta = math.degrees(half_side_km / (EARTH_RADIUS_KM * math.cos(lat_rad)))

    # Calculate the corner points
    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta

    return {
        "top_left": {"lat": min_lat, "lon": max_lon},
        "bottom_right": {"lat": max_lat, "lon": min_lon}
    }


# Assume 'client' is your initialized Elasticsearch connection object
@app.route('/api/elastic_search', methods=['GET'])
def elastic_search(latitude=None, longitude=None, date=None):
    """
    Purpose: 
        Query Elasticsearch to retrieve data by performing an EXACT match 
        on latitude, longitude, and date.

    Args:
        latitude (str): latitude of the desired coordinate
        longitude (str): longitude of the desired coordinate
        date (str): date of the desired data in MM-DD-YYYY format

    Returns:
        results (dict): The highest-scoring document's _source data, or None if not found.
    """

    if not latitude or not longitude or not date:
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        date = request.args.get('date')

    date = date_to_es_format(date)

    print(f"\n🔍 Searching for: 'lat: {str(latitude)}, lon: {str(longitude)}, date: {date}'")

    # 1. Define the Query DSL using 'bool' and 'term' clauses
    # 'term' is for exact matching on non-analyzed fields (like dates and coordinates).
    bounding_box = get_bounding_box(float(latitude), float(longitude), 0.5)
    search_body = {
        "query": {
            "bool": {
                "must": {
                    "match_all": {}
                },
                "filter": {
                    "geo_distance": {
                        "distance": "100km",
                        "location": [float(latitude), float(longitude)]
                    }
                }
            }
        }
    }

    print(json.dumps(search_body, indent=2))

    try:
        # 2. Execute the search (assuming 'client' is globally available or passed in)
        # Using client.search() from the official 'elasticsearch' client
        results = client.search(index="fire_hazards_data", body=search_body)

        # 3. Process the results
        total_hits = results['hits']['total']['value']
        print('results', json.dumps(results.body, indent=2))
        print(f"Total Hits: {total_hits}")

        if total_hits > 0:
            # Return the contents of the highest-scoring document's '_source' field
            return results['hits']['hits'][0]['_source']
        else:
            return None
            
    except Exception as e:
        print(f"Elasticsearch Query Error: {e}")
        return None

def within_cache(task: dict) -> bool:
    """
    Purpose:

    Args:

    Returns:
    """
    key = json.dumps(task)
    if(cache.get(key) == ""):
        return False
    else:
        return True
    
def read_data(filepath: str) -> dict:
    """
    Purpose:

    Args:

    Returns:
    """
    data = []
    try:
        # 'r' mode for reading, 'newline=""' is important for cross-platform compatibility
        with open(filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            # csv.DictReader uses the first row as field names (keys)
            reader = csv.DictReader(csvfile)
            
            # Iterate over each row (which is already a dictionary)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        # logger.error(f"Error: The file '{filepath}' was not found.")
        return None
    
    return data

def cached_task(task: dict) -> dict:
    """
    Purpose: 
        Task was already queried within the last 5 queries. 
        This function reads the local cached data and returns it. 
        Function avoids using the network for highly-request data

    Args:
        task - json query that would've been sent to the databases

    Returns:
        data that was cached from previous search to give to the backend
    """
    
    key = json.dumps(task)

    file_path = cache.get(key)

    data = read_data(file_path)
    return data

def push_to_cache(task: dict, file_path: str) -> None:
    """
    Purpose:
        Function takes in the task as the key and the filepath as the value for the cache.
        This allows us to download the data locally and maintain it.

    Args:
        task - JSON string that has all the parameters user wants.
        file_path - file path of the cached data

    Returns:
        None
    """
    old_file_path = cache.put(json.dumps(task), file_path)
    if(old_file_path == ""):
        return
    else:
        os.remove(old_file_path)

def make_task(input_params: input_parameters) -> dict:
    """
    Purpose:
        Converts input data object from frontend to a JSON string usable to backend framework.
        
    Args:
        input_params - Class with the following variables:
            * latitude   - latitude of the desired coordinate
            * longitude  - longitude of the desired coordinate
            * date_start - Start of the date range for which to extract data: MM-DD-YYYY
            * date_end   - End of the date range for which to extract data: MM-DD-YYYY
            * recurring  - Makes the data ignore one year and return data for a range of years
            * year_range - [-1,-1] if not recurring, [year start, year end] if recurring is true
        
    Returns:
        JSON string with the parameters provided from input_parameters object
    """

    request_json = {
    "task_type": "point",
    "task_name": "NDVI_Multi_Point_Extract",
    "params": {
        "dates": [
            {
                "startDate": input_params.date_start,
                "endDate": input_params.date_end
            }
        ],
        "layers": [
            {"layer": "_1_km_monthly_NDVI", "product": "MOD13A3.061"},
        ],
        "output": {
            "format": {"type": "csv"}
        },
        
        "coordinates": [{
        "latitude": input_params.lat,
        "longitude": input_params.lon}
        ]
        
        }
    }
    return request_json

def enqueue_data(request_json: dict) -> dict:
    """
    Purpose:
        Enqueues the data to the AppEEARS database and returns. 
    
    Args:
        request_json - JSON string that has parameters given from the frontend.

    returns:
        AppEEARS reply after we push to queue our request
    """
    submit_response_obj = r.post(f"{api}task", headers=HEADERS, json=request_json)

    submit_response = submit_response_obj.json()
    return submit_response

def data_ready(id):
    """
    Purpose: 
        Check the status of the task until it is done. 
        Checks status every 5 seconds until the task is complete
        or fails.

    Args:
        None
        
    Returns:
        True if task is done, False if task failed
    """

    print("--- Waiting for Task to Process ---")
    status = 'pending'
    while status not in ['done', 'failed', 'error']:
        time.sleep(5) # Poll every 5 seconds
        
        status_response = r.get(f"{api}status/{id}", headers=HEADERS).json()
        status = status_response.get('status', 'unknown')
        progress = status_response.get('progress', 0)
        print(f"Current Status: {status} ({progress}%)")

    if status != 'done':
        print(f"Task failed or ended with status: {status}. Check AppEEARS site for details.")
        return False
    return True

def fetch_data(id):
    """
    Purpose: 
        Downloads the data from the AppEEARS database once the task is complete. 
        Saves the data to a local directory for later use. It transforms the csv into a
        dict and returns it. None if not found.

    Args:
        None
        
    Returns:
        Python dictionary object that's structured like a JSON string
        
    """

    print("--- Task done. Retrieving file manifest ---")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 5a. Get the file manifest
    files_response = r.get(f"{api}bundle/{id}", headers=HEADERS).json()
    file_list = files_response.get('files', [])

    # 5b. Find the main ZIP file output
    data_file_details = next((f for f in file_list if f.get('file_type') == 'csv'), None)

    if data_file_details:
        FILE_ID = data_file_details['file_id']
        FILE_NAME = FILE_ID+".csv"
        
        download_path = os.path.join(DOWNLOAD_DIR, FILE_NAME)
        download_url = f"{api}bundle/{id}/{FILE_ID}"
        
        print(f"Starting download of {FILE_NAME} to {download_path}")

        # 5c. Stream the file download
        file_response = r.get(download_url, headers=HEADERS, stream=True)
        
        if file_response.status_code == 200:
            with open(download_path, 'wb') as file:
                for chunk in file_response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            print("Download complete! Your NDVI data is ready for analysis.")
            filepath = os.path.join(DOWNLOAD_DIR, FILE_NAME)
            
            return read_data(filepath), download_path
        else:
            print(f"Download failed. HTTP Status Code: {file_response.status_code}")
            return None, None
    else:
        print("Download failed: Could not find the main CSV output file in the bundle.")
        return None, None

def perform_background_uploads(task, file_path, data_for_elastic):
    push_to_cache(task, file_path)
    elastic_insert(data_for_elastic)

@app.route('/api/access_data', methods=['GET'])
def access_data():
    """
    """
    lat = request.args.get('latitude')
    lon = request.args.get('longitude')
    date_s = request.args.get('date_start')
    date_e = request.args.get('date_end')
    input = input_parameters(lat, lon, date_s, date_e)

    task = make_task(input)

    if(within_cache(task)):
        return jsonify(cached_task(task))

    data  = elastic_search(input.lat, input.lon, input.date_start) # only searching start date for now

    if data:
        return jsonify(data)
    reply = enqueue_data(task)
    
    # check reply if its valid ----------------------------------------------
    print(reply)

    if data_ready(reply['task_id']): # wait while data is getting processed 
        data, file_path = fetch_data(reply['task_id'])
        if not data or not file_path:
            print("No data fetched.")
            return jsonify({"message": "No data fetched"})
        if not data:
            print("No data fetched.")
            return jsonify({"message": "No data fetched"})
        perform_background_uploads(task, file_path, data)
        print("DATA:", data)
        return jsonify(data)
    return jsonify({"message": "Task failed or ended with error"})

if __name__ == '__main__':
    # Flask runs on port 5000 by default
    print("running...")
    connect_to_elastic()
    connect_to_api("hassoonu", "FireHazard123!")
    app.run(debug=True)
    # access_data()