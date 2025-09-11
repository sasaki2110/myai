# 04_mcpClient.py
# MCPクライアント - 疑似MCPループを実行
# シンプルなHTTP APIを使用

import requests
import json
from typing import Dict, Any, List

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

def react_loop(client: MCPClient, user_input: str):
    """
    疑似MCPループを実行
    Observation → Thought → Action → Feedback の流れ
    """
    print(f"\n=== MCP Loop Demo ===")
    print(f"User Input: {user_input}")
    
    # 初回 Observation はユーザー入力
    observation = user_input
    
    while True:
        print(f"\n--- Observation ---")
        print(f"Content: {observation}")
        
        # --- Thought ---
        print(f"\n--- Thought ---")
        thought = analyze_user_input(observation)
        print(f"Plan: {thought['plan']}")
        print(f"Reasoning: {thought['reasoning']}")
        
        # --- Action ---
        print(f"\n--- Action ---")
        if thought['plan'] == 'multiply':
            # 数値を抽出
            numbers = extract_numbers(observation)
            if len(numbers) >= 2:
                result = client.call_tool("multiply", {"a": numbers[0], "b": numbers[1]})
                action_output = f"{numbers[0]} × {numbers[1]} = {result}"
            else:
                action_output = "掛け算に必要な数値が不足しています"
        
        elif thought['plan'] == 'get_weather':
            # 都市名を抽出
            city = extract_city_name(observation)
            result = client.call_tool("get_weather", {"city": city})
            action_output = f"{city}の天気: {result}"
        
        elif thought['plan'] == 'answer_directly':
            action_output = f"回答: {observation}"
        
        else:
            action_output = "不明なアクションです"
        
        print(f"Action Result: {action_output}")
        
        # --- Feedback ---
        print(f"\n--- Feedback ---")
        # アクション結果を次のObservationとして設定
        observation = action_output
        
        # 終了条件チェック
        if thought['plan'] in ['answer_directly', 'multiply', 'get_weather']:
            print(f"\n=== Final Answer ===")
            print(f"{action_output}")
            break

def analyze_user_input(input_text: str) -> Dict[str, str]:
    """
    ユーザー入力を分析してアクションプランを決定
    （実際のLLMの代わりにルールベースで実装）
    """
    input_lower = input_text.lower()
    
    if any(keyword in input_lower for keyword in ["掛けて", "かけて", "×", "multiply", "計算"]):
        return {
            "plan": "multiply",
            "reasoning": "掛け算の要求を検出しました"
        }
    elif any(keyword in input_lower for keyword in ["天気", "weather", "気温", "温度"]):
        return {
            "plan": "get_weather",
            "reasoning": "天気情報の要求を検出しました"
        }
    else:
        return {
            "plan": "answer_directly",
            "reasoning": "直接回答が必要な質問です"
        }

def extract_numbers(text: str) -> List[int]:
    """テキストから数値を抽出"""
    import re
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers]

def extract_city_name(text: str) -> str:
    """テキストから都市名を抽出（簡易版）"""
    # よくある都市名のパターン
    cities = ["東京", "大阪", "名古屋", "福岡", "札幌", "横浜", "神戸", "京都"]
    
    for city in cities:
        if city in text:
            return city
    
    # デフォルトは東京
    return "東京"

def main():
    """メイン関数"""
    print("MCP Client - 疑似MCPループデモ")
    print("サーバー: http://localhost:8001")
    print("利用可能なツール: multiply, get_weather")
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
            react_loop(client, user_input)
            
        except KeyboardInterrupt:
            print("\n\n終了します。")
            break
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()