from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

from langchain_core.messages import SystemMessage, HumanMessage


load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

response = llm.invoke([
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Explain decorators in Python.")
])

print(response.content)