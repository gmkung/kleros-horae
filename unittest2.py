import os
import openai

openai.api_key = "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"
# os.getenv("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")

OpenAI_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user",
            "content": "Tell me if you are a beautiful assistant and what Kleros does.",
        }
    ],
)

print(OpenAI_response['choices'][0]['message']['content'])
