from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader

# Load environment variables from .env file
load_dotenv()

# FastAPI app initialization
app = FastAPI()

# Initialize the product extractor and negotiation bot
class ProductExtractor:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-70b-versatile")
        self.file_path = "ecom_items.csv"
        self.loader = CSVLoader(file_path=self.file_path)
        self.data = self.loader.load()
        self.prompt = PromptTemplate.from_template(
            """ from the {data} and the {query} identify the product asked by user in query and give the only name,original price, selling price, description from only data other than this nothing required no special chartacers in output  """
        )

    def get_product_details(self, query):
        res = self.llm.invoke(self.prompt.format(data=str(self.data), query=str(query)))
        product_details = str(res.content)
        product_dict = {}
        lines = product_details.split('\n')
        for line in lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                product_dict[key] = value
        return product_dict


class NegotiationBot:
    def __init__(self, session_id):
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-70b-versatile")
        self.prompt_extract = ChatPromptTemplate.from_messages(
            [
                ("system", """
            ### JOB DESCRIPTION: Give a response in two lines.
            You are a negotiation bot responsible for negotiating product prices with customers. You are provided with the following product information: {product}.
        
            if user accept or yes or confirm to buy then greet them saying thank you for buying 
            if user decline or not willing or no to price then greet them saying visit us again
            give response in two lines
            """),
                ("human", "{input_messages}"),
            ]
        )
        self.store = {}
        self.config = {"configurable": {"session_id": session_id}}

    def get_session_history(self, session_id):
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        else:
            self.store[session_id].clear()
        return self.store[session_id]

    def negotiate(self, product_dict, input_messages):
        chain = self.prompt_extract | self.llm
        conversation = RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=self.get_session_history,
            input_messages_key="input_messages",
            output_messages_key="output",
            history_messages_key="history"
        )
        
        output = conversation.invoke(
            input={
                'input_messages': input_messages,
                'product': list(product_dict.items())
            },
            config=self.config
        )

        return output.content


# FastAPI Request models
class ProductQuery(BaseModel):
    query: str

class NegotiationInput(BaseModel):
    input_messages: str
    session_id: str


# API Endpoints
@app.get("/")
async def root():
    return {"message": "Negotiation Bot API is running."}


@app.post("/start-negotiation")
async def start_negotiation(query: ProductQuery):
    extractor = ProductExtractor()
    try:
        product_dict = extractor.get_product_details(query.query)
        if not product_dict:
            raise HTTPException(status_code=404, detail="Product not found.")
        return {"product_details": product_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/negotiate")
async def negotiate(input: NegotiationInput):
    try:
        session_id = input.session_id or str(uuid.uuid4())
        negotiator = NegotiationBot(session_id)
        product_dict = {}  # You'll need to pass the actual product details here
        response = negotiator.negotiate(product_dict, input.input_messages)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# To run the app, use:
# uvicorn app:app --reload
