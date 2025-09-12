# 04_mcpClientLlm.py
# MCPクライアント - LLM統合版
# 実際のLLM（gpt-4.1-mini）を使用してReActループを実行

import requests
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv
import os
from openai import OpenAI

# 環境変数を読み込み
load_dotenv()

# OpenAIクライアントを初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MCPClientクラス（既存と同じ）
class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツール一覧を取得"""
        try:
            response = self.session.get(f"{self.base_url}/tools")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ツール一覧の取得に失敗しました: {e}")
            return []
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """ツールを呼び出し"""
        try:
            payload = {
                "tool": tool_name,
                "parameters": parameters
            }
            response = self.session.post(
                f"{self.base_url}/call",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("result", "エラー: 結果が取得できませんでした")
        except requests.exceptions.RequestException as e:
            return f"ツール呼び出しエラー: {e}"

def call_llm(messages: List[Dict[str, str]], model: str = "gpt-4.1-mini") -> str:
    """LLMを呼び出してレスポンスを取得"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM呼び出しエラー: {e}"

def analyze_user_input_with_llm(input_text: str, available_tools: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    LLMを使用してユーザー入力を分析し、アクションプランを決定
    """
    # 利用可能なツールの情報を文字列に変換
    tools_info = []
    for tool in available_tools:
        tools_info.append(f"- {tool['name']}: {tool['description']}")
    tools_str = "\n".join(tools_info)
    
    # LLMに送信するメッセージ
    messages = [
        {
            "role": "system",
            "content": f"""あなたはMCP（Model Context Protocol）のエージェントです。
ユーザーの入力を分析し、適切なアクションプランを決定してください。

利用可能なツール:
{tools_str}

以下の形式でJSONレスポンスを返してください:
{{
    "plan": "ツール名またはanswer_directly",
    "reasoning": "選択理由",
    "parameters": {{"パラメータ名": "値"}}
}}

例:
- 掛け算の場合: {{"plan": "multiply", "reasoning": "数値の掛け算が要求されています", "parameters": {{"a": 3, "b": 5}}}}
- 天気の場合: {{"plan": "get_weather", "reasoning": "天気情報が要求されています", "parameters": {{"city": "東京"}}}}
- 直接回答の場合: {{"plan": "answer_directly", "reasoning": "ツールを使わずに直接回答します", "parameters": {{}}}}
"""
        },
        {
            "role": "user",
            "content": f"ユーザー入力: {input_text}"
        }
    ]
    
    # LLMを呼び出し
    response = call_llm(messages)
    
    try:
        # JSONレスポンスをパース
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # JSONパースに失敗した場合のフォールバック
        return {
            "plan": "answer_directly",
            "reasoning": "LLMの応答を解析できませんでした",
            "parameters": {}
        }

def extract_numbers_from_text(text: str) -> List[int]:
    """テキストから数値を抽出"""
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers]

def extract_city_from_text(text: str) -> str:
    """テキストから都市名を抽出"""
    cities = ["東京", "大阪", "名古屋", "福岡", "札幌", "横浜", "神戸", "京都", "仙台", "広島"]
    
    for city in cities:
        if city in text:
            return city
    
    return "東京"  # デフォルト

def react_loop_with_llm(client: MCPClient, user_input: str, available_tools: List[Dict[str, Any]]):
    """
    LLMを使用したMCPループを実行
    Observation → Thought → Action → Feedback の流れ
    """
    print(f"\n=== MCP Loop with LLM ===")
    print(f"User Input: {user_input}")
    
    observation = user_input
    max_iterations = 5  # 無限ループを防ぐ
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        print(f"Observation: {observation}")
        
        # --- Thought (LLM使用) ---
        print(f"\n--- Thought (LLM) ---")
        thought = analyze_user_input_with_llm(observation, available_tools)
        print(f"Plan: {thought['plan']}")
        print(f"Reasoning: {thought['reasoning']}")
        print(f"Parameters: {thought['parameters']}")
        
        # --- Action ---
        print(f"\n--- Action ---")
        action_output = ""
        
        if thought['plan'] == 'multiply':
            # パラメータから数値を取得、またはテキストから抽出
            params = thought['parameters']
            if 'a' in params and 'b' in params:
                a, b = params['a'], params['b']
            else:
                numbers = extract_numbers_from_text(observation)
                if len(numbers) >= 2:
                    a, b = numbers[0], numbers[1]
                else:
                    action_output = "掛け算に必要な数値が不足しています"
                    break
            
            if not action_output:
                result = client.call_tool("multiply", {"a": a, "b": b})
                action_output = f"{a} × {b} = {result}"
        
        elif thought['plan'] == 'get_weather':
            # パラメータから都市名を取得、またはテキストから抽出
            params = thought['parameters']
            if 'city' in params:
                city = params['city']
            else:
                city = extract_city_from_text(observation)
            
            result = client.call_tool("get_weather", {"city": city})
            action_output = f"{city}の天気: {result}"
        
        elif thought['plan'] == 'answer_directly':
            # LLMに直接回答を生成させる
            messages = [
                {
                    "role": "system",
                    "content": "ユーザーの質問に直接回答してください。簡潔で分かりやすく答えてください。"
                },
                {
                    "role": "user",
                    "content": observation
                }
            ]
            direct_answer = call_llm(messages)
            action_output = f"回答: {direct_answer}"
        
        else:
            action_output = f"不明なアクション: {thought['plan']}"
        
        print(f"Action Result: {action_output}")
        
        # --- Feedback ---
        print(f"\n--- Feedback ---")
        observation = action_output
        
        # 終了条件チェック
        if thought['plan'] in ['answer_directly', 'multiply', 'get_weather']:
            print(f"\n=== Final Answer ===")
            print(f"{action_output}")
            break
    
    if iteration >= max_iterations:
        print(f"\n=== Max Iterations Reached ===")
        print(f"最大反復回数に達しました。最終結果: {action_output}")

def main():
    """メイン関数"""
    print("MCP Client with LLM - gpt-4.1-mini統合版")
    print("サーバー: http://localhost:8001")
    print("LLM: gpt-4.1-mini")
    print("終了するには 'quit' または 'exit' と入力してください\n")
    
    # MCPクライアントを作成
    client = MCPClient()
    
    # サーバー接続テスト
    print("サーバーに接続中...")
    tools = client.get_tools()
    if tools:
        print(f"接続成功! 利用可能なツール: {[tool.get('name', 'unknown') for tool in tools]}")
    else:
        print("警告: サーバーに接続できませんでした。サーバーが起動しているか確認してください。")
        return
    
    # LLM接続テスト
    print("LLM接続テスト中...")
    test_response = call_llm([{"role": "user", "content": "Hello"}])
    if "LLM呼び出しエラー" in test_response:
        print(f"LLM接続エラー: {test_response}")
        print("APIキーが正しく設定されているか確認してください。")
        return
    else:
        print("LLM接続成功!")
    
    # メインループ
    while True:
        try:
            user_input = input("\nUser query: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '終了']:
                print("終了します。")
                break
            
            if not user_input:
                continue
            
            # MCPループを実行
            react_loop_with_llm(client, user_input, tools)
            
        except KeyboardInterrupt:
            print("\n\n終了します。")
            break
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
