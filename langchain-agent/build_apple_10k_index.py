"""Build the Apple 10-K vector store.

One-time (or refresh-on-demand) script: fetches Apple's FY2023-FY2025 10-K
filings as PDFs from Apple's investor relations site, chunks them BY PAGE
(one chunk = one PDF page, no further splitting), embeds with OpenAI, and
upserts into a Pinecone serverless index named "apple-10k". Run this before
using the search_apple_10k tool in agent.py -- the agent only *queries* this
index at runtime, it doesn't build it.

Usage:
    python build_apple_10k_index.py
"""

import os
import time

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

INDEX_NAME = "apple-10k"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# PDF URLs from Apple's investor relations site. NOTE: Apple's URL pattern
# is NOT consistent year to year (host, path, and filename all vary) -- if
# adding a new fiscal year, search "investor.apple.com doc_earnings <year>
# 10-K As-Filed.pdf" to find the actual filename rather than guessing it.
FILINGS = {
    2025: "https://s2.q4cdn.com/470004039/files/doc_financials/2025/ar/_10-K-2025-As-Filed.pdf",
    2024: "https://investor.apple.com/files/doc_earnings/2024/q4/filing/10-Q4-2024-As-Filed.pdf",
    2023: "https://investor.apple.com/files/doc_earnings/2023/q4/filing/_10-K-Q4-2023-As-Filed.pdf",
}

# Apple's investor relations site rejects requests without a browser-like User-Agent.
PDF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def build_page_chunks() -> list[Document]:
    """One chunk per PDF page, tagged with fiscal year and page number."""
    chunks: list[Document] = []
    for fiscal_year, url in FILINGS.items():
        print(f"Fetching FY{fiscal_year} 10-K PDF ...")
        loader = PyPDFLoader(url, headers=PDF_HEADERS)
        pages = loader.load()
        print(f"  -> {len(pages)} pages")
        for page in pages:
            page.metadata["fiscal_year"] = fiscal_year
            page.metadata["source"] = url
        chunks.extend(pages)
        time.sleep(0.5)  # be polite to the server
    return chunks


def ensure_index(pc: Pinecone) -> None:
    existing_names = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME in existing_names:
        print(f"Index '{INDEX_NAME}' already exists, reusing it.")
        return

    print(f"Creating Pinecone index '{INDEX_NAME}' ...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(INDEX_NAME).status["ready"]:
        time.sleep(1)


def main() -> None:
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise SystemExit("PINECONE_API_KEY is not set. Add it to .env first.")

    pc = Pinecone(api_key=pinecone_api_key)
    ensure_index(pc)

    chunks = build_page_chunks()
    print(f"Embedding and upserting {len(chunks)} page-chunks into Pinecone ...")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    PineconeVectorStore.from_documents(chunks, embeddings, index_name=INDEX_NAME)

    print("Done. The 'apple-10k' index is ready to query.")


if __name__ == "__main__":
    main()
