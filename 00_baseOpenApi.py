# openai_chat.py
from openai import OpenAI
client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "あなたは親切なアシスタントです"},
        {"role": "user", "content": "こんにちは、自己紹介してください"}
    ]
)
print(resp.choices[0].message.content)
