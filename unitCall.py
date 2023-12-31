from policebot import handle_event
import requests

itemIDArray = [
    "0x9b41736110b21b836786a287b3ae7ccaedbcdda92cca59af2e7d3a5cbef487ad"
]


def returnFirstResult(itemID):
    # Define the GraphQL endpoint and the query
    endpoint = "https://api.thegraph.com/subgraphs/name/kleros/legacy-curate-xdai"  # Replace with your subgraph endpoint
    query = """
        query GetItem($itemID: ID!) {
            litems(where:{itemID:$itemID}){
                itemID  
                data
                registryAddress
                key0
                latestRequestSubmissionTime
            }
        }
    """

    # Set up the headers and variables for the request
    headers = {"Content-Type": "application/json"}
    variables = {"itemID": itemID}

    # Send the request and retrieve the response
    response = requests.post(
        endpoint, json={"query": query, "variables": variables}, headers=headers
    )

    # Check for a valid response
    if response.ok:
        # Parse and return the JSON response
        item_data = response.json()
        return item_data["data"]["litems"][0]
    else:
        print(f"Failed to retrieve data: {response.text}")
        return None


# Looping through everything that needs commenting by the goddesses
for itemID in itemIDArray:
    bytes_object = bytes.fromhex(itemID[2:])
    itemData = returnFirstResult(itemID)
    print(itemData)
    try:
        if itemData["registryAddress"] == "0xee1502e29795ef6c2d60f8d7120596abe3bad990":
            registryName = "Tokens"
        elif (
            itemData["registryAddress"] == "0x66260c69d03837016d88c9877e61e08ef74c59f2"
        ):
            registryName = "Tags"
        elif (
            itemData["registryAddress"] == "0x957a53a994860be4750810131d9c876b2f52d6e1"
        ):
            registryName = "CDN"
        else:
            raise Exception("Unknown registry: " + itemData["registryAddress"])
        response=handle_event(bytes_object, itemData["data"], registryName,itemData["latestRequestSubmissionTime"],'noONCHAIN')
        print (response)
    except Exception as e:
        print("Error reading registry name: " + str(e))
