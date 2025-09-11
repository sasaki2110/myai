#
# コスト（トークン利用量×レート=料金）計算ユーティリティ
#

# cost_utils.py
import re

# モデルごとの料金（1,000 tokens あたりのドル）
MODEL_RATES = {
    "gpt-5": {"input": 1.25, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
    "gpt-5-chat-latest": {"input": 1.25, "output": 10.00},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-realtime": {"input": 4.00, "output": 16.00},
    "gpt-4o-realtime-preview": {"input": 5.00, "output": 20.00},
    "gpt-4o-mini-realtime-preview": {"input": 0.60, "output": 2.40},
    "gpt-audio": {"input": 2.50, "output": 10.00},
    "gpt-4o-audio-preview": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini-audio-preview": {"input": 0.15, "output": 0.60},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-pro": {"input": 150.00, "output": 600.00},
    "o3-pro": {"input": 20.00, "output": 80.00},
    "o3": {"input": 2.00, "output": 8.00},
    "o3-deep-research": {"input": 10.00, "output": 40.00},
    "o4-mini": {"input": 1.10, "output": 4.40},
    "o4-mini-deep-research": {"input": 2.00, "output": 8.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o1-mini": {"input": 1.10, "output": 4.40},
    "codex-mini-latest": {"input": 1.50, "output": 6.00},
    "gpt-4o-mini-search-preview": {"input": 0.15, "output": 0.60},
    "gpt-4o-search-preview": {"input": 2.50, "output": 10.00},
    "computer-use-preview": {"input": 3.00, "output": 12.00},
    "gpt-image-1": {"input": 5.00, "output": None},
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
            raise ValueError(f"モデル '{self.model}' の料金情報が見つかりません")

        # 1トークンあたりの料金計算
        self.input_rate_per_token = self.rates["input"] / 1000
        self.output_rate_per_token = (
            self.rates["output"] / 1000 if self.rates["output"] is not None else 0
        )

        # 利用量計算
        self.input_cost = self.prompt_tokens * self.input_rate_per_token
        self.output_cost = self.completion_tokens * self.output_rate_per_token
        self.total_cost = self.input_cost + self.output_cost

    # レポート表示
    def report(self):
        print("=== Usage Report ===")
        print(f"Model: {self.model}")
        print(f"Prompt tokens: {self.prompt_tokens}  | Rate: ${self.input_rate_per_token:.6f}/token | Cost: ${self.input_cost:.6f}")
        print(f"Completion tokens: {self.completion_tokens}  | Rate: ${self.output_rate_per_token:.6f}/token | Cost: ${self.output_cost:.6f}")
        print(f"Total tokens: {self.total_tokens}")
        print(f"Total cost:  ${self.total_cost:.6f}")
