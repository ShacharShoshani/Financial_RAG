import os
import sys
from dotenv import load_dotenv
from sources import HistoricalEdgarFetcher


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
    fetcher = HistoricalEdgarFetcher(user_agent=user_agent)

    ticker = "AAPL"
    apple_cik = "320193"

    print(f"\nRequesting historical facts for {ticker} (CIK: {apple_cik})...")

    try:
        documents = fetcher.fetch(ticker=ticker, cik=apple_cik)

        if not documents:
            print(f"No documents returned for {ticker}.")
            sys.exit(1)

        print("\n" + "=" * 40)
        print("✅ FETCH SUCCESSFUL")
        print("=" * 40)
        print(f"Ticker:        {ticker}")
        print(f"Source URL:    {documents[0].source_url}")
        print(f"Documents:     {len(documents):,}")

        preview_count = 4
        print(f"\n--- Document Preview (First {preview_count}) ---\n")
        for i, doc in enumerate(documents[:preview_count], start=1):
            print(f"{i:>3}. Title: {doc.title}\n")
            print(f"  Content: {doc.sentences[0]}\n")
            print(f"  Publish Date: {doc.publish_date.strftime('%Y-%m-%d')}\n")
            print(f"  Description: {doc.description}\n")
            print(f"  Ticker:      {doc.ticker_symbol}\n")
            print(f"  Type:        {doc.document_type}\n")
            print(f"  Publisher:   {doc.publisher}\n")
            print(f"  Source URL:  {doc.source_url}\n")
            print("-" * 38 + "\n")
        if len(documents) > preview_count:
            print(f"     ... and {len(documents) - preview_count:,} more")
        print("-" * 38 + "\n")

        payload_bytes = sum(
            len(s.encode("utf-8")) for doc in documents for s in doc.sentences
        )
        payload_mb = payload_bytes / (1024 * 1024)
        print(f"\nTotal Payload Size: {payload_mb:.2f} MB")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
