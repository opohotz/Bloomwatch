from elasticsearch import Elasticsearch
from pprint import pprint # Used for cleaner printing of JSON responses

# 1. Connect to the local cluster (default port 9200, no auth assumed)

import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ELASTIC_API_KEY")

try:
    client = Elasticsearch(
    "https://my-elasticsearch-project-b1ab41.es.us-central1.gcp.elastic.cloud:443",
    api_key=api_key
    )
    client.info() # Try to get cluster info
    print("✅ Successfully connected to Elasticsearch!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit()

INDEX_NAME = "customer_orders"

# Function to create the index
def create_index():
    # Ignore 400 means if the index already exists, don't throw an error
    client.indices.create(index=INDEX_NAME, ignore=400)
    print(f"\n📦 Index '{INDEX_NAME}' created (or already exists).")

# Function to delete the index (useful for a clean start)
def delete_index():
    # Ignore 404 means if the index doesn't exist, don't throw an error
    client.indices.delete(index=INDEX_NAME, ignore=404)
    print(f"\n🗑️ Index '{INDEX_NAME}' deleted (if it existed).")

# Let's clean up and start fresh
# delete_index()
create_index()  

# A list of JSON documents to index
orders = [
    {
        "order_id": "A1001",
        "customer_name": "Alice Smith",
        "product": "Laptop Stand",
        "price": 45.00,
        "status": "Shipped",
        "timestamp": "2025-05-01T10:00:00Z"
    },
    {
        "order_id": "B2002",
        "customer_name": "Bob Johnson",
        "product": "Mechanical Keyboard",
        "price": 120.00,
        "status": "Processing",
        "timestamp": "2025-05-02T11:30:00Z"
    },
    {
        "order_id": "C3003",
        "customer_name": "Alice Smith",
        "product": "Wireless Mouse",
        "price": 25.00,
        "status": "Shipped",
        "timestamp": "2025-05-03T09:15:00Z"
    }
]

# Index the documents one by one
def index_documents():
    print("\nIndexing documents...")
    for i, order in enumerate(orders):
        # We use a custom ID for easy reference later (optional)
        response = client.index(index=INDEX_NAME, id=i + 1, document=order)
        # print(f"Indexed doc {i+1}: {response['result']}")

index_documents()

def get_document(doc_id):
    print(f"\n🔎 Retrieving Document ID: {doc_id}")
    try:
        response = client.get(index=INDEX_NAME, id=doc_id)
        pprint(response['_source'])
    except Exception:
        print(f"Document ID {doc_id} not found.")

get_document(2)

def update_document(doc_id, new_status):
    print(f"\n🔄 Updating Document ID: {doc_id} status to '{new_status}'")
    
    # The 'doc' parameter specifies only the fields you want to change
    update_body = {
        "doc": {
            "status": new_status,
            "notes": "Updated after quality check"
        }
    }
    client.update(index=INDEX_NAME, id=doc_id, body=update_body)
    get_document(doc_id) # Verify the update

update_document(2, "Delivered")

def delete_document(doc_id):
    print(f"\n🗑️ Deleting Document ID: {doc_id}")
    client.delete(index=INDEX_NAME, id=doc_id)
    get_document(doc_id) # Should show 'not found'

delete_document(3)

def search_product(term):
    print(f"\n🔍 Searching for: '{term}'")
    
    # 1. Define the Query DSL in a Python dictionary
    search_body = {
        "query": {
            "match": {
                "product": term
            }
        },
        # Optional: Limit the fields returned to keep the response clean
        "_source": ["customer_name", "product", "price", "status"] 
    }
    
    # 2. Execute the search
    results = client.search(index=INDEX_NAME, body=search_body)

    # 3. Print the results
    print(f"Total Hits: {results['hits']['total']['value']}")
    for hit in results['hits']['hits']:
        print(f"  Score: {hit['_score']:.2f} | {hit['_source']['customer_name']} bought: {hit['_source']['product']} (Status: {hit['_source']['status']})")

search_product("Keyboard")

def search_with_filter(customer, status):
    print(f"\n🔍 Searching for {status} orders by {customer}")

    search_body = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"customer_name.keyword": customer}}, # Use .keyword for exact matches
                    {"term": {"status.keyword": status}}
                ]
            }
        },
        "_source": ["customer_name", "product", "status"]
    }

    results = client.search(index=INDEX_NAME, body=search_body)
    
    # Print the results
    print(f"Total Hits: {results['hits']['total']['value']}")
    for hit in results['hits']['hits']:
        print(f"  {hit['_source']['customer_name']} bought: {hit['_source']['product']}")

search_with_filter("Alice Smith", "Shipped")