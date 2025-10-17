# Import packages 
import requests as r
import getpass, pprint, time, os, json
import geopandas as gpd

inDir = os.path.dirname(os.path.dirname(os.getcwd()))          # IMPORTANT: Update if this does not reflect the proper directory on your OS
os.chdir(inDir)                                      # Change to working directory
api = 'https://appeears.earthdatacloud.nasa.gov/api/'

user = getpass.getpass(prompt = 'Enter NASA Earthdata Login Username: ')      # Input NASA Earthdata Login Username
password = getpass.getpass(prompt = 'Enter NASA Earthdata Login Password: ')

token_response = r.post('{}login'.format(api), auth=(user, password)).json() # Insert API URL, call login service, provide credentials & return json
del user, password                                                           # Remove user and password information
print(token_response)

product_response = r.get('{}product'.format(api)).json()                         # request all products in the product service
print('AρρEEARS currently supports {} products.'.format(len(product_response)))


API_URL = 'https://appeears.earthdatacloud.nasa.gov/api/'

# 1. Login to get Bearer Token
# NOTE: getpass securely prompts for username and password
USERNAME = "mateo2910"
PASSWORD = "JyA.14#1S2$W"

login_response = r.post(f"{API_URL}login", auth=(USERNAME, PASSWORD)).json()

# Extract the token and set the authorization header
TOKEN = login_response['token']
HEADERS = {'Authorization': f"Bearer {TOKEN}"}

# Clean up credentials
del USERNAME, PASSWORD


# request_json = {
#     "task_type": "point",
#     "task_name": "NDVI_Multi_Point_Extract",
#     "params": {
#         "dates": [
#             {
#                 "startDate": "01-01-2022",
#                 "endDate": "12-31-2023"
#             }
#         ],
#         "layers": [
#             {"layer": "_1_km_monthly_NDVI", "product": "MOD13A3.061"},
#         ],
#         "output": {
#             "format": {"type": "csv"}
#         },
        
#         "coordinates": [{
#         "latitude": "-3.45",
#         "longitude": "-60.12"}
#         ]
        
#     }
# }