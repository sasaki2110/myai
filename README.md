# 📘 学習コンテンツ：OpenAI APIを基盤とした ReAct / LangChain / Function Calling / MCP / FastMCP 再理解プラン

これは、順を踏んでMCPまでを理解するプラン（のはず）です。  

## ✅ 共通環境セットアップ

```bash
# Python仮想環境作成（例: venv）
python3 -m venv .venv
source .venv/bin/activate

# 必要パッケージ
pip install --upgrade pip
pip install openai langchain langchain-community anthropic mcp fastmcp aiohttp rich jupyter
```

#### 環境変数定義
```bash
export OPENAI_API_KEY="sk-xxxx..."
```

#### 後半のフェーズ２で、新たに指示される環境
```bash
# pip のアップデート
pip install --upgrade pip

# 必要パッケージをインストール
pip install --upgrade \
    langchain \
    langchain-openai \
    langchain-community \
    openai \
    requests \
    python-dotenv
```

#### なんか警告が出たから、削除して入れ直せと言われた。
```bash
# 古い LangChain をアンインストール
pip uninstall -y langchain langchain-core langchain-text-splitters

# 新しいパッケージをインストール
pip install --upgrade langchain langchain-openai langchain-community invoke
```

#### そして環境変数の定義方法を変えろと
```bash
cd ~/myai
echo "OPENAI_API_KEY=sk-xxxxxx" > .env
```

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

## 共通処理

- OpenAIからのレスポンスから、モデル名・トークン数を取得し、
  今回のセッション料金を計算。
cost_utils.py

## フェーズ0：OpenAI API基礎  

- OpenAI()を利用して、簡単にGPTを呼び出すサンプル  
00_baseOpenApi.py

- その回答を複数にする例  
00_baseOpenApiMultiChices.py

- Async 呼び出し例  
00_baseOpenApiAsync.py

- 新しい呼び出し例（client.responses.create）  
00_baseOpenApiNew.py

## フェーズ1：ReAct（手書き実装）  

- ReAct 疑似実行（１回のコールで全部実行）  
01_ReAct.py

- ReAct 疑似実行（試行、アクション、（観察）、回答　の流れを別々にコール）  
01_ReActStep.py

観察とはLLMの推論結果ではなく、外部（MCP等）から得られる情報。

## フェーズ1.5：ReAct（複数回LLM呼び出し）  

- LLM呼び出しを１回だけ  
01.5_ReAct_FunctionCall.py

- 複数回LLM呼び出し  
01.5_ReAct_Loop.py

## フェーズ2：LangChainでReAct  

- 掛け算ツールを呼び出す例  
02_ReActOnLangChain.py

- 掛け算ツールと、天気情報モックと、直接回答の例  
02_ReActOnLangChainMultiTool.py

- 直接回答でエラーが出ないように修正した版  
02_ReActOnLangChainMultiTool_2.py

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
