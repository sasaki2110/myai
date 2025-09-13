# 05_mcpClient.py
# FastMCPを使用したMCPクライアント
# シンプルなツール呼び出しデモ

import asyncio
from fastmcp import Client

async def main():
    """メイン関数"""
    print("FastMCP Client - シンプルデモ")
    print("サーバー: http://localhost:8001")
    print("利用可能なツール: multiply, divide, get_weather")
    print("終了するには 'quit' または 'exit' と入力してください\n")
    
    # MCPクライアントのインスタンスを作成
    client = Client("http://localhost:8001/mcp")
    
    # async with コンテキストマネージャーを使用
    async with client:
        try:
            # サーバー接続テスト
            print("サーバーに接続中...")
            
            # 利用可能なツール一覧を取得
            tools = await client.list_tools()
            if tools:
                print(f"接続成功! 利用可能なツール: {[tool.name for tool in tools]}")
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
                    
                    # 簡単なルールベースでツールを選択
                    if any(keyword in user_input.lower() for keyword in ["掛けて", "かけて", "×", "multiply", "計算"]):
                        # 数値を抽出（簡易版）
                        numbers = []
                        for word in user_input.split():
                            try:
                                numbers.append(int(word))
                            except ValueError:
                                continue
                        
                        if len(numbers) >= 2:
                            result = await client.call_tool("multiply", {"a": numbers[0], "b": numbers[1]})
                            # 結果を適切に表示
                            if hasattr(result, 'data'):
                                print(f"結果: {numbers[0]} × {numbers[1]} = {result.data}")
                            else:
                                print(f"結果: {numbers[0]} × {numbers[1]} = {result}")
                        else:
                            print("掛け算に必要な数値が不足しています")
                    
                    elif any(keyword in user_input.lower() for keyword in ["割って", "割り算", "÷", "divide"]):
                        # 数値を抽出（簡易版）
                        numbers = []
                        for word in user_input.split():
                            try:
                                numbers.append(float(word))
                            except ValueError:
                                continue
                        
                        if len(numbers) >= 2:
                            try:
                                result = await client.call_tool("divide", {"a": numbers[0], "b": numbers[1]})
                                # 結果を適切に表示
                                if hasattr(result, 'data'):
                                    print(f"結果: {numbers[0]} ÷ {numbers[1]} = {result.data}")
                                else:
                                    print(f"結果: {numbers[0]} ÷ {numbers[1]} = {result}")
                            except Exception as e:
                                print(f"エラー: {e}")
                        else:
                            print("割り算に必要な数値が不足しています")
                    
                    elif any(keyword in user_input.lower() for keyword in ["天気", "weather", "気温", "温度"]):
                        # 都市名を抽出（簡易版）
                        cities = ["東京", "大阪", "名古屋", "福岡", "札幌", "横浜", "神戸", "京都"]
                        city = "東京"  # デフォルト
                        
                        for c in cities:
                            if c in user_input:
                                city = c
                                break
                        
                        result = await client.call_tool("get_weather", {"city": city})
                        # 結果を適切に表示
                        if hasattr(result, 'data'):
                            print(f"結果: {city}の天気: {result.data}")
                        else:
                            print(f"結果: {city}の天気: {result}")
                    
                    else:
                        print("対応していないクエリです。以下の形式で入力してください：")
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
