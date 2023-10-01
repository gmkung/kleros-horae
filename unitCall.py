from policebot import handle_event

itemId = "0x88c8f96d1de9a6885bbd84c4490246c0bca038b56ca3dea7533db7f4e275ddd7"
ipfsUri = "/ipfs/QmeKuothr6kKpVnDrjFDHEsYuUCTbwoXKC61Un2hJGVJcf/item.json"


bytes_object = bytes.fromhex(itemId[2:])
print(bytes_object)

handle_event(bytes_object, ipfsUri)
