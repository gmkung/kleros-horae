from web3 import Web3
import json
import time
from policebot import handle_event

# Initialize Web3
w3 = Web3(
    Web3.HTTPProvider(
        "https://nd-500-249-268.p2pify.com/512e720763b369ed620657f84d38d2af"
    )
)
w3.eth.defaultAccount = "0x814D43C478EEE41884279afde0836D957fe63254"

# Initialize contract
contract_address = "0x66260C69d03837016d88c9877e61e08Ef74C59F2"  # 0xa64E8949Ad24259526a32d4BfD53A9f2154ae6bB is the test registry # real: 0x66260C69d03837016d88c9877e61e08Ef74C59F2

# loading ABI
with open("./ABI/lcurate_abi.json", "r") as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Create a new event filter
try:
    new_item_filter = contract.events.NewItem.create_filter(fromBlock="latest")
except Exception as e:
    print(f"Error creating filter: {e}")
    new_item_filter = contract.events.NewItem.create_filter(fromBlock="latest")

# Main loop to listen for events
while True:
    try:
        print("Looping")
        new_entries = new_item_filter.get_new_entries()

        for event in new_entries:
            print(f"Handling event: {event}")
            handle_event(event["args"]["_itemID"], event["args"]["_data"])
        time.sleep(5)

    except Exception as e:
        print(f"Error in loop: {e}")
