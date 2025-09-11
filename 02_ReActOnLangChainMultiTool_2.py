# agent_with_fallback.py
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory

# --- ツール定義 ---
def multiply(a: str, b: str) -> str:
    return str(int(a) * int(b))

def mock_weather(city: str) -> str:
    # モックの天気情報
    return f"{city}の天気は晴れ、気温30度、湿度60%です。"

tools = [
    Tool(
        name="Multiplier",
        func=lambda q: multiply(*q.split()),
        description="Multiply two numbers given as 'a b'"
    ),
    Tool(
        name="MockWeather",
        func=mock_weather,
        description="Return mock weather info for a given city"
    )
]

# --- LLM とメモリ ---
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# --- エージェント初期化 ---
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True,
)

# --- テスト ---
queries = [
    "2 3 を掛けて",
    "今の東京の天気は？",
    "人生、宇宙、すべての答えは？"
]

for q in queries:
    print(f">>> {q}")
    result = agent.invoke(q)
    # Observation や Thought を無視して LLMの回答だけを取得
    # LangChain 0.3系の場合、resultは dict ではなく str が返ることがある
    if hasattr(result, "content"):
        print(result.content)
    else:
        print(result)  # 直接文字列の場合
    print("-" * 40)
