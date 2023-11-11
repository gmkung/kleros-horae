#This script runs by default for the past day. Currently configured by a cron job to run at 1 am UTC everyday.
#if reruns for specific days is needed, use: heroku run python your_script.py --date "YYYY-MM-DD"
import argparse
from datetime import datetime, timedelta
import requests
from policebot import handle_event

# Setup argument parser
parser = argparse.ArgumentParser(description="Process events for a specific date.")
parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format to process events for. Defaults to yesterday.')

# Parse arguments
args = parser.parse_args()

# If a date is provided, use that, otherwise default to yesterday's date
process_date = args.date if args.date else (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

# Convert the date into a Unix timestamp range (beginning and end of the day)
start_timestamp = int(datetime.strptime(process_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0).timestamp())
end_timestamp = start_timestamp + 86400  # 86400 seconds in a day

def query_events_by_date(start_timestamp, end_timestamp):
    # Define the GraphQL endpoint and the query
    endpoint = "https://api.thegraph.com/subgraphs/name/kleros/legacy-curate-xdai"
    query = """
        query GetItemsByDate($startTime: Int!, $endTime: Int!) {
            items: litems(where:{
                registryAddress_in:["0x66260c69d03837016d88c9877e61e08ef74c59f2","0xee1502e29795ef6c2d60f8d7120596abe3bad990"],
                latestRequestSubmissionTime_gte: $startTime,
                latestRequestSubmissionTime_lt: $endTime
            }) {
                itemID
                registryAddress
                data
                latestRequestSubmissionTime
            }
        }
    """
    
    # Set up the headers and variables for the request
    headers = {"Content-Type": "application/json"}
    variables = {"startTime": start_timestamp, "endTime": end_timestamp}
    
    # Send the request and retrieve the response
    response = requests.post(
        endpoint, json={"query": query, "variables": variables}, headers=headers
    )
    
    # Check for a valid response
    if response.ok:
        # Parse and return the JSON response
        events_data = response.json()
        return events_data["data"]["items"]
    else:
        print(f"Failed to retrieve data: {response.text}")
        return None

# Main execution
if __name__ == "__main__":
    events = query_events_by_date(start_timestamp, end_timestamp)
    if events:
        for event in events:
            print ("event['itemID'][2:]",event['itemID'][2:])
            print ("event['itemID']",event['itemID'])
            # Assuming event['itemID'] returns a string that needs to be stripped of '0x' and converted to bytes
            bytes_object = bytes.fromhex(event['itemID'][2:])
            
            try:
                if event["registryAddress"] == "0xee1502e29795ef6c2d60f8d7120596abe3bad990":
                    registryName = "Tokens"
                elif event["registryAddress"] == "0x66260c69d03837016d88c9877e61e08ef74c59f2":
                    registryName = "Tags"
                elif event["registryAddress"] == "0x957a53a994860be4750810131d9c876b2f52d6e1":
                    registryName = "CDN"
                else:
                    raise Exception("Unknown registry: " + event["registryAddress"])
                handle_event(bytes_object, event["data"], registryName,event["latestRequestSubmissionTime"],'COMMENT_ONCHAIN')  # Assuming handle_event is defined
            except Exception as e:
                print(f"Error processing itemID {event['itemID']}: {str(e)}")
    else:
        print(f"No events to process for date: {process_date}")
