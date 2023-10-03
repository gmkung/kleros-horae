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
tags_contract_address = "0x66260C69d03837016d88c9877e61e08Ef74C59F2"
tokens_contract_address = "0xeE1502e29795Ef6C2D60F8D7120596abE3baD990"

# loading ABI
with open("./ABI/lcurate_abi.json", "r") as f:
    contract_abi = json.load(f)

tags_contract = w3.eth.contract(address=tags_contract_address, abi=contract_abi)
tokens_contract = w3.eth.contract(address=tokens_contract_address, abi=contract_abi)

# Create a new event filter for tags
try:
    tags_new_item_filter = tags_contract.events.NewItem.create_filter(
        fromBlock="latest"
    )
except Exception as e:
    print(f"Error creating filter: {e}")

# Create a new event filter for tokens
try:
    tokens_new_item_filter = tokens_contract.events.NewItem.create_filter(
        fromBlock="latest"
    )
except Exception as e:
    print(f"Error creating filter: {e}")

# Main loop to listen for events
while True:
    try:
        print("Looping Tags police patrol")
        new_tags_entries = tags_new_item_filter.get_new_entries()

        for event in new_tags_entries:
            print(f"Handling event: {event}")
            handle_event(event["args"]["_itemID"], event["args"]["_data"], "Tags")
        time.sleep(5)

    except Exception as e:
        print(f"Error in loop: {e}")

    try:
        print("Looping Tokens police patrol")
        new_token_entries = tokens_new_item_filter.get_new_entries()

        for event in new_token_entries:
            print(f"Handling event: {event}")
            handle_event(event["args"]["_itemID"], event["args"]["_data"], "Tokens")
        time.sleep(5)

    except Exception as e:
        print(f"Error in loop: {e}")
