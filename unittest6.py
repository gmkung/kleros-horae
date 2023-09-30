from web3 import Web3
import requests
import pdfplumber
import json
from io import BytesIO
import time
import os
import openai
from perplexityai.Perplexity import Perplexity
import random


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

itemID = "0xc50f8ce87e0e7a838155fa771d43fc9bca5dada5c87f0ba6222763ca115df3f9"

evidenceIpfsUri = "/ipfs/sdfsdfjkshdfsdf"

formatted_itemID = Web3.to_bytes(text=itemID).ljust(32, b"\0")


print(formatted_itemID)

transaction = contract.functions.submitEvidence(
    formatted_itemID, evidenceIpfsUri
).buildTransaction(
    {
        "chainId": 100,  # Gnosis chain
        "gas": 2000000,
        "gasPrice": w3.toWei("20", "gwei"),
        "nonce": w3.eth.getTransactionCount(w3.eth.defaultAccount),
    }
)

# Sign the transaction
signed_txn = w3.eth.account.signTransaction(
    transaction, os.environ.get("ETH_bot_private_key", "default_value")
)

# Send the transaction
transaction_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

print("Evidence submitted!: " + transaction_hash.hex())

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
