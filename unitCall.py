from policebot import handle_event

itemId = "0x9c0744cc8a74bce1d14f038c951cf82564e5abb4e31af6c1998021fa5eb2ddb8"
ipfsUri = "/ipfs/Qmb5vWHTvFP6DuyrGGdix6PXmmK881Fh7XrXcdraniQW6Y/item.json"


bytes_object = bytes.fromhex(itemId[2:])

handle_event(bytes_object, ipfsUri, 'Tokens')
