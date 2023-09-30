from web3 import Web3
import json
import os
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
itemId = b"f\xbc{C\xa8\xf2\x18F\x08\x80C\xa4fT\xbb\x96\xdc\xa3\xe1~ue|s\xc4\xde\xfdB\x8e=\xd0\xf5"
ipfsUrl = "/ipfs/sdfsdfkjshdfjkshdjkf"

# Submit evidence to the contract


# Get the transaction data
transaction_data = contract.functions.submitEvidence(itemId, ipfsUrl).build_transaction(
    {
        "gas": 2000000,
        "nonce": w3.eth.get_transaction_count(w3.eth.defaultAccount),
    }
)
# Sign the transaction
signed_txn = w3.eth.account.sign_transaction(
    transaction_data, os.environ.get("ETH_bot_private_key", "default_value")
)

# Send transaction
txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

# Wait for transaction to be mined
txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

print(txn_receipt)
