
# Negotiation Chatbot API

Welcome to the **Negotiation Chatbot API**! This bot helps customers negotiate prices on products. It provides discounts, counteroffers, and handles multiple items while ensuring profitability for the business.

## Features
- **Product Negotiation:** Helps users negotiate product prices.
- **Random Product Display:** Showcases random products and prices for users.
- **FastAPI Integration:** Leverages FastAPI to provide API endpoints.
- **Chain of Negotiation Logic:** Uses Groq's large language model (LLM) to process and respond to negotiations.

## Tech Stack
- **FastAPI**: For creating the web API.
- **LangChain and Groq API**: LLM-powered negotiation bot logic.
- **Pandas and CSVLoader**: For handling product data from CSV.
- **Uvicorn**: ASGI server for serving the FastAPI app.

## Setup Instructions

### Prerequisites
- **Python 3.8+**
- **FastAPI**  (`pip install fastapi`)
- **Uvicorn**  (`pip install uvicorn`)
- **LangChain**, **Groq API**, and **Pandas** libraries installed
  ```bash
  pip install fastapi uvicorn langchain pandas python-dotenv tabulate
![Example Image](IMAGE/flow chart.png)

