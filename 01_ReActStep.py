# 01_ReAct_step_by_step.py
from openai import OpenAI

client = OpenAI()

# 質問
question = "2と3を掛けてください"

# ---------- Step 1: Thought ----------
prompt_thought = f"""
あなたはReActエージェントです。
次のフォーマットで推論してください：

Thought: あなたの考え
Action: 実行するアクション名
Observation: 行動の結果
Answer: 最終回答

質問: {question}

次に出力するのは Thought だけです。
"""

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt_thought}]
)
thought_text = resp.choices[0].message.content.strip()
print("=== Thought ===")
print(thought_text)

# ---------- Step 2: Action ----------
prompt_action = f"""
前回の Thought: {thought_text}

次に出力するのは Action だけです。
"""
resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt_action}]
)
action_text = resp.choices[0].message.content.strip()
print("\n=== Action ===")
print(action_text)

# ---------- Step 3: Observation ----------
# このステップでは自動計算を行う想定
if "計算を実行" in action_text:
    observation_text = "2 × 3 = 6"
else:
    observation_text = "何もしない"

print("\n=== Observation ===")
print(observation_text)

# ---------- Step 4: Answer ----------
prompt_answer = f"""
Thought: {thought_text}
Action: {action_text}
Observation: {observation_text}

次に出力するのは Answer だけです。
"""
print("\n=== Prompt Answer ===")
print(prompt_answer)

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt_answer}]
)
answer_text = resp.choices[0].message.content.strip()
print("\n=== Answer ===")
print(answer_text)

# トークン数と料金計算
from cost_utils import UsageCostCalculator
calc = UsageCostCalculator(resp)
calc.report()