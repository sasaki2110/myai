# 04_mcpServer.py
# FastAPIを使用した低レベルMCPサーバー実装
# multiply と get_weather をツールとして提供

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any, List

# FastAPIアプリケーションを作成
app = FastAPI(title="MCP Learning Server")

# --- ツール関数 ---
def multiply(a: int, b: int) -> int:
    """
    2つの数値を掛け算します。
    
    Args:
        a: 最初の数値
        b: 2番目の数値
    
    Returns:
        掛け算の結果
    """
    result = a * b
    print(f"multiply({a}, {b}) = {result}")
    return result

def get_weather(city: str) -> str:
    """
    指定された都市の天気情報を取得します。
    
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

# ツール一覧を取得するエンドポイント
@app.get("/tools")
async def get_tools():
    """利用可能なツール一覧を取得"""
    tools = [
        {
            "name": "multiply",
            "description": "2つの数値を掛け算します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "最初の数値"},
                    "b": {"type": "integer", "description": "2番目の数値"}
                },
                "required": ["a", "b"]
            }
        },
        {
            "name": "get_weather",
            "description": "指定された都市の天気情報を取得します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "都市名"}
                },
                "required": ["city"]
            }
        }
    ]
    return tools

# ツール呼び出しのリクエストボディのPydanticモデル
class ToolCallRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]

# ツールを呼び出すエンドポイント
@app.post("/call")
async def call_tool(request: ToolCallRequest):
    """ツールを呼び出し"""
    tool_name = request.tool
    parameters = request.parameters
    
    if tool_name == "multiply":
        a = parameters.get("a")
        b = parameters.get("b")
        if a is None or b is None:
            return {"error": "Parameters 'a' and 'b' are required for multiply"}
        result = multiply(a, b)
    elif tool_name == "get_weather":
        city = parameters.get("city")
        if city is None:
            return {"error": "Parameter 'city' is required for get_weather"}
        result = get_weather(city)
    else:
        return {"error": f"Tool '{tool_name}' not found"}
    
    return {"result": result}

if __name__ == "__main__":
    print("MCP Server starting on port 8001...")
    print("Available tools: multiply, get_weather")
    print("Press Ctrl+C to stop the server")
    
    # サーバーを起動
    uvicorn.run(app, host="0.0.0.0", port=8001)