from perplexityai import Perplexity

prompt = input("👦: ")
for a in Perplexity().generate_answer(prompt):
    print(f"🤖: {a['answer']}")