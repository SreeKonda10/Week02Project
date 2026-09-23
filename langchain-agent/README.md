# LangChain Agent — Stock Price + Weather + Apple 10-K Search

A LangChain agent with three tools:

1. **`get_stock_price`** — last closing price for a ticker, via `yfinance` (no API key needed)
2. **`get_weather`** — current weather for a city, via the OpenWeatherMap API (needs `OPENWEATHER_API_KEY`)
3. **`search_apple_10k`** — semantic search over Apple's FY2023-FY2025 10-K filings, via a Pinecone vector store (needs `PINECONE_API_KEY`)

## Setup

Requires Python 3.11 (Python 3.14 currently breaks `langchain-pinecone`'s dependencies).

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your OPENAI_API_KEY, OPENWEATHER_API_KEY, and PINECONE_API_KEY
```

Get keys at:
- OpenAI: https://platform.openai.com/api-keys
- OpenWeatherMap: https://openweathermap.org/api (free tier available)
- Pinecone: https://www.pinecone.io (free tier available)

## Build the Apple 10-K index (one-time)

Before `search_apple_10k` works, fetch Apple's 10-Ks and load them into Pinecone:

```bash
python build_apple_10k_index.py
```

This creates a serverless Pinecone index named `apple-10k` (AWS us-east-1) and embeds FY2023-FY2025 filing text into it. Re-run it any time you want to refresh the index (e.g. once a new fiscal year's 10-K is filed).

**Chunking is page-based**: each 10-K is fetched as a PDF from Apple's investor relations site (not SEC EDGAR's HTML, which has no real page concept), and each PDF page becomes exactly one chunk — no further splitting. This means chunk boundaries match the actual document's printed pages, at the cost of inconsistent chunk sizes (a dense table page vs. a sparse section-header page embed very differently).

## Run

```bash
python agent.py
```
