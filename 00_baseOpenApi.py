# 00_baseOpenApi.py
from openai import OpenAI
from cost_utils import UsageCostCalculator

client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "あなたは親切なアシスタントです"},
        {"role": "user", "content": "こんにちは、自己紹介してください"}
    ]
    # , max_completion_tokens=100 # 必要に応じて最大トークン数を指定　だけど回答されなくなりリスク有り
)

# レスポンス表示
print("=== AI Response ===")
print(resp.choices[0].message.content)

# トークン数と料金計算
calc = UsageCostCalculator(resp)
calc.report()
