# function_calling.py
from openai import OpenAI
client = OpenAI()

functions = [
    {
        "name": "get_weather",
        "description": "都市の天気を取得する",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "東京の天気は？"}],
    functions=functions,
    function_call="auto",
)

print(resp.choices[0].message)
