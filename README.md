# Sisters of Horae 

A set of tools that can be used to programmatically check the correctness of entries on Kleros' 3x metaregistries.

## Description

Submitting and challenging entries on Kleros Curate can be a very time-consuming and subjective task. The scripts/tools in this repo are tools that uses Perplexity.ai (for online searches) and OpenAI's chatCompletion API (for policy interpretation, image recognition, etc ...) programmatically 'police' the three main registries of Kleros Curate ([Tags](https://curate.kleros.io/tcr/100/0x66260C69d03837016d88c9877e61e08Ef74C59F2), [Tokens](https://curate.kleros.io/tcr/100/0xeE1502e29795Ef6C2D60F8D7120596abE3baD990) and [Contract Domain Names](https://curate.kleros.io/tcr/100/0x957A53A994860BE4750810131d9c876b2f52d6E1)). It can also automatically post the results on-chain as evidence under the entry.

In this latest versionm, each of the [three mythological Sisters of Horae](https://en.wikipedia.org/wiki/Horae) is assigned to each of the three registries:
* Dikē -> Tags
* Eunomia -> Tokens
* Eirene -> CDN

## Installation

The policebot.py script is the main script here, which contains the 'handle_event' function. which takes the following arguments:

1. _itemID (byte-encoded Curate itemID)
2. data (the ipfs URI of the Light Curate object)
3. registryType (accepts 'Tags', 'Tokens' or 'CDN' as values)
4. timeStampToCheckAt (the unix time-stamp to take into account when looking for duplicates)
5. mode (if set to 'COMMENT_ONCHAIN', it will post the results as evidence to the entry, otherwise it will just return the results locally)

The OpenAI API key and Ethereum address PK are just set as environmental variables for simplicity at this moment:
OpenAI_API_Key (e.g. sk-FB7...........jkxyz)
ETH_bot_private_key (e.g. 6034312......7760)
