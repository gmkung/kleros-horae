from policebot import handle_event

itemId = "0xdb3d890c18c324d82bad11d10906dedadd5eb654227e97603f25730e0362fad3"
ipfsUri = "/ipfs/QmdBp8CsWeDjy3wzDw4F2hV5JoTX4AqR8NwqzEGqNG6VLf/item.json"


bytes_object = bytes.fromhex(itemId[2:])

handle_event(bytes_object, ipfsUri, 'Tokens')
