import os
import sys
from dotenv import load_dotenv
import spacy
from tqdm import tqdm
from sources import HistoricalEdgarFetcher
from schemas import FinancialDocument

TARGET_COMPANIES = [
    ("AAPL", "320193"),    # Apple Inc.
    ("MSFT", "789019"),    # Microsoft Corp.
    ("GOOGL", "1652044"),  # Alphabet Inc.
    ("AMZN", "1018724"),   # Amazon.com Inc.
    ("NVDA", "1045810"),   # NVIDIA Corp.
    ("TSLA", "1318605"),   # Tesla Inc.
    ("META", "1326801"),   # Meta Platforms Inc.
    ("WMT", "104169"),     # Walmart Inc.
    ("JPM", "19617"),      # JPMorgan Chase & Co.
    ("PANW", "1327567"),   # Palo Alto Networks Inc.
]

def main():
    if spacy.prefer_gpu():
        print("GPU is available and will be used by spaCy.")
    else:
        print("GPU not available or not preferred by spaCy. Falling back to CPU.")

    print("Loading environment variables...")
    # This automatically finds and loads the .env file
    load_dotenv()
    nlp = spacy.load("en_core_web_sm")

    # Retrieve the variables safely
    app_name = os.getenv("APP_NAME", "DefaultRAGProject/1.0")
    contact_email = os.getenv("SEC_CONTACT_EMAIL")

    if not contact_email:
        print("❌ Error: SEC_CONTACT_EMAIL is missing from the .env file.")
        sys.exit(1)

    user_agent = f"{app_name} ({contact_email})"

    print(f"Initializing SEC Edgar Fetcher with User-Agent: {user_agent}")
    edgar_fetcher = HistoricalEdgarFetcher(user_agent=user_agent)

    fetchers = [edgar_fetcher]
    documents: list[FinancialDocument] = []
    tokens: list[spacy.language.Doc] = []

    try:
        print("\nStarting data fetch for target companies...")

        for fetcher in fetchers:
            print(f"\nUsing fetcher: {fetcher.__class__.__name__}")
            for ticker, cik in TARGET_COMPANIES:
                try:
                    fetched_docs = fetcher.fetch(ticker=ticker, cik=cik)
                    documents.extend(fetched_docs)
                except Exception as e:
                    print(f"❌ An error occurred while fetching data: {e}")
                    print(f"Skipping {ticker} due to the error.")

        content_size = sum(len(doc.content) for doc in documents)
        print(f"\nFetched {len(documents)} documents with a total content size of {content_size / (1024 * 1024):.2f} MB.")

        for doc in tqdm(documents, desc="Tokenizing documents"):
            next_tokens = nlp(doc.content)
            tokens.append(next_tokens)

        print(tokens[0].ents[0].text)
        print(tokens[0].ents[0].sent.text)

    except Exception as e:
        print(f"❌ An error occurred during the fetching process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
