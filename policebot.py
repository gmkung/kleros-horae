from web3 import Web3
import requests
import pdfplumber
import json
from io import BytesIO
import os
import openai
from perplexity import Perplexity
from PIL import Image
from urllib.parse import urlparse

openai.api_key = os.environ.get("OpenAI_API_Key", "default_value")

# Initialize Web3
w3 = Web3(
    Web3.HTTPProvider(
        "https://nd-500-249-268.p2pify.com/512e720763b369ed620657f84d38d2af"
    )
)
w3.eth.defaultAccount = "0xA5C9F2ebC96B4EE1Ec2908Daa0d1eCD9aDBe0caF"

# loading ABI
with open("./ABI/lcurate_abi.json", "r") as f:
    contract_abi = json.load(f)

tags_contract_address = "0x66260C69d03837016d88c9877e61e08Ef74C59F2"
tokens_contract_address = "0xeE1502e29795Ef6C2D60F8D7120596abE3baD990"
cdn_contract_address = "0x957A53A994860BE4750810131d9c876b2f52d6E1"
# Initialize contracts
tags_contract = w3.eth.contract(address=tags_contract_address, abi=contract_abi)
tokens_contract = w3.eth.contract(address=tokens_contract_address, abi=contract_abi)
cdn_contract = w3.eth.contract(address=cdn_contract_address, abi=contract_abi)


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
    url=f"https://ipfs.kleros.io{ipfs_url}"
    print("Token image URL", url)
    try:
        
        response = requests.get(url)
        print("Token retrieval response code",response.status_code)
        if response.status_code == 200:
            # Parse the JSON response
            print("token image retrieval okay")
            return response
        else:
            raise Exception(
                f"Failed to get proper response on token image from IPFS: {response.status_code}, {response.text}"
            )
    except Exception as e:
        print(f"Error fetching logo image from IPFS: {e}")
        response=""
        


    return response


def getSubgraphResults(query):

    # Define the URL of the GraphQL endpoint
    graphql_url = "https://api.thegraph.com/subgraphs/name/kleros/legacy-curate-xdai"

    # Prepare the HTTP request
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}

    # Send the HTTP request
    response = requests.post(graphql_url, headers=headers, json=payload)

    # Check for a valid response
    response.raise_for_status()

    # Parse and return the JSON response
    return response.json()


def createTagsPrompt(_itemID, data, timeStampToCheckAt):
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
    perplexity_text_results ='No results from Perplexity.ai'
    try:    
        perplexity = Perplexity()   
        response = perplexity.search_sync(  # search_sync returns the final dict while search returns a generator that streams in results
            "Do a thorough search online and tell me what the contract at this address is for? "
            + curatedObject["values"]["Contract Address"].split(":")[-1].strip()
        )
        #print(response);
        perplexity_text_results = response["answer"]  # 'response'

        perplexity.close()
    except Exception as e:
        print(f"Error searching in perplexity: {e}")
    # do some parsing with this response

    # Check for duplicates
    query= f"""
    {{
        litems(where:{{key0_starts_with_nocase:"{curatedObject["values"]["Contract Address"].lower()}", registry:"{tags_contract_address.lower()}", status_in:[Registered,ClearingRequested]}}){{
            itemID
            key0
            key1
            key2
            key3
            key4
            status
            latestRequestSubmissionTime
        }}
    }}
    """
    existingEntries = getSubgraphResults(query)["data"]["litems"]

    # Filter existingEntries with 'latestRequestSubmissionTime' < timeStampToCheckAt
    filteredEntries = [
        entry for entry in existingEntries
        if entry.get('latestRequestSubmissionTime', float('inf')) < timeStampToCheckAt
    ]

    try:
        OpenAI_prompt = (
            "This is the acceptance policy for this registry: \n```"
            + policyText
            + "```\n\n"
            + "Here is the information submitted about the contract: \n```"
            + object_to_text_lines(curatedObject["values"])
            + "```\n\n"
            + "The information found independently from the internet about this contract: \n```"
            + perplexity_text_results
            + "\n\n"
            + "If there is already an entry for this address on this chain, it should be rejected outright. After checking the subgraph for this registry, it is "
            + str(len(filteredEntries) > 0)
            + " that there is already an existing entry for this address on this chain"
            + (
                (
                    " and it can be found at https://curate.kleros.io/tcr/100/"
                    + tags_contract_address
                    + "/"
                    + filteredEntries[0]["itemID"]
                )
                if len(filteredEntries) > 0
                else ""
            )
            + "."
            + "```\n\n"
            + "Taking into account both the acceptance policy and the information found online (only mention this if actually available above), do you think the entry should be accepted into the registry?  Make sure that the information submitted makes sense intrinsically and is not nonsense. End off your response using ACCEPT, REJECT or INCONCLUSIVE."
        )
        #print(OpenAI_prompt)
    except Exception as e:
        print(f"Error creating OpenAI query: {e}")

    return OpenAI_prompt

def createCDNPrompt(_itemID, data,timeStampToCheckAt):
    try:
        # Fetch JSON from IPFS
        policyText = extractPDF("/ipfs/QmP3be4kpiNrDx4nV222UsT3sAwi846xNkq4tctTVNJYfJ")
    except Exception as e:
        print(f"Error fetching policy from IPFS: {e}")
    # fetch itemID's data object
    try:
        curatedObject = fetch_json("https://ipfs.kleros.io" + data)
    except Exception as e:
        print(f"Error fetching curated IPFS object: {e}")

    # Analyze with Perplexity.AI
    perplexity_text_results ='No results from Perplexity.ai'
    try:
        perplexity = Perplexity()
        response = perplexity.search_sync(  # search_sync returns the final dict while search returns a generator that streams in results
            "Do a thorough search online and tell me what the contract at this address is for?"
            + curatedObject["values"]["Contract address"].split(":")[-1].strip()
        )  # using Address instead of 'Contract Address' due to different field name
        perplexity_text_results = response["answer"]  # 'response'

        perplexity.close()
    except Exception as e:
        print(f"Error searching in perplexity: {e}")
    # do some parsing with this response

    # Check for duplicates
    query= f"""
    {{
        litems(where:{{key0_starts_with_nocase:"{curatedObject["values"]["Contract address"].lower()}", registry:"{cdn_contract_address.lower()}", status_in:[Registered,ClearingRequested]}}){{
            itemID
            key0
            key1
            key2
            key3
            key4
            status
            latestRequestSubmissionTime
        }}
    }}
    """
    existingEntries = getSubgraphResults(query)["data"]["litems"]
    print(existingEntries)
    filteredEntries = [
        entry for entry in existingEntries
        if entry.get('latestRequestSubmissionTime', float('inf')) < timeStampToCheckAt and entry.get('key1') == curatedObject["values"]["Domain name"]
    ]
    
    final_domain=returnfinaldomain(curatedObject["values"]["Domain name"])
    print("Final domain", final_domain==curatedObject["values"]["Domain name"])
    
    try:
        OpenAI_prompt_text = (
            "This is the acceptance policy for this registry: \n```"
            + policyText
            + "```\n\n"
            + "Here is the information submitted about this supposed contract: \n```"
            + object_to_text_lines(curatedObject["values"])
            + "```\n\n"
            + "The information found independently from the internet about this supposed token contract: \n```"
            + perplexity_text_results
            #+ "```\n\n"
            #+ "There is an image provided with this prompt, in which the address "+curatedObject["values"]["Contract address"]+ " should be visible in full or truncated form."
            + "\n\n"
            + (
                (
                   "This entry should be rejected as it actually redirects to "+str(final_domain)
                )
                if final_domain!=curatedObject["values"]["Domain name"]
                else ""
            )
            +"\n\n"
            + "If there is already an entry for this combination address and domain name on this chain, it should be rejected outright (quote the link in the next sentence in your response). After checking the subgraph for this registry, it is "
            + str(len(filteredEntries) > 0)
            + " that there is already an existing entry for this address on this chain"
            + (
                (
                    " and it can be found at https://curate.kleros.io/tcr/100/"
                    + cdn_contract_address
                    + "/"
                    + filteredEntries[0]["itemID"]
                )
                if len(filteredEntries) > 0
                else ""
            )
            + "."
            + "```\n\n"
            + "Note that domains with 'www' as a prefix needs to show that exactly in the screenshot."
            + "```\n\n"
            + "Taking into account the image/screenshot provided, the coherence of the information submitted in the entry, their coherence with the acceptance policy and the information found online (only mention this if actually available above), do you think the entry should be accepted into the registry?  Make sure that the information submitted makes sense intrinsically and is not nonsense. Keep your responses concise and no more than 200 words. End off your response using the exact strings ACCEPT, REJECT or INCONCLUSIVE."
        )
        print(OpenAI_prompt_text)
        OpenAI_prompt=  [{"type":"text", "text": OpenAI_prompt_text },{"type" : "image_url", "image_url":{"url":"https://ipfs.kleros.io"+curatedObject["values"]["Visual proof"]}}]
    except Exception as e:
        print(f"Error creating OpenAI query: {e}")

    return OpenAI_prompt

def hasTransparency(image):
    # Convert to RGBA if it is not already
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Check for transparency
    for pixel in image.getdata():
        if pixel[3] < 255:
            return True  # Image has transparency

    return False  # Image does not have transparency

def returnfinaldomain(domain):
    response = requests.get("https://"+domain)

    # Extract the domain after the final redirect
    final_domain = urlparse(response.url).netloc
    return final_domain

def createTokensPrompt(_itemID, data,timeStampToCheckAt):
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
        has_transparency = hasTransparency(image)
        logo_width, logo_height = image.size
        logo_format = image.format.lower()

    except Exception as e:
        logo_width = "unknown"
        logo_height = "unknown"
        logo_format = "unknown"
        has_transparency = False

        print(f"Error logo image from IPFS: {e}")

    # Analyze with Perplexity.AI
    perplexity_text_results ='NO RESULTS FROM PERPLEXITY.AI'
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
    
    # Check for duplicates
    query= f"""
    {{ 
        litems(where:{{key0_starts_with_nocase:"{":".join(curatedObject["values"]["Address"].lower().split(":")[:2])}", registry:"{tokens_contract_address.lower()}", status_in:[Registered,ClearingRequested], key2:"{curatedObject["values"]["Symbol"]}"}}){{
            itemID
            key0
            key1
            key2
            key3
            key4
            status
            latestRequestSubmissionTime
        }}
        litems2: litems(where:{{key0_starts_with_nocase:"{curatedObject["values"]["Address"].lower()}", registry:"{tokens_contract_address.lower()}", status_in:[Registered,ClearingRequested]}}){{
            itemID
            key0
            key1
            key2
            key3
            key4
            status
            latestRequestSubmissionTime
        }}
    }}
    """ #Adding special logic to query on the first parts of the address only to allow for checking of duplicates for the same ticker as well. 
    
    # Execute the GraphQL query
    query_results = getSubgraphResults(query)
    
    # Extract the results for 'litems' and 'litems2'
    litems_results = query_results["data"]["litems"]
    litems2_results = query_results["data"]["litems2"]

    # Combine the results from both queries into a single list
    existingEntries = litems_results + litems2_results

    filteredEntries = [
        entry for entry in existingEntries
        if entry.get('latestRequestSubmissionTime', float('inf')) < timeStampToCheckAt
    ]

    try:
        OpenAI_prompt = (
            "This is the acceptance policy for this registry: \n```"
            + policyText
            + "```\n\n"
            + "Here is the information submitted about this supposed token contract: \n```"
            + object_to_text_lines(curatedObject["values"])
            + "```\n\n"
            + "The information found independently from the internet about this supposed token contract: \n```"
            + perplexity_text_results
            + "```\n\n"
            + "The format of the token's logo is "
            + str(logo_width)
            + " x "
            + str(logo_height)
            + " and the format is ."
            + str(logo_format)
            + " . Verify that both the width and height of the image are greater than the dimensions set out in the policy. The width and height do not have to be the same. Acknowledge that you can't comment on how the image looks like yet."
            + "\n\n"
            + "It is "+str(has_transparency)+" that the image is transparent."
            + "\n\n"
            + "If there is already an entry for this address on this chain, it should be rejected outright. After checking the subgraph for this registry, it is "
            + str(len(filteredEntries) > 0)
            + " that there is already an existing entry for this address on this chain"
            + (
                (
                    " and it can be found at https://curate.kleros.io/tcr/100/"
                    + tokens_contract_address
                    + "/"
                    + filteredEntries[0]["itemID"]
                )
                if len(filteredEntries) > 0 and filteredEntries[0]["key2"] == curatedObject["values"]["Symbol"] #checking for duplicates on ticker and chain.
                else ""
            )
            + "."
            + "```\n\n"
            + "If the name of the token is not phrased exactly as it is found online (e.g. 'Phala' vs 'Phala Network'), recommend to reject."
            + "```\n\n"
            + "Taking into account both the acceptance policy, the image dimensions, and the information found online (only mention this if actually available above), do you think the entry should be accepted into the registry?  Make sure that the information submitted makes sense intrinsically and is not nonsense. End off your response using the exact strings ACCEPT, REJECT or INCONCLUSIVE."
        )
        print(OpenAI_prompt)
    except Exception as e:
        print(f"Error creating OpenAI query: {e}")

    return OpenAI_prompt


# Function to handle new item events
def handle_event(_itemID, data, registryType, timeStampToCheckAt, mode):
    response = {'openai_commentary': '', 'verdict': 'UNAVAILABLE'} # setting default

    try:
        # data = event["args"]["_data"]
        print("itemID: " + str(_itemID))
        print("data: " + data)
        print("registryType:"+ registryType)
    except Exception as e:
        print(f"Error in parsing event data: {e}")
        return response

    if registryType == "Tags":
        OpenAI_prompt = createTagsPrompt(_itemID, data,timeStampToCheckAt)
    elif registryType == "Tokens":
        OpenAI_prompt = createTokensPrompt(_itemID, 
                                           data,timeStampToCheckAt)
    elif registryType == "CDN":
        OpenAI_prompt = createCDNPrompt(_itemID, data,timeStampToCheckAt)
    else:
        return

    # Analyze with OpenAI
    OpenAI_response={}
    if (registryType in ["Tokens", "Tags"]):
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
    elif registryType =='CDN':
        OpenAI_response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            max_tokens= 600,
            messages=[
                {
                    "role": "system",
                    "content": "You are a lawyer in the Kleros ecosystem, who only confirms and convicts when you are absolutely certain. You are clear and concise in your communication and likes to invite others to comment on your words.",
                },
                {"role": "user", "content": OpenAI_prompt}
            ],
            
        )

    
    
    response['openai_commentary'] = OpenAI_response["choices"][0]["message"]["content"]

    # Search for verdict in the description
    if "ACCEPT" in response['openai_commentary']:
        response['verdict'] = 'ACCEPT'
    elif "REJECT" in response['openai_commentary']:
        response['verdict'] = 'REJECT'
    elif "INCONCLUSIVE" in response['openai_commentary']:
        response['verdict'] = 'INCONCLUSIVE'
    
    if (mode =='COMMENT_ONCHAIN'): #Send comments onchain only if requested.
        # Saving the evidence to Kleros's IPFS node
        if registryType == "Tokens":
            deityName = "Eunomia, AI goddess of good order"
        elif registryType == "Tags":
            deityName = "Dikē, AI goddess of fair judgements"
        elif registryType == "CDN":
            deityName = "Eirene, AI goddess of peace"
        else:
            deityName = "Zeus, who works only when no one does."
            
        expression = f"Opinion by {deityName}"
        evidence_object = {
            "title": expression,
            "description": OpenAI_response["choices"][0]["message"]["content"],
        }
        evidenceIpfsUri = postJSONtoKlerosIPFS(evidence_object)
        print(evidenceIpfsUri)

        # Submit evidence to the contract

        # Get the transaction data
        if registryType == "Tags":
            transaction_data = tags_contract.functions.submitEvidence(
                _itemID, evidenceIpfsUri
            ).build_transaction(
                {
                    "gas": 2000000,
                    "nonce": w3.eth.get_transaction_count(w3.eth.defaultAccount),
                }
            )
        elif registryType == "Tokens":
            transaction_data = tokens_contract.functions.submitEvidence(
                _itemID, evidenceIpfsUri
            ).build_transaction(
                {
                    "gas": 2000000,
                    "nonce": w3.eth.get_transaction_count(w3.eth.defaultAccount),
                }
            )
        elif registryType == "CDN":
            transaction_data = cdn_contract.functions.submitEvidence(
                _itemID, evidenceIpfsUri
            ).build_transaction(
                {
                    "gas": 2000000,
                    "nonce": w3.eth.get_transaction_count(w3.eth.defaultAccount),
                }
            )
        else:
            return

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
    return response