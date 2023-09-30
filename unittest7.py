from perplexityai.Perplexity import Perplexity

perplexity = Perplexity()
answer = perplexity.search("What is the meaning of life?")
for a in answer:
    print(a)
perplexity.close()