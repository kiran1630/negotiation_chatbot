from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
# os.environ['GROQ_API_KEY'] = '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'
load_dotenv()


llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-70b-versatile")

prompt_extract = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a interactive  negotiater chatbot give responce in one line  "),
        ("human", "{input}"),
    ]
)
chain = prompt_extract |llm



store = {}

config = {"configurable": {"session_id": "abc123"}}

def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
)


while True:
    input_messages = input('user: ')
    if input_messages == 'quit':
        break
    output = conversation.invoke(input_messages, config)
    print(output.content)