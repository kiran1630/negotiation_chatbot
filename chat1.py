from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import uuid

# Your original code starts here

from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader


load_dotenv()

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
        print(product_details)
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
        
            if user accept or yes or confirm to buy then greet them saying thankyou for buying 
            if user  decline or not willing or no to price then greet them saying visit us again
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

# Your original code ends here

# Define FastAPI app
app = FastAPI()

# Input schema for API requests
class UserInput(BaseModel):
    input_message: str

# Initialize session and objects
session_id = str(uuid.uuid4())
extractor = ProductExtractor()
negotiator = NegotiationBot(session_id)
product_dict = None

# FastAPI endpoint that takes one input parameter 'input_message'
@app.post("/negotiate")
def negotiate(input_data: UserInput):
    global product_dict  # Keep the product details stored in memory for the session

    # Extract product details if not already extracted
    if not product_dict:
        try:
            product_dict = extractor.get_product_details(input_data.input_message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Handle negotiation
    try:
        output = negotiator.negotiate(product_dict, input_data.input_message)
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
