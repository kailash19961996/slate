# Add Memory (conversation history that “sticks”)

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL")

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

llm = ChatOpenAI(
    model=OPEN_AI_MODEL,
    api_key=OPENAI_API_KEY,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "keep your answers short"),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

chain = prompt | llm

store = {}

def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chat = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history"
)

session = {"configurable": {"session_id": "user-123"}}

print(chat.invoke({"input": "My name is bubloo."}, config=session).content)
print(chat.invoke({"input": "What’s my name?"},      config=session).content)