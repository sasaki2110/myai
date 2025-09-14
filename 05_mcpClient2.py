# 05_mcpClient2.py
# FastMCPを使用した汎用MCPクライアント
# 動的ツール選択版（LLM統合）

import asyncio
import re
from typing import Dict, Any, List
from fastmcp import Client
from openai import OpenAI
from dotenv import load_dotenv
import os

# 環境変数を読み込み
load_dotenv()

# OpenAIクライアントを初期化
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_llm(user_input: str, available_tools: List[Any]) -> tuple[str, Dict[str, Any]] | tuple[None, None]:
    """
    LLMにツール選択とパラメータ生成を依頼
    """
    # 利用可能なツールの情報を構築
    tools_info = []
    for tool in available_tools:
        schema = getattr(tool, 'inputSchema', {})
        properties = schema.get('properties', {}) if schema else {}
        required = schema.get('required', []) if schema else []
        
        tool_info = f"- {tool.name}: {tool.description}"
        if properties:
            param_details = []
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'string')
                is_required = param_name in required
                param_details.append(f"{param_name}({param_type}{'必須' if is_required else '任意'})")
            tool_info += f" [パラメータ: {', '.join(param_details)}]"
        tools_info.append(tool_info)
    
    tools_description = "\n".join(tools_info)
    
    # システムプロンプト
    system_prompt = f"""あなたはツール選択の専門家です。ユーザーの入力に基づいて、最適なツールを選択し、必要なパラメータを生成してください。
最適なツールが無い場合、直接回答を行ってください。

利用可能なツール:
{tools_description}

回答形式:
- ツールが必要な場合: "TOOL: ツール名" の後に、JSON形式でパラメータを出力
- ツールが不要な場合: "DIRECT: 直接回答" と出力

例:
- 入力: "5 と 3 を掛けて" → 出力: "TOOL: multiply\n{{"a": 5, "b": 3}}"
- 入力: "東京の天気は？" → 出力: "TOOL: get_weather\n{{"city": "東京"}}"
- 入力: "こんにちは" → 出力: "DIRECT: こんにちは！何かお手伝いできることはありますか？"

重要: パラメータは必ずJSON形式で出力し、必須パラメータは必ず含めてください。"""

    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # レスポンスを解析
        if response_text.startswith("TOOL:"):
            # ツール選択の場合
            lines = response_text.split('\n')
            tool_name = lines[0].replace("TOOL:", "").strip()
            
            if len(lines) > 1:
                try:
                    import json
                    parameters = json.loads(lines[1])
                    return tool_name, parameters
                except json.JSONDecodeError:
                    return None, None
            else:
                return None, None
                
        elif response_text.startswith("DIRECT:"):
            # 直接回答の場合
            direct_answer = response_text.replace("DIRECT:", "").strip()
            return "DIRECT", {"answer": direct_answer}
        else:
            return None, None
    
    except Exception as e:
        print(f"LLMツール選択エラー: {e}")
        return None, None

async def main():
    """メイン関数"""
    print("FastMCP Client - LLM完全統合版")
    print("サーバー: http://localhost:8001/mcp")
    print("終了するには 'quit' または 'exit' と入力してください\n")
    
    # LLM接続テスト
    print("LLM接続テスト中...")
    try:
        test_response = ask_llm("テスト", [])
        print("LLM接続成功!")
    except Exception as e:
        print(f"LLM接続エラー: {e}")
        print("LLM機能は利用できません。")
        return
    
    """
    ここから実際のMCPクライアント処理。
    クライアント側では、そこまでFastMCPの恩恵を受けない。
    クライアントの作成、ツールリストの取得、ツールの実行のみ。

    MCP Loop Observation→Thought→Action→Feedback と
    LLM呼び出しは、自前スクリプトで実装する。
    """

    # MCPクライアントのインスタンスを作成
    client = Client("http://localhost:8001/mcp")
    
    # async with コンテキストマネージャーを使用
    async with client:
        try:
            # サーバー接続テスト（兼ツール一覧取得）
            print("サーバーに接続中...")
            
            # 利用可能なツール一覧を取得
            # 接続テストを兼ねたいところだが、LLMの問題とFastMCPの問題を切り分ける為に、別記述とする。
            tools = await client.list_tools()
            if tools:
                print(f"接続成功! 利用可能なツール: {[tool.name for tool in tools]}")
                
                # ツールの詳細情報を表示
                print("\n=== 利用可能なツール詳細 ===")
                for tool in tools:
                    print(f"- {tool.name}: {tool.description}")
                    schema = getattr(tool, 'inputSchema', {})
                    if schema and 'properties' in schema:
                        print(f"  パラメータ: {list(schema['properties'].keys())}")
                    if schema and 'required' in schema:
                        print(f"  必須パラメータ: {schema['required']}")
                print()
            else:
                print("警告: サーバーに接続できませんでした。サーバーが起動しているか確認してください。")
                return
            
            # メインループ
            while True:
                try:
                    user_input = input("\nUser query: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', '終了']:
                        print("終了します。")
                        break
                    
                    if not user_input:
                        continue
                    
                    # LLMによるツール選択
                    print("\nLLMに問い合わせ中...")
                    tool_decision, parameters = ask_llm(user_input, tools)
                    
                    # デバッグ出力（本番では削除可能）
                    DEBUG = True  # デバッグフラグ
                    if DEBUG:
                        print("--------------------------------")
                        print(f"問い合せ結果: {tool_decision} パラメータ: {parameters}")
                        print("--------------------------------")

                    if tool_decision and tool_decision != "DIRECT":
                        # ツール選択の場合
                        # ツール名から実際のツールオブジェクトを取得
                        selected_tool = None
                        for tool in tools:
                            if tool.name == tool_decision:
                                selected_tool = tool
                                break
                        
                        if selected_tool:
                            try:
                                print(f"選択されたツール: {selected_tool.name}")
                                print(f"パラメータ: {parameters}")
                                
                                result = await client.call_tool(selected_tool.name, parameters)
                                
                                # 結果を適切に表示
                                if hasattr(result, 'data'):
                                    actual_result = result.data
                                else:
                                    actual_result = result
                                
                                param_str = ", ".join([f"{k}={v}" for k, v in parameters.items()])
                                print(f"結果: {selected_tool.name}({param_str}) = {actual_result}")

                                
                            except Exception as e:
                                print(f"ツール実行エラー: {e}")
                        else:
                            print(f"エラー: ツール '{tool_decision}' が見つかりません")

                    elif tool_decision == "DIRECT" and parameters and 'answer' in parameters:
                        # 直接回答の場合
                        print(f"回答: {parameters['answer']}")
                    
                    else:
                        # エラーまたは判断できない場合
                        print("申し訳ありませんが、適切な回答を生成できませんでした。")
                        print("利用可能なツール:")
                        for tool in tools:
                            print(f"- {tool.name}: {tool.description}")
                        print("\n例:")
                        print("- 掛け算: '5 と 3 を掛けて'")
                        print("- 割り算: '10 を 2 で割って'")
                        print("- 天気: '東京の天気は？'")
                
                except KeyboardInterrupt:
                    print("\n\n終了します。")
                    break
                except Exception as e:
                    print(f"エラーが発生しました: {e}")
        
        except Exception as e:
            print(f"クライアント初期化エラー: {e}")
            print("サーバーが起動しているか確認してください。")

if __name__ == "__main__":
    asyncio.run(main())