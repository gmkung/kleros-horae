from perplexity import Perplexity
import json

perplexity = Perplexity()
answer = perplexity.search_sync("What is the meanifffng of life?")

print(answer["answer"])

perplexity.close()
