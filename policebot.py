from web3 import Web3
import requests
import pdfplumber
import json
from io import BytesIO
import os
import openai
from perplexity import Perplexity
import random
from PIL import Image


openai.api_key = os.environ.get("OpenAI_API_Key", "default_value")


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


def retrieveLogo(ipfs_url):
    response = requests.get(f"https://ipfs.kleros.io{ipfs_url}")

    return response


def createTagsPrompt(_itemID, data):
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
        perplexity = Perplexity()
        response = perplexity.search_sync(  # search_sync returns the final dict while search returns a generator that streams in results
            "Do a thorough search online and tell me what the contract at this address is for?"
            + curatedObject["values"]["Contract Address"].split(":")[-1].strip()
        )
        perplexity_text_results = response["answer"]  # 'response'

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
            + "Taking into account both the acceptance policy and the information found online (only mention this if actually available above), do you think the entry should be accepted into the registry?  Make sure that the information submitted makes sense intrinsically ending and is not nonsense. End off your response using ACCEPT, REJECT or INCONCLUSIVE."
        )
        print(OpenAI_prompt)
    except Exception as e:
        print(f"Error creating OpenAI query: {e}")

    return OpenAI_prompt


def createTokensPrompt(_itemID, data):
    try:
        # Fetch JSON from IPFS
        policyText = extractPDF("/ipfs/Qmak6tHNB4q1Y2ihYde9bZqKaB2wy8mRZ53ChnpCSRfiXR")
    except Exception as e:
        print(f"Error fetching policy from IPFS: {e}")
    # fetch itemID's data object
    try:
        curatedObject = fetch_json("https://ipfs.kleros.io" + data)
    except Exception as e:
        print(f"Error fetching curated IPFS object: {e}")

    try:  # Fetch Logo from IPFS
        logoFile = retrieveLogo(curatedObject["values"]["Logo"])
        image = Image.open(BytesIO(logoFile.content))
        logo_width, logo_height = image.size
        logo_format = image.format.lower()

    except Exception as e:
        logo_width = "unknown"
        logo_height = "unknown"
        logo_format = "unknown"

        print(f"Error fetching policy from IPFS: {e}")

    # Analyze with Perplexity.AI
    try:
        perplexity = Perplexity()
        response = perplexity.search_sync(  # search_sync returns the final dict while search returns a generator that streams in results
            "Do a thorough search online and tell me what the contract at this address is for?"
            + curatedObject["values"]["Address"].split(":")[-1].strip()
        )  # using Address instead of 'Contract Address' due to different field name
        perplexity_text_results = response["answer"]  # 'response'

        perplexity.close()
    except Exception as e:
        print(f"Error searching in perplexity: {e}")
    # do some parsing with this response

    try:
        OpenAI_prompt = (
            "This is the acceptance policy for this registry: \n```"
            + policyText
            + "```\n"
            + "Here is the information submitted about this supposed token contract: \n```"
            + object_to_text_lines(curatedObject["values"])
            + "```\n"
            + "The information found independently from the internet about this supposed token contract: \n```"
            + perplexity_text_results
            + "```\n"
            + "The format of the token's logo is "
            + str(logo_width)
            + " x "
            + str(logo_height)
            + " and the format is ."
            + str(logo_format)
            + "\n"
            + "Taking into account both the acceptance policy, the image dimensions, and the information found online (only mention this if actually available above), do you think the entry should be accepted into the registry?  Make sure that the information submitted makes sense intrinsically ending and is not nonsense. End off your response using ACCEPT, REJECT or INCONCLUSIVE."
        )
        print(OpenAI_prompt)
    except Exception as e:
        print(f"Error creating OpenAI query: {e}")

    return OpenAI_prompt


# Function to handle new item events
def handle_event(_itemID, data, registryType):
    try:
        # data = event["args"]["_data"]
        print("itemID: " + str(_itemID))
        print("data: " + data)
    except Exception as e:
        print(f"Error in parsing event data: {e}")
    if registryType == "Tags":
        OpenAI_prompt = createTagsPrompt(_itemID, data)
    elif registryType == "Tokens":
        OpenAI_prompt = createTokensPrompt(_itemID, data)
    else:
        return

    # Analyze with OpenAI
    OpenAI_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a lawyer in the Kleros ecosystem, who only confirms and convicts when you are absolutely certain. You are clear and concise in your communication and likes to invite others to comment on your words.",
            },
            {"role": "user", "content": OpenAI_prompt},
        ],
    )

    print(OpenAI_response["choices"][0]["message"]["content"])

    # Saving the evidence to Kleros's IPFS node
    deityName = random.choice(
        [
            "Eunomia, AI goddess of good order",
            "Dikē, AI goddess of fair judgements",
            "Eirene, AI goddess of peace",
        ]
    )
    expression = f"Opinion by {deityName}"
    evidence_object = {
        "title": expression,
        "description": OpenAI_response["choices"][0]["message"]["content"],
    }
    evidenceIpfsUri = postJSONtoKlerosIPFS(evidence_object)
    print(evidenceIpfsUri)

    # Submit evidence to the contract

    # Get the transaction data
    transaction_data = contract.functions.submitEvidence(
        _itemID, evidenceIpfsUri
    ).build_transaction(
        {
            "gas": 2000000,
            "nonce": w3.eth.get_transaction_count(w3.eth.defaultAccount),
        }
    )
    # Sign the transaction
    signed_txn = w3.eth.account.sign_transaction(
        transaction_data, os.environ.get("ETH_bot_private_key", "default_value")
    )

    try:
        # Send transaction
        txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for transaction to be mined
        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
        print("Evidence submitted successfully! ")
        print(txn_receipt)
    except Exception as e:
        print("Error submitting transaction: " + e)
