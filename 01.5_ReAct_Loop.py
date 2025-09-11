# 01_ReAct_Loop.py
import math
from openai import OpenAI
from cost_utils import UsageCostCalculator  # フェーズ0で作ったユーティリティ

# --- ここでモデルを切り替え可能 ---
MODEL_NAME = "gpt-4.1-mini"  # 例: "gpt-5-nano", "gpt-4.1-mini"
#MODEL_NAME = "gpt-5"  # 例: "gpt-5-nano", "gpt-4.1-mini"

client = OpenAI()

# --- 外部関数（ツール）例 ---
def calculator(action_input: str):
    """簡単な計算ツール"""
    try:
        return str(eval(action_input, {"__builtins__": None}, {"math": math}))
    except Exception as e:
        return f"Error: {e}"

# --- ReActプロンプトテンプレート ---
def build_prompt(thought="", action="", observation="", question=""):
    prompt = f"""
あなたはReActエージェントです。
次のフォーマットで回答してください：

Thought: あなたの考え
Action: 実行するアクション名または式
Observation: 行動の結果
Answer: 最終回答

{thought}{action}{observation}
質問: {question}
"""
    return prompt

# --- 学習したい質問 ---
#question = "2と3を掛けてください"
question = "今の東京の天気は？"

# Step 1: Thought を生成
prompt_thought = build_prompt(question=question)
resp_thought = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": prompt_thought}]
)
thought = resp_thought.choices[0].message.content
UsageCostCalculator(resp_thought).report()

print("=== Thought ===")
print(thought.strip())

# Step 2: Action を生成
prompt_action = build_prompt(thought=f"Thought: {thought}\n", question=question)
resp_action = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": prompt_action}]
)
action = resp_action.choices[0].message.content
UsageCostCalculator(resp_action).report()

print("\n=== Action ===")
print(action.strip())

# Step 3: Observation（外部関数呼び出し）
#observation_result = calculator("2*3")
observation_result = "今日の東京は、気温32.5度・湿度64%・晴れ"
observation_text = f"Observation: {observation_result}"

print("\n=== Observation ===")
print(observation_text)

# Step 4: Answer を生成
prompt_answer = build_prompt(
    thought=f"Thought: {thought}\n",
    action=f"Action: {action}\n",
    observation=f"{observation_text}\n",
    question=question
)
resp_answer = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": prompt_answer}]
)
answer = resp_answer.choices[0].message.content
UsageCostCalculator(resp_answer).report()

print("\n=== Answer ===")
print(answer.strip())
