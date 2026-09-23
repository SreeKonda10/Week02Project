import os

import requests
import yfinance as yf
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

APPLE_10K_INDEX_NAME = "apple-10k"
_apple_10k_vectorstore = None


def _get_apple_10k_vectorstore() -> PineconeVectorStore:
    global _apple_10k_vectorstore
    if _apple_10k_vectorstore is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        _apple_10k_vectorstore = PineconeVectorStore(index_name=APPLE_10K_INDEX_NAME, embedding=embeddings)
    return _apple_10k_vectorstore


def get_stock_price(ticker: str) -> str:
    """Get the last closing stock price for a given ticker symbol, e.g. 'AAPL' or 'MSFT'."""
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info.get("lastPrice")
    except Exception:
        price = None

    if price is None:
        return f"Could not find a price for ticker '{ticker}'. It may be an invalid or delisted symbol."
    return f"The last price for {ticker.upper()} is ${price:.2f}."


def get_weather(city: str) -> str:
    """Get the current weather for a given city name, e.g. 'San Francisco'."""
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        return "OPENWEATHER_API_KEY is not set."

    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": api_key, "units": "metric"},
        timeout=10,
    )
    if response.status_code != 200:
        return f"Could not get weather for '{city}': {response.json().get('message', 'unknown error')}"

    data = response.json()
    description = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return f"The weather in {city} is {description} with a temperature of {temp}°C."


def search_apple_10k(query: str) -> str:
    """Search Apple's 10-K filings (FY2023-FY2025) for information about Apple's business,
    financials, risk factors, or other annual-report content.

    Args:
        query: What to look up, e.g. 'iPhone revenue trends' or 'supply chain risk factors'.
    """
    try:
        vectorstore = _get_apple_10k_vectorstore()
        results = vectorstore.similarity_search(query, k=4)
    except Exception as e:
        return f"Could not search the Apple 10-K index: {e}"

    if not results:
        return "No relevant information found in the Apple 10-K filings."

    passages = []
    for doc in results:
        fiscal_year = doc.metadata.get("fiscal_year", "unknown year")
        page_label = doc.metadata.get("page_label", doc.metadata.get("page", "unknown"))
        passages.append(f"[FY{fiscal_year}, page {page_label}] {doc.page_content}")
    return "\n\n---\n\n".join(passages)


agent = create_agent(
    model=ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none"),
    tools=[get_stock_price, get_weather, search_apple_10k],
    system_prompt=(
        "You are a helpful assistant with access to stock prices, weather information, "
        "and Apple's 10-K filings (FY2023-FY2025) for questions about Apple's business and financials."
    ),
    checkpointer=MemorySaver(),
)


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "cli-session"}}
    print("Chat with the agent (stock prices + weather). Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )
        print(f"Agent: {result['messages'][-1].content}\n")
