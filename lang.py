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


llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-70b-versatile")


file_path = ("ecom_items.csv")

loader = CSVLoader(file_path=file_path)
data = loader.load()

prompt = PromptTemplate.from_template(
    """ from the {data} and the {query}  identify the product asked by user and give the only name,original price ,selling price ,description other than this nothing requireed """
)




prompt_extract = ChatPromptTemplate.from_messages(
    [
        ("system","""
                   

                ### JOB DESCRIPTION:
                You are a negotiation bot responsible for negotiating product prices with customers. You are provided with the following information for each product:  

                - Product Name: {{name}}  
                - Original Price: {{original_price}}  
                - Selling Price: {{selling_price}}  
                - Product Description: {{description}}

                ### INSTRUCTION:
                You are a highly skilled negotiation bot whose primary responsibility is to negotiate the best price for both the customer and the business. Your goal is to offer fair discounts and counteroffers while maintaining a reasonable price range. Use the following negotiation logic:

                1. **Initial Offer**: Start by offering a **5% discount** off the selling price ({{selling_price}}).
                2. **Further Negotiation**: If the customer insists on a lower price, gradually offer higher discounts:
                - Second offer: 10% off the selling price.
                - Third offer: 15% off the selling price.
                - Final offer: 20%–25% off the selling price.
                
                3. **Price Boundaries**: You cannot offer a price lower than the original price ({{original_price}}). Ensure that all discounts stay between the original price and selling price, with the maximum discount capped at 25%.

                4. **Persuasion**: Justify your offers by highlighting the quality and features of the product using the product description. Emphasize that the original price is a strict boundary to ensure profitability and quality service.

                5. **Closure**: If the customer accepts the offer within this range, confirm the sale. If the customer declines, offer alternatives or explain why no further discounts are possible.

                ### RESPONSE (NO PREAMBLE):


""" ),
        ("human", "{input_messages}"),
    ]
)
chain = prompt_extract |llm
 chain = prompt |llm
query ='what is price of wasing machine'
res = chain.invoke(input={'data':str(data),'query':str(query)})
product_details = str(res.content)
product_dict = {}

# Split the string by lines
lines = product_details.split('\n')

# Parse each line to extract key-value pairs
for line in lines:
    key, value = line.split(': ', 1)
    product_dict[key] = value


store = {}

config = {"configurable": {"session_id": "abc123" }}

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


   
 
    output = conversation.invoke(input={'input_messages':input_messages,'name':product_dict['Item'],'original_price':product_dict['Original_Price'],'selling_price':product_dict['Selling_Price'],'description':product_dict['Description']}, config)
     
    print(output.content)