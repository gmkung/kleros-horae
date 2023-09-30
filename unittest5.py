import json

with open("./ABI/lcurate_abi.json", "r") as f:
    contract_abi = json.load(f)

print(contract_abi)