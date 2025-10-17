import requests as r
import getpass
import json
import time
import os

# --- Configuration ---
API_URL = 'https://appeears.earthdatacloud.nasa.gov/api/'
DOWNLOAD_DIR = 'appeears_ndvi_downloads'

# --- 1. Define Coordinates and Request Parameters ---
# MODIS MOD13A3.061 is monthly, 1km NDVI, ideal for time series
PRODUCT = "MOD13A3.061"
LAYERS = [
    {"layer": "NDVI", "product": PRODUCT},
    {"layer": "VI_Quality", "product": PRODUCT} # Essential for filtering bad data
]
TASK_NAME = "NDVI_Peak_Bloom_Analysis"
START_DATE = "01-01-2020"
END_DATE = "12-31-2023"

# Example point data (ID, Lat, Lon)
points_data = [
    {"id": "PeakBloom_Site_1", "lat": 40.7128, "lon": -74.0060}, # Example 1
    {"id": "PeakBloom_Site_2", "lat": 34.0522, "lon": -118.2437} # Example 2
]

# Build the GeoJSON FeatureCollection required by the API
geojson_payload = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
            "properties": {"id": p["id"]}
        } for p in points_data
    ]
}

request_json = {
    "task_type": "point",
    "task_name": "NDVI_Multi_Point_Extract",
    "params": {
        "dates": [
            {
                "startDate": "01-01-2022",
                "endDate": "12-31-2023"
            }
        ],
        "layers": [
            {"layer": "_1_km_monthly_NDVI", "product": "MOD13A3.061"},
        ],
        "output": {
            "format": {"type": "csv"}
        },
        
        "coordinates": [{
        "latitude": "-3.45",
        "longitude": "-60.12"}
        ]
        
    }
}

# --- 2. Login and Get Bearer Token ---
print("--- Logging in to Earthdata ---")
try:
    # Use getpass for secure credential input
    USERNAME = "mateo2910"
    PASSWORD = "JyA.14#1S2$W"

    login_response = r.post(f"{API_URL}login", auth=(USERNAME, PASSWORD)).json()
    TOKEN = login_response.get('token')
    
    if not TOKEN:
        print("Login failed. Check username and password.")
        exit()
        
    HEADERS = {'Authorization': f"Bearer {TOKEN}"}
    del USERNAME, PASSWORD # Clean up
    print("Login successful. Token acquired.")

except Exception as e:
    print(f"An error occurred during login: {e}")
    exit()

# --- 3. Submit the Task ---
print("--- Submitting AppEEARS Request ---")
submit_response_obj = r.post(f"{API_URL}task", headers=HEADERS, json=request_json)
submit_status = submit_response_obj.status_code

submit_response = submit_response_obj.json()
TASK_ID = submit_response.get('task_id')
# if submit_status == 200:
#     print(f"SUCCESS! Task submitted. ID: {TASK_ID}")
# else:
#     print(f"ERROR: API submission failed (Status {submit_status}).")
#     try:
#         error_details = submit_response_obj.json()
#         print(f"Server message: {json.dumps(error_details, indent=4)}")
#     except:
#         print("No JSON error details available.")
#     exit()

# --- 4. Wait for Task Completion (Polling) ---
print("--- Waiting for Task to Process ---")
status = 'pending'
while status not in ['done', 'failed', 'error']:
    time.sleep(5) # Poll every 30 seconds
    
    status_response = r.get(f"{API_URL}status/{TASK_ID}", headers=HEADERS).json()
    status = status_response.get('status', 'unknown')
    progress = status_response.get('progress', 0)
    
    print(f"Current Status: {status} ({progress}%)")

if status != 'done':
    print(f"Task failed or ended with status: {status}. Check AppEEARS site for details.")
    exit()

# --- 5. Download the Output ---
print("--- Task done. Retrieving file manifest ---")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 5a. Get the file manifest
files_response = r.get(f"{API_URL}bundle/{TASK_ID}", headers=HEADERS).json()
file_list = files_response.get('files', [])

# 5b. Find the main ZIP file output
data_file_details = next((f for f in file_list if f.get('file_type') == 'csv'), None)

if data_file_details:
    FILE_ID = data_file_details['file_id']
    FILE_NAME = data_file_details['file_name']
    
    download_path = os.path.join(DOWNLOAD_DIR, FILE_NAME)
    download_url = f"{API_URL}bundle/{TASK_ID}/{FILE_ID}"
    
    print(f"Starting download of {FILE_NAME} to {download_path}")

    # 5c. Stream the file download
    file_response = r.get(download_url, headers=HEADERS, stream=True)
    
    if file_response.status_code == 200:
        with open(download_path, 'wb') as file:
            for chunk in file_response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print("Download complete! Your NDVI data is ready for analysis.")
    else:
        print(f"Download failed. HTTP Status Code: {file_response.status_code}")
else:
    print("Download failed: Could not find the main ZIP output file in the bundle.")