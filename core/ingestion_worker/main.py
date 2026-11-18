import os
import sys
from dotenv import load_dotenv
from sources import HistoricalEdgarFetcher

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
    print("Loading environment variables...")
    # This automatically finds and loads the .env file
    load_dotenv()

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
    documents = []

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

        print(f"\nTotal documents fetched: {len(documents)}")
        print(f"Total payload size: {sum(len(s.encode('utf-8')) for doc in documents for s in doc.sentences) / (1024 * 1024):.2f} MB")
        print("\nDocument Preview (First 4):")
        for i, doc in enumerate(documents[:4], start=1):
            print(f"{i:>3}. Title: {doc.title}\n")
            print(f"   Content: {doc.sentences[0]}\n")
            print(f"   Publish Date: {doc.publish_date.strftime('%Y-%m-%d')}\n")
            print(f"   Description: {doc.description}\n")
            print(f"   Ticker:      {doc.ticker_symbol}\n")
            print(f"   Type:        {doc.document_type}\n")
            print(f"   Publisher:   {doc.publisher}\n")
            print(f"   Source URL:  {doc.source_url}\n")
            print("" + "-" * 80 + "\n")

    except Exception as e:
        print(f"❌ An error occurred during the fetching process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
