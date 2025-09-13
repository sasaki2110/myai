# 04_mcpClientLlm2.py
# MCPクライアント - 動的ツール対応版
# サーバーから動的にツールを取得し、それに基づいて制御

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

def call_llm(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
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

def create_tools_schema(available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    利用可能なツールからOpenAI Function Calling用のスキーマを作成
    """
    tools_schema = []
    
    for tool in available_tools:
        tool_schema = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool.get("parameters", {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            }
        }
        tools_schema.append(tool_schema)
    
    return tools_schema

def analyze_user_input_with_llm_dynamic(input_text: str, available_tools: List[Dict[str, Any]], is_tool_result: bool = False) -> Dict[str, Any]:
    """
    LLMを使用してユーザー入力を分析し、動的にツールを選択
    """
    # 利用可能なツールのスキーマを作成
    tools_schema = create_tools_schema(available_tools)
    
    # ツールの詳細情報を文字列として構築
    tools_detail = []
    for tool in available_tools:
        tool_info = f"- {tool['name']}: {tool['description']}"
        
        # パラメータ情報を追加
        params = tool.get('parameters', {})
        if 'properties' in params and params['properties']:
            tool_info += "\n  パラメータ:"
            for param_name, param_info in params['properties'].items():
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '')
                required = param_name in params.get('required', [])
                required_mark = " (必須)" if required else " (任意)"
                tool_info += f"\n    - {param_name} ({param_type}){required_mark}: {param_desc}"
        else:
            tool_info += "\n  パラメータ: なし"
        
        tools_detail.append(tool_info)
    
    tools_detail_str = "\n".join(tools_detail)
    
    # システムメッセージを状況に応じて調整
    if is_tool_result:
        system_content = f"""あなたはMCP（Model Context Protocol）のエージェントです。
現在、ツールの実行結果を受け取っています。この結果を分析し、次のアクションを決定してください。

利用可能なツール:
{tools_detail_str}

以下の形式でJSONレスポンスを返してください:
{{
    "plan": "ツール名またはanswer_directly",
    "reasoning": "選択理由",
    "parameters": {{"パラメータ名": "値"}}
}}

重要:
- ツールの実行結果が得られた場合は、通常 "answer_directly" を選択して最終回答を提供してください
- 追加の情報が必要な場合のみ、他のツールを使用してください
- タスクが完了した場合は必ず "answer_directly" を選択してください

例:
- 計算結果が得られた場合: {{"plan": "answer_directly", "reasoning": "計算が完了しました", "parameters": {{}}}}
- 天気情報が得られた場合: {{"plan": "answer_directly", "reasoning": "天気情報を取得しました", "parameters": {{}}}}
"""
    else:
        system_content = f"""あなたはMCP（Model Context Protocol）のエージェントです。
ユーザーの入力を分析し、適切なアクションプランを決定してください。

利用可能なツール:
{tools_detail_str}

以下の形式でJSONレスポンスを返してください:
{{
    "plan": "ツール名またはanswer_directly",
    "reasoning": "選択理由",
    "parameters": {{"パラメータ名": "値"}}
}}

重要:
- ツールを使用する場合は、上記のパラメータ名を正確に使用してください
- 必須パラメータは必ず含めてください
- パラメータの型（string, integer等）に注意してください
- 計算が必要な場合は、multiplyツールを使用してください（直接計算しない）
- 天気情報が必要な場合は、get_weatherツールを使用してください
- 一般的な質問や会話の場合は "answer_directly" を選択してください

例:
- 掛け算の場合: {{"plan": "multiply", "reasoning": "数値の掛け算が要求されています", "parameters": {{"a": 3, "b": 5}}}}
- 天気の場合: {{"plan": "get_weather", "reasoning": "天気情報が要求されています", "parameters": {{"city": "東京"}}}}
- 直接回答の場合: {{"plan": "answer_directly", "reasoning": "ツールを使わずに直接回答します", "parameters": {{}}}}
"""
    
    # LLMに送信するメッセージ
    messages = [
        {
            "role": "system",
            "content": system_content
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
        
        # ツール名の検証
        valid_tool_names = [tool["name"] for tool in available_tools]
        if result.get("plan") not in valid_tool_names and result.get("plan") != "answer_directly":
            print(f"警告: 無効なツール名 '{result.get('plan')}' が選択されました。直接回答にフォールバックします。")
            result["plan"] = "answer_directly"
            result["reasoning"] = "無効なツール名のため直接回答にフォールバック"
            result["parameters"] = {}
        
        return result
    except json.JSONDecodeError:
        # JSONパースに失敗した場合のフォールバック
        return {
            "plan": "answer_directly",
            "reasoning": "LLMの応答を解析できませんでした",
            "parameters": {}
        }

def generate_dynamic_result_display(tool_name: str, parameters: Dict[str, Any], result: Any, tool_info: Dict[str, Any]) -> str:
    """
    ツールのスキーマ情報を基に、動的に結果表示を生成
    """
    # ツールの説明から表示形式を推測
    description = tool_info.get('description', '')
    
    # パラメータの情報を取得
    params = tool_info.get('parameters', {})
    properties = params.get('properties', {})
    
    # よくあるパターンに基づいて表示形式を決定
    if '掛け算' in description or 'multiply' in tool_name.lower():
        # 掛け算の場合
        a = parameters.get("a", "?")
        b = parameters.get("b", "?")
        return f"{a} × {b} = {result}"
    
    elif '天気' in description or 'weather' in tool_name.lower():
        # 天気の場合
        city = parameters.get("city", "?")
        return f"{city}の天気: {result}"
    
    elif '計算' in description or 'calculate' in tool_name.lower():
        # 計算系の場合
        param_values = []
        for param_name in properties.keys():
            if param_name in parameters:
                param_values.append(f"{param_name}={parameters[param_name]}")
        param_str = ", ".join(param_values) if param_values else "計算"
        return f"{param_str} = {result}"
    
    elif '情報' in description or 'info' in tool_name.lower():
        # 情報取得系の場合
        # 主要なパラメータを表示
        main_param = None
        for param_name, param_info in properties.items():
            if param_name in parameters and param_info.get('type') == 'string':
                main_param = parameters[param_name]
                break
        
        if main_param:
            return f"{main_param}の{description}: {result}"
        else:
            return f"{description}: {result}"
    
    else:
        # 汎用的な表示
        # 主要なパラメータがあれば表示
        main_params = []
        for param_name, param_info in properties.items():
            if param_name in parameters:
                main_params.append(f"{param_name}={parameters[param_name]}")
        
        if main_params:
            param_str = ", ".join(main_params)
            return f"{tool_name}({param_str}): {result}"
        else:
            return f"{tool_name}の結果: {result}"

def execute_tool_dynamically(client: MCPClient, tool_name: str, parameters: Dict[str, Any], available_tools: List[Dict[str, Any]]) -> str:
    """
    動的にツールを実行
    """
    # ツールが存在するかチェック
    tool_exists = any(tool["name"] == tool_name for tool in available_tools)
    
    if not tool_exists:
        return f"エラー: ツール '{tool_name}' が見つかりません"
    
    # ツールの詳細情報を取得
    tool_info = next((tool for tool in available_tools if tool["name"] == tool_name), None)
    
    if not tool_info:
        return f"エラー: ツール '{tool_name}' の情報を取得できません"
    
    # パラメータの検証
    required_params = tool_info.get("parameters", {}).get("required", [])
    missing_params = [param for param in required_params if param not in parameters]
    
    if missing_params:
        return f"エラー: 必須パラメータが不足しています: {missing_params}"
    
    # ツールを実行
    try:
        result = client.call_tool(tool_name, parameters)
        
        # 結果の表示形式を動的に生成
        return generate_dynamic_result_display(tool_name, parameters, result, tool_info)
            
    except Exception as e:
        return f"ツール実行エラー: {e}"

def react_loop_with_llm_dynamic(client: MCPClient, user_input: str, available_tools: List[Dict[str, Any]]):
    """
    動的ツール対応のMCPループを実行
    Observation → Thought → Action → Feedback の流れ
    """
    print(f"\n=== MCP Loop with Dynamic Tools ===")
    print(f"User Input: {user_input}")
    
    observation = user_input
    max_iterations = 5  # 無限ループを防ぐ
    iteration = 0
    is_tool_result = False  # ツール実行結果かどうかを追跡
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        print(f"Observation: {observation}")
        
        # --- Thought (LLM使用) ---
        print(f"\n--- Thought (LLM) ---")
        thought = analyze_user_input_with_llm_dynamic(observation, available_tools, is_tool_result)
        print(f"Plan: {thought['plan']}")
        print(f"Reasoning: {thought['reasoning']}")
        print(f"Parameters: {thought['parameters']}")
        
        # --- Action ---
        print(f"\n--- Action ---")
        action_output = ""
        
        if thought['plan'] == 'answer_directly':
            # LLMに直接回答を生成させる
            if is_tool_result:
                # ツール実行結果の場合は、結果を基に最終回答を生成
                messages = [
                    {
                        "role": "system",
                        "content": "ツールの実行結果を受け取りました。この結果を基に、ユーザーの質問に対する最終回答を提供してください。"
                    },
                    {
                        "role": "user",
                        "content": f"元の質問: {user_input}\nツール実行結果: {observation}"
                    }
                ]
            else:
                # 初回の場合は直接回答
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
            # 動的にツールを実行
            action_output = execute_tool_dynamically(
                client, 
                thought['plan'], 
                thought['parameters'], 
                available_tools
            )
            is_tool_result = True  # 次の反復ではツール結果として処理
        
        print(f"Action Result: {action_output}")
        
        # --- Feedback ---
        print(f"\n--- Feedback ---")
        observation = action_output
        
        # 終了条件チェック
        if thought['plan'] == 'answer_directly':
            print(f"\n=== Final Answer ===")
            print(f"{action_output}")
            break
    
    if iteration >= max_iterations:
        print(f"\n=== Max Iterations Reached ===")
        print(f"最大反復回数に達しました。最終結果: {action_output}")

def main():
    """メイン関数"""
    print("MCP Client with Dynamic Tools - gpt-4o-mini統合版")
    print("サーバー: http://localhost:8001")
    print("LLM: gpt-4o-mini")
    print("終了するには 'quit' または 'exit' と入力してください\n")
    
    # MCPクライアントを作成
    client = MCPClient()
    
    # サーバー接続テスト
    print("サーバーに接続中...")
    tools = client.get_tools()
    if tools:
        print(f"接続成功! 利用可能なツール: {[tool.get('name', 'unknown') for tool in tools]}")
        
        # ツールの詳細情報を表示
        print("\n=== 利用可能なツール詳細 ===")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
            params = tool.get('parameters', {})
            if 'properties' in params:
                print(f"  パラメータ: {list(params['properties'].keys())}")
            if 'required' in params:
                print(f"  必須パラメータ: {params['required']}")
        print()
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
            react_loop_with_llm_dynamic(client, user_input, tools)
            
        except KeyboardInterrupt:
            print("\n\n終了します。")
            break
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
