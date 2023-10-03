from policebot import handle_event

itemId = "0xf22e1721d7f5c3c1674cf6327248a3c0098e6e61fbe37219fdcafac6f8487e94"
ipfsUri = "/ipfs/QmY8QHVB44t74AnUGRtQmA7M55mc6WBB1PWX1amCvXDuE4/token.json"


bytes_object = bytes.fromhex(itemId[2:])

handle_event(bytes_object, ipfsUri, 'Tokens')
