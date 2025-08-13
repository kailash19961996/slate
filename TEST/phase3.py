#Phase 3 — Tools + an Agent that chooses tools (function calling)


from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL")

# phase3_agent_tools.py
from datetime import datetime
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

# 1) Define tools
@tool
def add(a: float, b: float) -> float:
    """Return a+b."""
    return a + b

@tool
def now(tz: str = "UTC") -> str:
    """Return current time as ISO string (ignores tz here for demo)."""
    return datetime.utcnow().isoformat() + "Z"

tools = [add, now]

# 2) Model (enable function calling)
llm = ChatOpenAI(
    model=OPEN_AI_MODEL,
    api_key=OPENAI_API_KEY,
)

# 3) Prompt with chat history placeholder
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful agent. Use tools when needed. Be brief."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# 4) Build agent + executor
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5) Run a couple queries
history: list = []
def run(user_text: str):
    global history
    result = executor.invoke({"input": user_text, "chat_history": history})
    history += [("human", user_text), ("ai", result["output"])]
    print("AI:", result["output"])

run("What is 2.5 + 7.2?")
run("What time is it right now?")
