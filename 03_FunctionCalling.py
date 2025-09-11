# 03_FunctionCalling.py
from openai import OpenAI
import json

# OpenAI クライアント
client = OpenAI()

# モック関数
def get_weather(city: str) -> str:
    """モック天気関数"""
    mock_data = {
        "東京": "晴れ、気温30度、湿度60%",
        "大阪": "曇り、気温28度、湿度70%",
        "札幌": "雨、気温20度、湿度80%",
    }
    return mock_data.get(city, "不明な都市です")

# Function Calling 用の定義
functions = [
    {
        "name": "get_weather",
        "description": "指定された都市の、現在の天気を取得する",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    }
]

# ユーザーの入力
# user_query = "東京の天気は？"
# user_query = "日本の首相は？"
#user_query = "生命、宇宙、そして万物についての究極の疑問の答えは何ですか？"
user_query = "2024年3月2日の東京の天気は？"

# 1️⃣ LLM に最初に問い合わせる（関数を呼ぶか判断）
resp1 = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": user_query}],
    functions=functions,
    function_call="auto"
)

message1 = resp1.choices[0].message

# 2️⃣ 関数呼び出しが必要かチェック
if message1.function_call:
    # 関数名と引数を取得
    func_name = message1.function_call.name
    func_args = json.loads(message1.function_call.arguments)

    # 今回は get_weather を呼ぶ
    if func_name == "get_weather":
        city = func_args["city"]
        observation = get_weather(city)

    # 3️⃣ 関数結果を LLM に渡して最終回答を生成
    resp2 = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": None, "function_call": message1.function_call},
            {"role": "function", "name": func_name, "content": observation}
        ]
    )

    final_message = resp2.choices[0].message
    print("=== Final Answer ===")
    print(final_message.content)

else:
    # 関数呼び出し不要 → LLM が直接回答
    print("=== Final Answer ===")
    print(message1.content)
