from policebot import handle_event

itemId = "0xa1a5c92216ba2cf3c941f7af94acffc6f238406fd0e6462bcc5a8c5a6393f0bc"
ipfsUri = "/ipfs/QmP8okfrwYUedXbZPDhQKxK1so4PY5LMeojpJEm7pHPSLz/item.json"


bytes_object = bytes.fromhex(itemId[2:])
print(bytes_object)

handle_event(bytes_object, ipfsUri)
