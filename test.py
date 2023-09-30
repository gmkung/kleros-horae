from perplexity import Perplexity
import json

perplexity = Perplexity()
answer = perplexity.search("What is the meaning of life?")

print(json.dumps(next(answer)))
perplexity.close()
