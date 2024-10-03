from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
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
            """From the {data} and the {query}, identify the product asked by the user in the query and provide only the name, original price, selling price, and description. No special characters in output."""
        )

    def get_product_details(self, query):
        res = self.llm.invoke(self.prompt.format(data=str(self.data), query=str(query)))
        product_details = str(res.content)
        product_dict = {}
        lines = product_details.split('\n')
        for line in lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                product_dict[key.strip()] = value.strip()
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
                    - If the customer proposes a price more than 30% below the selling price, present product features to convince them.
                    - If the proposed price is within 7% of the selling price, accept the offer.
                    - If the proposed price is within 10% of the original price (without going below it), accept it.
                """),
                ("human", "{input_messages}"),
            ]
        )
        self.store = {}
        self.config = {"configurable": {"session_id": session_id}}

    def get_session_history(self, session_id):
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        return self.store[session_id]

    def negotiate(self, product_dict, input_messages):
        original_price = float(product_dict['Original Price'])
        selling_price = float(product_dict['Selling Price'])
        proposed_price = float(input_messages.split()[-1])  # Assuming last input is the price
        
        max_discount_price = selling_price - (selling_price * 0.09)  # Max price with 11% discount
        acceptance_threshold_7_percent = selling_price * 0.95  # 7% less than selling price
        acceptance_threshold_10_percent = original_price   # 10% less than original price

        # Determine response
        if proposed_price < max_discount_price:
            response = " However, I can only offer a maximum discount of 11%."
            response += f" The maximum price I can offer is around {max_discount_price:.2f}."
            response += f" Here are the features of the microwave oven: {product_dict['Description']}"
        elif proposed_price <= acceptance_threshold_7_percent:
            response = "Thank you for your offer! I can accept that price."
        elif proposed_price <= original_price:
            response = "Thank you! That price works for me."
        else:
            response = f"I'm sorry, but I can't go above the original price of {original_price:.2f}."

        return response

session_id = str(uuid.uuid4())  # Create a new session ID for each negotiation
product_dict = None  # Reset product_dict for the new session
extractor = ProductExtractor()  # Create a new instance of ProductExtractor
negotiator = NegotiationBot(session_id)

# Main loop
while True:
      # Create a new instance of NegotiationBot

    input_messages = input('user: ')
    if input_messages.lower() == 'quit':
        break

    if not product_dict:
        query = input_messages
        product_dict = extractor.get_product_details(query)
        print(product_dict)

    output = negotiator.negotiate(product_dict, input_messages)
    print(output)
