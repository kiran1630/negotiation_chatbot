from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import uuid
from fastapi.responses import PlainTextResponse
from negotiation import ProductExtractor, NegotiationBot, DisplayItems

# Initialize the display object
display_items = DisplayItems()

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

@app.get("/", response_class=PlainTextResponse)
def display_random_items():
    greeting = "Hello! I am your friendly negotiation bot. I can help you find great deals on products.\n"
    bot_details = "I specialize in negotiating product prices and offering discounts. Here are some random products you might like:\n"
    
    # Instructions to use FastAPI Swagger UI
    swagger_instructions = (
        "\n\n"
        "***************\n"
        "IMPORTANT: USE FASTAPI SWAGGER UI TO CHAT WITH ME!\n"
        "***************\n\n"
        "To interact with the bot, please follow these steps:\n"
        "1. Open your browser and go to: http://127.0.0.1:8000/docs\n"
        "2. You will see the FastAPI Swagger UI.\n"
        "3. Look for the `/negotiate` POST endpoint.\n"
        "4. Click 'Try it out' to test the negotiation chatbot.\n"
        "5. Enter your message in the 'input_message' field and press 'Execute'.\n"
    )

    # Get the formatted table of random items
    table = display_items.get_table()
    response_message = greeting + bot_details + "\n" + table + swagger_instructions

    return response_message

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
