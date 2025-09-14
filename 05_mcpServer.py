# 05_mcpServer.py
# FastMCPを使用したMCPサーバー
# multiply, divide, get_weather ツールを提供

from fastmcp import FastMCP
import asyncio

# ツール関数を定義
async def multiply(a: int, b: int) -> int:
    """2つの数値を掛け算します。
    
    Args:
        a: 最初の数値
        b: 2番目の数値
    
    Returns:
        掛け算の結果
    """
    result = a * b
    print(f"multiply({a}, {b}) = {result}")
    return result

async def divide(a: float, b: float) -> float:
    """2つの数値を割り算します。
    
    Args:
        a: 被除数（割られる数）
        b: 除数（割る数）
    
    Returns:
        割り算の結果
    """
    if b == 0:
        raise ValueError("ゼロで割ることはできません")
    
    result = a / b
    print(f"divide({a}, {b}) = {result}")
    return result

async def get_weather(city: str) -> str:
    """指定された都市の天気情報を取得します。
    
    Args:
        city: 都市名
    
    Returns:
        天気情報の文字列
    """
    # モックの天気データ
    weather_data = {
        "東京": "晴れ、気温30度、湿度60%",
        "大阪": "曇り、気温28度、湿度70%",
        "名古屋": "雨、気温25度、湿度80%",
        "福岡": "晴れ、気温32度、湿度55%",
        "札幌": "曇り、気温22度、湿度65%"
    }
    
    result = weather_data.get(city, f"{city}の天気情報はありません")
    print(f"get_weather({city}) = {result}")
    return result

async def get_japan_pm() -> str:
    """現在の日本の首相を取得します。
    
    Returns:
        日本の首相に関する情報
    """
    
    return "石破茂（第103代） 就任日 2024年（令和6年）11月11日"

"""
ここから実際のMCPサーバー処理。
１．FastMCPサーバーのインスタンスを作成
２．ツールを登録
３．サーバーを起動
だけで、サーバーが起動する。
"""
# FastMCPサーバーのインスタンスを作成
mcp = FastMCP("LearningMCPServer")

# ツールを登録
mcp.tool(multiply)
mcp.tool(divide)
mcp.tool(get_weather)
mcp.tool(get_japan_pm)

if __name__ == "__main__":
    print("FastMCP Server starting...")
    print("Available tools: multiply, divide, get_weather, get_japan_pm")
    print("Server will run on http://0.0.0.0:8001")
    print("Press Ctrl+C to stop the server")
    
    # サーバーを起動（HTTPトランスポート）
    mcp.run(transport="http", host="0.0.0.0", port=8001, path="/mcp")
