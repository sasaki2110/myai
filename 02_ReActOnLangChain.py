# 02_ReActOnLangChain.py
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

# 環境変数の読み込み
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# ツール定義
def multiply(a: str, b: str) -> str:
    return str(int(a) * int(b))

tools = [
    Tool(
        name="Multiplier",
        func=lambda q: multiply(*q.split()),
        description="Multiply two numbers given as 'a b'"
    )
]

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools,
    llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True,
)

print(agent.invoke("2 3 を掛けて"))
