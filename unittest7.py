from perplexity import Perplexity
import json

perplexity = Perplexity()
answer = perplexity.search_sync(
    "Tell me what the contract at this address is for? 0x445FE580eF8d70FF569aB36e80c647af338db351"
)

print(answer["answer"])

print(json.dumps(answer))

perplexity.close()
