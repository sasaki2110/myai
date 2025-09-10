# mcp_server.py
from mcp.server.fastmcp import FastMCP

app = FastMCP("WeatherServer")

@app.tool()
def get_weather(city: str) -> str:
    """都市の天気を返すダミー関数"""
    return f"{city} は晴れです"

if __name__ == "__main__":
    app.run()
