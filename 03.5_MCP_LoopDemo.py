# 03_5_MCP_LoopDemo.py
from typing import Dict, Any

# --- モックツール関数 ---
def multiply(a: str, b: str) -> str:
    return str(int(a) * int(b))

def get_weather(city: str) -> str:
    # モックの天気情報
    weather_data = {
        "東京": "晴れ、気温30度、湿度60%",
        "大阪": "曇り、気温28度、湿度70%",
        "金沢": "情報なし"
    }
    return weather_data.get(city, "情報なし")

# --- ユーザー入力 ---
user_input = input("User query: ")

# 初回 Observation はユーザー入力
observation = {"type": "user_input", "content": user_input}

# ループ開始
while True:
    # --- Thought ---
    thought: Dict[str, Any] = {"plan": None}

    # ツールを使うか判断（簡単なルールベース）
    if "掛けて" in observation["content"]:
        thought["plan"] = "multiply"
    elif "天気" in observation["content"]:
        thought["plan"] = "get_weather"
    else:
        thought["plan"] = "answer_directly"

    print(f"> Thought: {thought}")

    # --- Action ---
    action_output = None
    if thought["plan"] == "multiply":
        parts = observation["content"].split()
        nums = [p for p in parts if p.isdigit()]
        if len(nums) == 2:
            action_output = multiply(nums[0], nums[1])
        else:
            action_output = "数字が見つかりません"
    elif thought["plan"] == "get_weather":
        # 「東京の天気は？」のように都市名を抽出（簡易）
        city = observation["content"].replace("の天気は？", "").strip()
        action_output = get_weather(city)
    elif thought["plan"] == "answer_directly":
        # LLMを呼ぶ代わりにそのまま返す（モック）
        action_output = f"回答: {observation['content']}"

    print(f"> Action result: {action_output}")

    # --- Feedback ---
    # Action結果をObservationとして次ループに渡す
    observation = {"type": "action_result", "content": action_output}

    # 終了条件（Final Answer）
    # 今回は一回のループで完結する
    print(f"=== Final Answer ===\n{action_output}")
    break
