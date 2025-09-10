# langchain_react.py
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

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

llm = ChatOpenAI(model="gpt-4.1-mini")
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools,
    llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True,
)

print(agent.run("2 3 を掛けて"))
