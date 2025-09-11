# sample_agent.py
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory

# ---------------------------
# ツール定義
# ---------------------------

# 1. 乗算ツール
def multiply(a: str, b: str) -> str:
    return str(int(a) * int(b))

# 2. モック天気ツール
def mock_weather(location: str) -> str:
    # ここでは固定値で返す
    return f"{location}の天気は晴れ、気温30度、湿度60%です。"

tools = [
    Tool(
        name="Multiplier",
        func=lambda q: multiply(*q.split()),
        description="Multiply two numbers given as 'a b'"
    ),
    Tool(
        name="MockWeather",
        func=mock_weather,
        description="Return current weather of the given location (mocked data)"
    )
]

# ---------------------------
# LLM & Memory
# ---------------------------
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
#llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ---------------------------
# エージェント作成
# ---------------------------
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True,
)

# ---------------------------
# テスト呼び出し
# ---------------------------
queries = [
    "2 3 を掛けて",
    "今の東京の天気は？",
    "今の石川県金沢市の天気は？",
    "人生、宇宙、すべての答えは？"
]

for q in queries:
    print(">>>", q)
    try:
        result = agent.invoke(q)
        print(result.content)
    except Exception as e:
        print("Error:", e)
    print("-" * 40)
