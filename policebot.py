from web3 import Web3
import requests
import pdfplumber
import json
from io import BytesIO
import time
import os
import openai
from perplexity import Perplexity
import random


perplexity = Perplexity()

openai.api_key = os.environ.get("OpenAI_API_Key", "default_value")


# Initialize Web3
w3 = Web3(
    Web3.HTTPProvider(
        "https://nd-500-249-268.p2pify.com/512e720763b369ed620657f84d38d2af"
    )
)
w3.eth.defaultAccount = "0x814D43C478EEE41884279afde0836D957fe63254"

# Initialize contract
contract_address = "0xa64E8949Ad24259526a32d4BfD53A9f2154ae6bB"

# loading ABI
with open("./ABI/lcurate_abi.json", "r") as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)


# Function to cache PDF
def extractPDF(ipfs_url):
    response = requests.get(f"https://ipfs.kleros.io{ipfs_url}")
    fullText = ""

    with pdfplumber.open(BytesIO(response.content)) as pdf:
        for page in pdf.pages:
            fullText += page.extract_text()

    return fullText


def fetch_json(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def object_to_text_lines(obj):
    return "\n".join([f"{key}: {value}" for key, value in obj.items()])


def postJSONtoKlerosIPFS(object):
    # Convert the Python object to a JSON string
    json_string = json.dumps(object)

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

    # Check if the request was successful
    if response.status_code == 201:
        # Parse the JSON response
        response_json = response.json()
        return "/ipfs/" + response_json["data"][0]["hash"]
    else:
        raise Exception(
            f"Failed to upload to IPFS: {response.status_code}, {response.text}"
        )


# Function to handle new item events
def handle_event(event):
    try:
        itemID = event["args"]["_itemID"].hex()
        data = event["args"]["_data"]
        print("itemID: " + itemID)
        print("data: " + data)
    except Exception as e:
        print(f"Error in parsing event data: {e}")
    try:
        # Fetch JSON from IPFS
        policyText = extractPDF("/ipfs/QmSaJWBFGGZ3FussTi6MqfXrMsaE75asumR2LLuAZFcrSf")
    except Exception as e:
        print(f"Error fetching policy from IPFS: {e}")
    # fetch itemID's data object
    try:
        curatedObject = fetch_json("https://ipfs.kleros.io" + data)
    except Exception as e:
        print(f"Error fetching curated IPFS object: {e}")

    # Analyze with Perplexity.AI
    try:
        response = perplexity.search(
            "What is this ethereum address? "
            + curatedObject["values"]["Contract Address"].split(":")[-1].strip()
            + "? Tell us what you can find about the project/team that it's linked to, the usage and function of the contract and the chain that it's on"
        )
        perplexity_text_results = next(response)[
            "answer"
        ]  # 'response' is a python generator, and I'm using next to read the first one.
        print(json.dumps(perplexity_text_results))
        perplexity.close()
    except Exception as e:
        print(f"Error searching in perplexity: {e}")
    # do some parsing with this response

    try:
        OpenAI_prompt = (
            "This is the acceptance policy for this registry: \n```"
            + policyText
            + "```\n"
            + "Here is the information submitted about the contract: \n```"
            + object_to_text_lines(curatedObject["values"])
            + "```\n"
            + "The information found independently from the internet about this contract: \n```"
            + perplexity_text_results
            + "```\n"
            + "Taking both the acceptance policy and the information online into account, is the entry acceptance for the registry? Give your advice sounding like a bureaucratic lawyer, making sure that the information submitted also makes sense intrinsically ending. End off your response using ACCEPT, REJECT or INCONCLUSIVE, and say something spicy at the end to spur participation in the discussion."
        )
        print(OpenAI_prompt)
    except Exception as e:
        print(f"Error creating OpenAI query: {e}")

    # Analyze with OpenAI
    OpenAI_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": OpenAI_prompt}]
    )

    print(OpenAI_response["choices"][0]["message"]["content"])

    # Saving the evidence to Kleros's IPFS node
    deityName = random.choice(["Eunomia", "Dikē", "Eirene"])
    expression = f"Opinion by {deityName}"
    evidence_object = {
        "title": expression,
        "description": OpenAI_response["choices"][0]["message"]["content"],
    }
    evidenceIpfsUri = postJSONtoKlerosIPFS(evidence_object)
    print(evidenceIpfsUri)

    # Submit evidence to the contract

    formatted_itemID = Web3.to_bytes(text=itemID).ljust(32, b"\0")
    print(formatted_itemID)
    transaction = contract.functions.submitEvidence(
        event["args"]["_itemID"], evidenceIpfsUri
    ).transact(
        {
            "chainId": 100,  # Gnosis chain
            "gas": 2000000,
            "gasPrice": int(20 * 1e9),  # to gwei
            "nonce": w3.eth.get_transaction_count(w3.eth.defaultAccount),
        }
    )
    try:
        # Sign the transaction
        signed_txn = w3.eth.account.signTransaction(
            transaction, os.environ.get("ETH_bot_private_key", "default_value")
        )

        # Send the transaction
        transaction_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    except Exception(e):
        print(e)
    print("Evidence submitted!: " + transaction_hash.hex())


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
            handle_event(event)
        time.sleep(5)

    except Exception as e:
        print(f"Error in loop: {e}")
