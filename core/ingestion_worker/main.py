import os
import sys
from dotenv import load_dotenv
import spacy
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from sources import HistoricalEdgarFetcher
from schemas import FinancialDocument, TokenizedContext, TextChunk, EmbeddingContext
from utils import chunk_tokenized_context

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 64
# Subword tokens shared between consecutive chunks, so a fact that straddles a
# boundary is still fully contained in at least one chunk.
CHUNK_OVERLAP_SUBWORDS = 32

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
    documents: list[FinancialDocument] = []

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

        nlp = spacy.load("en_core_web_sm")

        # Only the tokenizer is needed here. Running it directly skips the
        # tagger/parser/NER (much faster, no nlp.max_length limit on long docs).
        # The tokenizer is CPU-only, so spacy.prefer_gpu() would have no effect.
        tokenized_contexts: list[TokenizedContext] = []

        for doc in tqdm(documents, desc="Tokenizing documents"):
            spacy_doc = nlp.tokenizer(doc.content)
            kept = [token for token in spacy_doc if not token.is_space]
            tokenized_contexts.append(
                TokenizedContext(
                    document=doc,
                    tokens=[token.text for token in kept],
                    token_offsets=[token.idx for token in kept],
                )
            )

        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, token=os.getenv("HF_TOKEN"))

        if torch.cuda.is_available():
            print("PyTorch is using a GPU (CUDA is available).")
            print(f"Current CUDA device: {torch.cuda.get_device_name(0)}")
        else:
            print("PyTorch is currently running on CPU (CUDA is not available).")

        # Reserve room for the [CLS] and [SEP] tokens the model adds to every input.
        max_subwords = embedding_model.max_seq_length - 2

        chunked: list[tuple[TokenizedContext, TextChunk]] = []
        for tokenized_context in tqdm(tokenized_contexts, desc="Chunking documents"):
            for chunk in chunk_tokenized_context(
                tokenized_context,
                embedding_model.tokenizer,
                max_subwords=max_subwords,
                overlap_subwords=CHUNK_OVERLAP_SUBWORDS,
            ):
                chunked.append((tokenized_context, chunk))

        print(f"Split {len(tokenized_contexts)} documents into {len(chunked)} chunks.")

        # Encode all chunks in one batched call; far faster than one call per document.
        embeddings = embedding_model.encode(
            [chunk.text for _, chunk in chunked],
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=True,
        )

        embedding_contexts: list[EmbeddingContext] = [
            EmbeddingContext(tokenized_context=tokenized_context, chunk=chunk, embedding=embedding.tolist())
            for (tokenized_context, chunk), embedding in zip(chunked, embeddings)
        ]

        print(f"Created {len(embedding_contexts)} embedding contexts.")
        print(f"Sample embedding vector length: {len(embedding_contexts[0].embedding)}")
        print(f"Sample embedding vector (first 5 values): {embedding_contexts[0].embedding[:5]}")
        print(f"Sample embedding context chunk text: {embedding_contexts[0].chunk.text[:100]}...")

    except Exception as e:
        print(f"❌ An error occurred during the fetching process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
