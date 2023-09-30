import json
import requests

# Define your Python object
your_object = {
    "title": "3",
    "description": "1",
    "type": "image/png",
}

# Convert the Python object to a JSON string
json_string = json.dumps(your_object)

# Convert the JSON string to bytes
json_bytes = json_string.encode("utf-8")

# Create the 'buffer' field by converting each byte to its integer value
buffer_data = [int(byte) for byte in json_bytes]

# Create the final dictionary
final_dict = {
    "fileName": "evidence.json",
    "buffer": {"type": "Buffer", "data": buffer_data},
}

# Define the URL for the endpoint you want to post to
url = "https://ipfs.kleros.io/add"

# Make the POST request with 'application/json' content type
response = requests.post(
    url, json=final_dict, headers={"Content-Type": "application/json"}
)

response.content
# Check if the request was successful
if response.status_code == 201:
    # Parse the JSON response
    response_json = response.json()
    print("Success:", response_json)
else:
    print("Failed:", response.status_code, response.text)
