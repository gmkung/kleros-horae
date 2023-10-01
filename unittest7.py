from perplexity import Perplexity
import json

perplexity = Perplexity()
answer = perplexity.search_sync(
    "Do an exhaustive search online and tell me what the contract at this address is for? 0x3a00c557a2a0b7d4c5e05679c7904A970e5caccd"
)

print(answer["answer"])

perplexity.close()
