# 00_baseOpenApiAsync.py
import asyncio
from openai import AsyncOpenAI
from cost_utils import UsageCostCalculator

async def main():
    client = AsyncOpenAI()

    resp = await client.chat.completions.create(
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

# 実行
if __name__ == "__main__":
    asyncio.run(main())