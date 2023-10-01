from policebot import handle_event

itemId = "0x26566c428b92444a45d95f8bbb8d55f32c077faf0439fd66cf9172ce298fa3b0"
ipfsUri = "/ipfs/QmSejKm5V3dNMW175aDbuzxjC9q7Jv5QAG9NdMNhJk6ZGA/item.json"


bytes_object = bytes.fromhex(itemId[2:])

handle_event(bytes_object, ipfsUri)
