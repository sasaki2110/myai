# 05_mcpClient4.py
# FastMCP + mcp.json設定管理版
# 設定の外部化とエージェント抽象化を統合

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from fastmcp import Client
from openai import OpenAI
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from enum import Enum

# 環境変数を読み込み
load_dotenv()

# モデルごとの料金（1,000 tokens あたりのドル）
MODEL_RATES = {
    "gpt-5": {"input": 1.25, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
}

class UsageCostCalculator:
    def __init__(self, resp):
        self.resp = resp

        # モデル名を正規化（バージョン番号を削除）
        full_model_name = getattr(resp, "model", None) or resp.model
        self.model = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", full_model_name)

        # トークン数
        self.prompt_tokens = resp.usage.prompt_tokens
        self.completion_tokens = resp.usage.completion_tokens
        self.total_tokens = resp.usage.total_tokens

        # レート取得
        self.rates = MODEL_RATES.get(self.model)
        if self.rates is None:
            # デフォルトレート（gpt-4o-mini相当）
            self.rates = {"input": 0.15, "output": 0.60}
            print(f"⚠️  モデル '{self.model}' の料金情報が見つかりません。デフォルトレートを使用します。")

        # 1トークンあたりの料金計算
        self.input_rate_per_token = self.rates["input"] / 1000
        self.output_rate_per_token = (
            self.rates["output"] / 1000 if self.rates["output"] is not None else 0
        )

        # 利用量計算
        self.input_cost = self.prompt_tokens * self.input_rate_per_token
        self.output_cost = self.completion_tokens * self.output_rate_per_token
        self.total_cost = self.input_cost + self.output_cost

    def get_summary(self):
        """コスト情報のサマリーを返す"""
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost
        }

@dataclass
class SessionCostTracker:
    """セッション全体のコスト追跡"""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    model: str = ""

    def add_usage(self, cost_calc: UsageCostCalculator):
        """使用量を追加"""
        self.total_prompt_tokens += cost_calc.prompt_tokens
        self.total_completion_tokens += cost_calc.completion_tokens
        self.total_cost += cost_calc.total_cost
        self.request_count += 1
        if not self.model:
            self.model = cost_calc.model

    def get_session_summary(self):
        """セッション全体のサマリーを返す"""
        return {
            "model": self.model,
            "total_requests": self.request_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost": self.total_cost,
            "average_cost_per_request": self.total_cost / self.request_count if self.request_count > 0 else 0
        }

# 設定クラス
@dataclass
class MCPConfig:
    """MCP設定管理クラス"""
    
    def __init__(self, config_path: str = "mcp.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 設定ファイル読み込み完了: {self.config_path}")
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"設定ファイルのJSON形式が無効です: {e}")
        except Exception as e:
            raise RuntimeError(f"設定ファイル読み込みエラー: {e}")
    
    def get_server_config(self, server_name: str) -> Dict[str, Any]:
        """サーバー設定を取得"""
        servers = self.config.get("mcpServers", {})
        if server_name not in servers:
            raise KeyError(f"サーバー '{server_name}' が見つかりません")
        return servers[server_name]
    
    def get_client_config(self, client_name: str = "default") -> Dict[str, Any]:
        """クライアント設定を取得"""
        clients = self.config.get("clients", {})
        if client_name not in clients:
            raise KeyError(f"クライアント '{client_name}' が見つかりません")
        return clients[client_name]
    
    def get_llm_config(self) -> Dict[str, Any]:
        """LLM設定を取得"""
        return self.config.get("llm", {})
    
    def get_agent_config(self) -> Dict[str, Any]:
        """エージェント設定を取得"""
        return self.config.get("agent", {})
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """ツール設定を取得"""
        tools = self.config.get("tools", {})
        return tools.get(tool_name, {})
    
    def build_server_url(self, server_name: str) -> str:
        """サーバーURLを構築"""
        server_config = self.get_server_config(server_name)
        host = server_config.get("host", "localhost")
        port = server_config.get("port", 8001)
        path = server_config.get("path", "/mcp")
        return f"http://{host}:{port}{path}"

@dataclass
class LLMConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 500
    api_key: str = ""
    use_max_completion_tokens: bool = False
    use_temperature: bool = True

@dataclass
class AgentConfig:
    max_iterations: int = 5
    debug_mode: bool = True
    fallback_to_direct: bool = True
    timeout: int = 30

class ToolDecision(Enum):
    TOOL = "TOOL"
    DIRECT = "DIRECT"
    ERROR = "ERROR"

class ConfigurableMCPAgent:
    """設定可能なMCPエージェント"""
    
    def __init__(self, config_path: str = "mcp.json", server_name: str = "learning-server"):
        self.config_path = config_path
        self.server_name = server_name
        self.mcp_config: Optional[MCPConfig] = None
        self.llm_config: Optional[LLMConfig] = None
        self.agent_config: Optional[AgentConfig] = None
        self.client: Optional[Client] = None
        self.cost_tracker = SessionCostTracker()  # コスト追跡を追加
        self.tools: List[Any] = []
        self.llm_client: Optional[OpenAI] = None
        
    async def initialize(self) -> bool:
        """エージェントを初期化"""
        try:
            # 設定ファイル読み込み
            self.mcp_config = MCPConfig(self.config_path)
            
            # LLM設定の構築
            llm_config_data = self.mcp_config.get_llm_config()
            api_key = llm_config_data.get("apiKey", "")
            
            # 環境変数の読み込み処理
            if api_key.startswith("ENV:"):
                env_var_name = api_key[4:]  # "ENV:" を除去
                api_key = os.getenv(env_var_name)
                if not api_key:
                    raise ValueError(f"環境変数 '{env_var_name}' が設定されていません")
            elif not api_key:
                # フォールバック: 直接環境変数から取得
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI APIキーが設定されていません")
            
            # モデル別設定の取得
            model_name = llm_config_data.get("model", "gpt-4o-mini")
            model_settings = llm_config_data.get("modelSettings", {}).get(model_name, {})
            
            # トークン設定の決定
            if model_settings.get("useMaxCompletionTokens", False):
                max_tokens = model_settings.get("maxCompletionTokens", 500)
                use_max_completion_tokens = True
            else:
                max_tokens = model_settings.get("maxTokens", llm_config_data.get("maxTokens", 500))
                use_max_completion_tokens = False
            
            # 温度設定の決定
            if model_settings.get("useTemperature", True):
                temperature = model_settings.get("temperature", llm_config_data.get("temperature", 0.1))
                use_temperature = True
            else:
                temperature = 1.0  # デフォルト値
                use_temperature = False
            
            self.llm_config = LLMConfig(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                use_max_completion_tokens=use_max_completion_tokens,
                use_temperature=use_temperature
            )
            
            # エージェント設定の構築
            agent_config_data = self.mcp_config.get_agent_config()
            self.agent_config = AgentConfig(
                max_iterations=agent_config_data.get("maxIterations", 5),
                debug_mode=agent_config_data.get("debugMode", True),
                fallback_to_direct=agent_config_data.get("fallbackToDirect", True),
                timeout=agent_config_data.get("timeout", 30)
            )
            
            # LLMクライアントの初期化
            self.llm_client = OpenAI(api_key=self.llm_config.api_key)
            
            # サーバーURLの構築
            server_url = self.mcp_config.build_server_url(self.server_name)
            
            # MCPクライアントの初期化
            self.client = Client(server_url)
            await self.client.__aenter__()
            
            # ツール一覧の取得
            self.tools = await self.client.list_tools()
            
            print(f"✅ エージェント初期化完了")
            print(f"📁 設定ファイル: {self.config_path}")
            print(f"📡 サーバー: {server_url}")
            print(f"🤖 LLM: {self.llm_config.model}")
            print(f"🔧 利用可能ツール: {[tool.name for tool in self.tools]}")
            
            return True
            
        except Exception as e:
            print(f"❌ エージェント初期化エラー: {e}")
            return False
    
    async def cleanup(self):
        """リソースのクリーンアップ"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️ クリーンアップエラー: {e}")
    
    def _create_tools_schema(self) -> str:
        """利用可能なツールのスキーマ情報を生成"""
        tools_info = []
        for tool in self.tools:
            schema = getattr(tool, 'inputSchema', {})
            properties = schema.get('properties', {}) if schema else {}
            required = schema.get('required', []) if schema else {}
            
            # 設定ファイルからツール固有の情報を取得
            tool_config = self.mcp_config.get_tool_config(tool.name)
            description = tool_config.get("description", tool.description)
            
            tool_info = f"- {tool.name}: {description}"
            if properties:
                param_details = []
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'string')
                    is_required = param_name in required
                    param_details.append(f"{param_name}({param_type}{'必須' if is_required else '任意'})")
                tool_info += f" [パラメータ: {', '.join(param_details)}]"
            tools_info.append(tool_info)
        
        return "\n".join(tools_info)
    
    async def _ask_llm_for_decision(self, user_input: str) -> Tuple[ToolDecision, str, Dict[str, Any]]:
        """LLMにツール選択とパラメータ生成を依頼"""
        try:
            tools_schema = self._create_tools_schema()
            
            system_prompt = f"""あなたはツール選択の専門家です。ユーザーの入力に基づいて、最適なツールを選択し、必要なパラメータを生成してください。

利用可能なツール:
{tools_schema}

回答形式:
- ツールが必要な場合: "TOOL: ツール名" の後に、JSON形式でパラメータを出力
- ツールが不要な場合: "DIRECT: 具体的な回答内容" と出力

重要な指示:
1. ツール実行結果を受け取った場合は、その結果を基に最終回答を生成してください
2. DIRECT回答では、必ず具体的で有用な内容を提供してください
3. ツール結果の場合は、結果を自然な日本語で説明してください

例:
- 初回入力: "5 と 3 を掛けて" → 出力: "TOOL: multiply\n{{"a": 5, "b": 3}}"
- 初回入力: "東京の天気は？" → 出力: "TOOL: get_weather\n{{"city": "東京"}}"
- 初回入力: "こんにちは" → 出力: "DIRECT: こんにちは！何かお手伝いできることはありますか？"
- ツール結果後: "結果: get_weather(city=名古屋) = 雨、気温25度、湿度80%" → 出力: "DIRECT: 名古屋の天気は雨で、気温は25度、湿度は80%です。"
- ツール結果後: "結果: multiply(a=3, b=6) = 18" → 出力: "DIRECT: 3と6を掛けると18になります。"

重要: パラメータは必ずJSON形式で出力し、必須パラメータは必ず含めてください。"""

            # リクエストパラメータ
            request_params = {
                "model": self.llm_config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            }
            
            # モデル別の温度設定
            if self.llm_config.use_temperature:
                request_params["temperature"] = self.llm_config.temperature
            
            # モデル別のトークン設定
            if self.llm_config.use_max_completion_tokens:
                request_params["max_completion_tokens"] = self.llm_config.max_tokens
            else:
                request_params["max_tokens"] = self.llm_config.max_tokens
            
            response = self.llm_client.chat.completions.create(**request_params)
            
            # コスト追跡を追加
            try:
                cost_calc = UsageCostCalculator(response)
                self.cost_tracker.add_usage(cost_calc)
                if self.agent_config.debug_mode:
                    summary = cost_calc.get_summary()
                    print(f"💰 コスト: ${summary['total_cost']:.6f} (入力: {summary['prompt_tokens']}t, 出力: {summary['completion_tokens']}t)")
            except Exception as e:
                if self.agent_config.debug_mode:
                    print(f"⚠️  コスト計算エラー: {e}")
            
            response_text = response.choices[0].message.content.strip()
            
            # レスポンスを解析
            if response_text.startswith("TOOL:"):
                lines = response_text.split('\n')
                tool_name = lines[0].replace("TOOL:", "").strip()
                
                if len(lines) > 1:
                    try:
                        parameters = json.loads(lines[1])
                        return ToolDecision.TOOL, tool_name, parameters
                    except json.JSONDecodeError:
                        return ToolDecision.ERROR, "JSONパースエラー", {}
                else:
                    return ToolDecision.ERROR, "パラメータが不足", {}
                    
            elif response_text.startswith("DIRECT:"):
                direct_answer = response_text.replace("DIRECT:", "").strip()
                return ToolDecision.DIRECT, direct_answer, {}
            else:
                return ToolDecision.ERROR, "無効なレスポンス形式", {}
                
        except Exception as e:
            return ToolDecision.ERROR, f"LLM呼び出しエラー: {e}", {}
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str, Any]:
        """ツールを実行"""
        try:
            # ツールの存在確認
            selected_tool = None
            for tool in self.tools:
                if tool.name == tool_name:
                    selected_tool = tool
                    break
            
            if not selected_tool:
                return False, f"ツール '{tool_name}' が見つかりません", None
            
            # ツール実行
            result = await self.client.call_tool(tool_name, parameters)
            
            # 結果の処理
            if hasattr(result, 'data'):
                actual_result = result.data
            else:
                actual_result = result
            
            return True, "成功", actual_result
            
        except Exception as e:
            return False, f"ツール実行エラー: {e}", None
    
    def _format_tool_result(self, tool_name: str, parameters: Dict[str, Any], result: Any) -> str:
        """ツール結果の表示形式を生成"""
        param_str = ", ".join([f"{k}={v}" for k, v in parameters.items()])
        return f"結果: {tool_name}({param_str}) = {result}"
    
    async def process_query(self, user_input: str) -> str:
        """クエリを処理（MCP Loop実装）"""
        if self.agent_config.debug_mode:
            print(f"\n🔄 MCP Loop開始: {user_input}")
            print("=" * 50)
        
        observation = user_input
        max_iterations = self.agent_config.max_iterations
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if self.agent_config.debug_mode:
                print(f"\n--- Iteration {iteration} ---")
                print(f"Observation: {observation}")
            
            # --- Thought (LLM使用) ---
            if self.agent_config.debug_mode:
                print("\n--- Thought (LLM) ---")
            
            decision, tool_or_answer, parameters = await self._ask_llm_for_decision(observation)
            
            if self.agent_config.debug_mode:
                print(f"Decision: {decision.value}")
                print(f"Tool/Answer: {tool_or_answer}")
                print(f"Parameters: {parameters}")
            
            # --- Action ---
            if self.agent_config.debug_mode:
                print("\n--- Action ---")
            
            if decision == ToolDecision.TOOL:
                # ツール実行
                success, message, result = await self._execute_tool(tool_or_answer, parameters)
                
                if success:
                    action_output = self._format_tool_result(tool_or_answer, parameters, result)
                    if self.agent_config.debug_mode:
                        print(f"Action Result: {action_output}")
                else:
                    action_output = f"エラー: {message}"
                    if self.agent_config.debug_mode:
                        print(f"Action Error: {action_output}")
                
                # 次の反復のために観察を更新
                observation = action_output
                
            elif decision == ToolDecision.DIRECT:
                # 直接回答
                action_output = f"回答: {tool_or_answer}"
                if self.agent_config.debug_mode:
                    print(f"Action Result: {action_output}")
                
                # 最終回答として返す
                return action_output
                
            else:  # ToolDecision.ERROR
                # エラー処理
                if self.agent_config.fallback_to_direct:
                    action_output = f"エラー: {tool_or_answer}。直接回答を試行します。"
                    if self.agent_config.debug_mode:
                        print(f"Action Error: {action_output}")
                    
                    # フォールバック処理
                    try:
                        # フォールバック用のリクエストパラメータ
                        fallback_params = {
                            "model": self.llm_config.model,
                            "messages": [
                                {"role": "system", "content": "ユーザーの質問に直接回答してください。"},
                                {"role": "user", "content": user_input}
                            ]
                        }
                        
                        # モデル別の温度設定
                        if self.llm_config.use_temperature:
                            fallback_params["temperature"] = self.llm_config.temperature
                        
                        # モデル別のトークン設定
                        if self.llm_config.use_max_completion_tokens:
                            fallback_params["max_completion_tokens"] = self.llm_config.max_tokens
                        else:
                            fallback_params["max_tokens"] = self.llm_config.max_tokens
                        
                        fallback_response = self.llm_client.chat.completions.create(**fallback_params)
                        
                        # フォールバック処理のコスト追跡
                        try:
                            cost_calc = UsageCostCalculator(fallback_response)
                            self.cost_tracker.add_usage(cost_calc)
                            if self.agent_config.debug_mode:
                                summary = cost_calc.get_summary()
                                print(f"💰 フォールバックコスト: ${summary['total_cost']:.6f} (入力: {summary['prompt_tokens']}t, 出力: {summary['completion_tokens']}t)")
                        except Exception as e:
                            if self.agent_config.debug_mode:
                                print(f"⚠️  フォールバックコスト計算エラー: {e}")
                        
                        fallback_answer = fallback_response.choices[0].message.content.strip()
                        return f"回答: {fallback_answer}"
                    except Exception as e:
                        return f"申し訳ありませんが、適切な回答を生成できませんでした。エラー: {e}"
                else:
                    return f"エラー: {tool_or_answer}"
        
        # 最大反復回数に達した場合
        if self.agent_config.debug_mode:
            print(f"\n⚠️ 最大反復回数({max_iterations})に達しました")
        
        return "申し訳ありませんが、処理が完了しませんでした。時間を置いて再度お試しください。"

async def main():
    """メイン関数"""
    print("FastMCP Agent - 設定管理版 (mcp.json)")
    print("=" * 50)
    
    # エージェントの初期化
    agent = ConfigurableMCPAgent("mcp.json", "learning-server")
    
    try:
        # エージェント初期化
        if not await agent.initialize():
            print("❌ エージェントの初期化に失敗しました")
            return
        
        print("\n✅ エージェント準備完了！")
        print("終了するには 'quit' または 'exit' と入力してください\n")
        
        # メインループ
        while True:
            try:
                user_input = input("\nUser query: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '終了']:
                    # セッション終了時のコスト表示
                    print("\n" + "="*50)
                    print("📊 セッション終了")
                    print("="*50)
                    print(f"📁 設定ファイル: {agent.config_path}")
                    # サーバーURLを取得
                    server_url = "N/A"
                    if agent.mcp_config:
                        try:
                            server_config = agent.mcp_config.get_server_config(agent.server_name)
                            host = server_config.get("host", "localhost")
                            port = server_config.get("port", 8001)
                            path = server_config.get("path", "/mcp")
                            server_url = f"http://{host}:{port}{path}"
                        except:
                            server_url = "N/A"
                    print(f"📡 サーバー: {server_url}")
                    print(f"🤖 LLM: {agent.llm_config.model if agent.llm_config else 'N/A'}")
                    print(f"🔧 利用可能ツール: {[tool.name for tool in agent.tools] if agent.tools else 'N/A'}")
                    
                    # コスト情報を表示
                    if agent.cost_tracker.request_count > 0:
                        summary = agent.cost_tracker.get_session_summary()
                        print("\n💰 コスト情報")
                        print("-" * 30)
                        print(f"モデル: {summary['model']}")
                        print(f"リクエスト数: {summary['total_requests']}")
                        print(f"入力トークン: {summary['total_prompt_tokens']:,}")
                        print(f"出力トークン: {summary['total_completion_tokens']:,}")
                        print(f"総トークン数: {summary['total_tokens']:,}")
                        print(f"総コスト: ${summary['total_cost']:.6f}")
                        print(f"平均コスト/リクエスト: ${summary['average_cost_per_request']:.6f}")
                    else:
                        print("\n💰 コスト情報: リクエストなし")
                    
                    print("="*50)
                    print("👋 終了します。")
                    break
                
                if not user_input:
                    continue
                
                # クエリ処理
                result = await agent.process_query(user_input)
                print(f"\n{result}")
                
            except KeyboardInterrupt:
                print("\n\n👋 終了します。")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")
    
    finally:
        # クリーンアップ
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
