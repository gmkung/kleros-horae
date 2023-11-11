from policebot import handle_event
import requests

# Modified GraphQL function to retrieve all items
def returnAllResults():
    endpoint = "https://api.thegraph.com/subgraphs/name/kleros/legacy-curate-xdai"
    query = """
        query {
            litems(where:{ registryAddress_in: ["0xee1502e29795ef6c2d60f8d7120596abe3bad990", "0x66260c69d03837016d88c9877e61e08ef74c59f2"] }){
                itemID  
                data
                registryAddress
                key0
                latestRequestSubmissionTime
                status
            }
        }
    """

    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, json={"query": query}, headers=headers)

    if response.ok:
        item_data = response.json()
        return item_data["data"]["litems"]
    else:
        print(f"Failed to retrieve data: {response.text}")
        return []

# Modified loop to process all items
import csv

def write_to_csv(row_data, file_name='output.csv'):
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row_data)

# Define headers for the CSV file
headers = ["registryName", "registryAddress", "itemID", "status", "key0", "key1", "key2", "key3", "key4", "openai_commentary", "verdict"]

# Write the header row to the CSV file
write_to_csv(headers)

for itemData in returnAllResults():
    itemID = itemData["itemID"]
    bytes_object = bytes.fromhex(itemID[2:])
    print(itemData)

    try:
        if itemData["registryAddress"].lower() == "0xee1502e29795ef6c2d60f8d7120596abe3bad990":
            registryName = "Tokens"
        elif itemData["registryAddress"].lower() == "0x66260c69d03837016d88c9877e61e08ef74c59f2":
            registryName = "Tags"
        elif itemData["registryAddress"].lower() == "0x957a53a994860be4750810131d9c876b2f52d6e1":
            registryName = "CDN"
        else:
            raise Exception("Unknown registry: " + itemData["registryAddress"])

        response = handle_event(bytes_object, itemData["data"], registryName, itemData["latestRequestSubmissionTime"],'Silent')
        print(response)

        # Extract data for CSV
        csv_row = [
            registryName,
            itemData.get("registryAddress", ""),
            itemData.get("itemID", ""),
            itemData.get("status", ""),
            itemData.get("key0", ""),
            itemData.get("key1", ""),
            itemData.get("key2", ""),
            itemData.get("key3", ""),
            itemData.get("key4", ""),
            response.get("openai_commentary", ""),
            response.get("verdict", "")
        ]

        # Write the row to CSV
        write_to_csv(csv_row)

    except Exception as e:
        print("Error processing item: " + str(e))
        # Write error information to CSV (optional)
        error_row = [registryName, itemData.get("registryAddress", ""), itemID] + ['Error: ' + str(e)] + [''] * 7
        write_to_csv(error_row)
