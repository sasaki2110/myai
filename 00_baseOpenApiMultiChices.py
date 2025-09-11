# openai_chat.py
from openai import OpenAI
client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "user", "content": "こんにちは!"}
    ],
    n=3  # 選択肢を3つ生成
)

for i, choice in enumerate(resp.choices):
    print(f"--- 選択肢 {i} ---")
    print(choice.message.content)

# トークン使用量の表示
print("---- トークン使用量 ----")
print("Prompt tokens:", resp.usage.prompt_tokens)
print("Completion tokens:", resp.usage.completion_tokens)
print("Total tokens:", resp.usage.total_tokens)

# コスト計算 (例: gpt-4.1-mini 入力 $0.15/1K トークン, 出力 $0.60/1K トークン)
input_rate = 0.15 / 1_000_000
output_rate = 0.60 / 1_000_000

cost = resp.usage.prompt_tokens * input_rate + resp.usage.completion_tokens * output_rate
print(f"このリクエストのコスト: ${cost:.6f}")