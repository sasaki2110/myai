# 01.5_ReAct_FunctionCall.py
import asyncio
import math
from openai import AsyncOpenAI
from cost_utils import UsageCostCalculator  # フェーズ0で作ったユーティリティ

client = AsyncOpenAI()

# 外部ツール / 関数例
def calculator(a: int, b: int, op: str) -> str:
    if op == "add":
        return str(a + b)
    elif op == "mul":
        return str(a * b)
    else:
        return "Unsupported operation"

async def react_example():
    # Thought 生成
    thought = "2と3を掛ける計算を行う必要がある。"
    print(f"=== Thought ===\nThought: {thought}\n")

    # Action 生成
    action = "mul"  # 例: 掛け算
    observation = calculator(2, 3, action)
    print(f"=== Action ===\nAction: {action}\n")
    print(f"=== Observation ===\nObservation: {observation}\n")

    # AI に最終回答を生成させる
    prompt_answer = f"""
    あなたはReActエージェントです。
    Thought: {thought}
    Action: {action}
    Observation: {observation}
    Answerを出力してください。
    """

    resp = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt_answer}]
    )

    # 表示
    content = resp.choices[0].message.content
    print("=== Prompt Answer ===")
    print(prompt_answer)
    print("\n=== Answer ===")
    print(content)

    # コスト計算
    usage = UsageCostCalculator(resp)
    usage.report()

if __name__ == "__main__":
    asyncio.run(react_example())
