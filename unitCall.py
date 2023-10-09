from policebot import handle_event

itemId = "0x02d90cb7add0898ea4fe01334c422668b40f59988c1c680edb658a78b8986b49"
ipfsUri = "/ipfs/QmQZz1SQoS8emDRJ3Xm1nwL4RDarXEj8bVZCRWCunhAJRR/item.json"


bytes_object = bytes.fromhex(itemId[2:])

handle_event(bytes_object, ipfsUri, "Tags")
