# react_demo.py
from cost_utils import UsageCostCalculator
from openai import OpenAI

client = OpenAI()

prompt = """あなたはReActエージェントです。
次のフォーマットで推論してください：

Thought: あなたの考え
Action: 実行するアクション名
Observation: 行動の結果
Answer: 最終回答

質問: 2と3を掛けてください
"""

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}]
)

print(resp.choices[0].message.content)

# トークン数と料金計算
calc = UsageCostCalculator(resp)
calc.report()
