# 📘 学習コンテンツ：OpenAI APIを基盤とした ReAct / LangChain / Function Calling / MCP / FastMCP 再理解プラン

これは、順を踏んでMCPまでを理解するプラン（のはず）です。  

## ✅ 共通環境セットアップ

```python
# Python仮想環境作成（例: venv）
python3 -m venv .venv
source .venv/bin/activate

# 必要パッケージ
pip install --upgrade pip
pip install openai langchain langchain-community anthropic mcp fastmcp aiohttp rich jupyter
```

## フェーズ0：OpenAI API基礎  

## フェーズ1：ReAct（手書き実装）  

## フェーズ2：LangChainでReAct  

## フェーズ3：Function Calling  

## フェーズ4：MCP（Model Context Protocol）  

## フェーズ5：FastMCPで簡略化  

## ゴール整理  

- **ReAct**
思考 → 行動 → 観測 → 再思考 → 回答のフローを手作業で実装

- **LangChain**
上記フローをエージェントで簡単にラップ

- **Function Calling**
OpenAI標準の「関数呼び出し」方式を理解（ReActとの思想比較）

- **MCP**
Function Callingをプロトコル化した仕組みを体験

- **FastMCP**
MCPサーバー実装を最小限のコードで実現
