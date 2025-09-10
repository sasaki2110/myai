# mcp_client.py
import asyncio
from mcp.client.fastmcp import MCPClient

async def main():
    async with MCPClient("WeatherClient") as client:
        result = await client.call("get_weather", city="東京")
        print("結果:", result)

asyncio.run(main())
