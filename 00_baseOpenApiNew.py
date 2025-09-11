# 00_baseOpenApiNew.py
from openai import OpenAI
from cost_utils import UsageCostCalculator

client = OpenAI()

resp = client.responses.create(
    model="gpt-4.1-mini",
    instructions="あなたは親切なアシスタントです",
    input="こんにちは、自己紹介してください"
)

# レスポンス表示
print("=== AI Response ===")
print(resp.output[0].content[0].text)

# トークン数と料金計算
# calc = UsageCostCalculator(resp)
# calc.report()
