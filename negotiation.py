from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader
import pandas as pd
from tabulate import tabulate

load_dotenv()

# Product Extractor Class
class ProductExtractor:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-70b-versatile")
        self.file_path = "ecom_items.csv"
        self.loader = CSVLoader(file_path=self.file_path)
        self.data = self.loader.load()
        self.prompt = PromptTemplate.from_template(
            """ from the {data} and the {query} identify the product asked by user in query and give the only name,original price, selling price, description from only data other than this nothing required no special characters in output  """
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



# NegotiationBot Class
class NegotiationBot:
    def __init__(self, session_id):
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-8b-instant")
        self.prompt_extract = ChatPromptTemplate.from_messages(
            [
                ("system", """
    You are a negotiation bot responsible for negotiating product prices with customers. Your goal is to reach a mutually beneficial agreement on the price of the product.

    Product Information: {product}
    from the product remember orginal and selling price 

    
    - If the customer accepts the price, confirm the purchase and express excitement.
    - If the customer declines, thank them for considering the product and express hope for future interaction.
    
    response must me two or three line proper english sentence 
    
             
    give responce in two line 
    
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

# DisplayItems Class
class DisplayItems:
    def __init__(self) -> None:
        df = pd.read_csv('ecom_items.csv')
        self.random_items = df[['Item', 'Selling_Price']].sample(n=15)

    def get_table(self):
        return tabulate(self.random_items, headers='keys', tablefmt='grid', showindex=False)
