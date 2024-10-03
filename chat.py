from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader
import uuid


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
        # res = self.llm.invoke({'input': self.prompt.format(data=str(self.data), query=str(query))})
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

            ### INSTRUCTION:
            Your goal is to offer some discounts and counteroffers based on customer input while ensuring a reasonable price range. Follow this negotiation instruction:

            3. **Price Boundaries**:
            - The minimum price you can offer is the **original price** ({{original_price}}).
            - All discounts must stay between the original price and the selling price, with a maximum discount of 11%.

            4. **Persuasion**:
            - If the customer proposes a price more than 7% below the current price, present product features to convince them.
            - If the proposed price is within 3% of the current price, accept the offer.
            - If the proposed price is within 10% of the original price, accept it, ensuring it doesn't go below the original price.
            give response in two lines
            5. **Closure**: If the customer accepts the offer within this range, confirm the sale  greet them for buying or If the customer declines, greet them like thank you for visiting.
            
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
        # conversation = RunnableWithMessageHistory(
        #     chain, 
        #     self.get_session_history
           
        # )
        conversation = RunnableWithMessageHistory(
        runnable=chain,  # Chain needs to be passed as a 'runnable'
        get_session_history=self.get_session_history,  # This is passed as a keyword argument
        input_messages_key="input_messages",  # Define the key for input messages
        output_messages_key="output",  # Define the key for output messages
        history_messages_key="history"  # Define the key for history if needed
    )
        
        output = conversation.invoke(
    input={
        'input_messages': input_messages,

        'product' : list(product_dict.items())
    },
    config=self.config
)

        return output.content


# Main loop


while True:
    session_id = str(uuid.uuid4())
    product_dict = None
    extractor = ProductExtractor()
    negotiator = NegotiationBot(session_id)
    input_messages = input('user: ')
    if input_messages == 'quit':
        break
    if not product_dict:
        query = input_messages
        product_dict = extractor.get_product_details(query)
        print(product_dict)
    
    output = negotiator.negotiate(product_dict, input_messages)
    print(output)
