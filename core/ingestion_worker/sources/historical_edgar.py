import json
import zipfile
from pydantic import HttpUrl
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from tqdm import tqdm

from sources.base import BaseFetcher
from schemas.document import FinancialDocument


class HistoricalEdgarFetcher(BaseFetcher):
    """
    Downloads, extracts, and parses the SEC EDGAR bulk historical dataset (companyfacts.zip).
    Designed to run once to bootstrap the local vector database.
    """

    def __init__(self, user_agent: str, data_dir: str = ".data/sec_historical"):
        """
        Args:
            user_agent (str): Mandatory SEC header (e.g., 'MyRAGApp/1.0 (shachar@example.com)').
            data_dir (str): Local directory to store the multi-gigabyte historical data.
        """
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}

        # Setup paths using modern pathlib
        self.data_dir = Path(data_dir)
        self.zip_path = self.data_dir / "companyfacts.zip"
        self.extracted_dir = self.data_dir / "companyfacts"

    def _download_and_extract_if_needed(self) -> None:
        """
        Ensures the data exists locally. Downloads and extracts it if missing,
        with a visual progress bar.
        """
        if self.extracted_dir.exists() and any(self.extracted_dir.iterdir()):
            print("Historical data already extracted. Skipping download.")
            return

        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.zip_path.exists():
            print(
                "Downloading historical SEC bulk data (~1GB compressed). This may take a while..."
            )
            zip_url = (
                "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
            )

            with requests.get(zip_url, headers=self.headers, stream=True) as response:
                response.raise_for_status()

                # Get the total file size from the headers to calculate the percentage
                total_size = int(response.headers.get("content-length", 0))

                # Configure the tqdm progress bar
                with open(self.zip_path, "wb") as f, tqdm(
                    desc="Downloading companyfacts.zip",
                    total=total_size,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress_bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            progress_bar.update(
                                len(chunk)
                            )  # Update the bar by the chunk size
            print("Download complete.")

        print("Extracting JSON files (this process does not use tqdm, please wait)...")
        self.extracted_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
            zip_ref.extractall(self.extracted_dir)
        print("Extraction complete.")

    @staticmethod
    def _convert_edgar_json_to_text(raw_json: Dict[str, Any]) -> List[str]:
        """
        Parses a raw SEC EDGAR companyfacts JSON object and flattens it
        into a list of human-readable text strings for an embedding model.
        """
        # 1. Get the company name (Fallback to 'The company' if missing)
        entity_name = raw_json.get("entityName", "The company")
        facts_data = raw_json.get("facts", {})

        text_chunks = []

        # 2. Iterate through all taxonomies (e.g., 'us-gaap', 'dei')
        for taxonomy, concepts in facts_data.items():

            # 3. Iterate through all financial concepts (e.g., 'Revenues')
            for concept_key, concept_info in concepts.items():
                label = concept_info.get("label", concept_key)
                description = concept_info.get("description", "")
                description = description.strip() if description else ""
                desc_text = f" (Definition: {description})" if description else ""

                # 4. Iterate through measurement units (e.g., 'USD', 'shares')
                for unit, facts_array in concept_info.get("units", {}).items():

                    # 5. Iterate through the historical timeline array
                    for fact in facts_array:
                        val = fact.get("val")
                        end_date = fact.get("end")
                        fy = fact.get("fy", "an unspecified year")
                        fp = fact.get("fp", "an unspecified period")
                        form = fact.get("form", "an SEC filing")

                        # Skip incomplete data points
                        if val is None or not end_date:
                            continue

                        # Format numbers nicely (e.g., 895816758 -> 895,816,758)
                        try:
                            if isinstance(val, (int, float)):
                                formatted_val = f"{val:,}"
                            else:
                                formatted_val = str(val)
                        except Exception:
                            formatted_val = str(val)

                        # 6. Construct the simple, dense sentence for the embedding model
                        sentence = (
                            f"In the {form} filing for fiscal year {fy} period {fp}, "
                            f"{entity_name} reported {label}{desc_text} of {formatted_val} {unit} "
                            f"as of {end_date}."
                        )

                        text_chunks.append(sentence)

        return text_chunks

    def _fetch_raw(self, ticker: str, **kwargs) -> Optional[dict]:
        """
        Reads the raw historical facts JSON for a specific company from the local dataset.

        Args:
            ticker (str): The stock ticker (e.g., 'AAPL').
            **kwargs: Must contain 'cik' (Central Index Key) to find the SEC file.

        Returns:
            Optional[dict]: The parsed JSON, or None if no file exists for the company.
        """
        # Ensure the bulk dataset is ready on disk
        self._download_and_extract_if_needed()

        # The SEC identifies files internally by a 10-digit zero-padded CIK, not the ticker.
        # We expect the pipeline to pass the mapped CIK via kwargs.
        cik = kwargs.get("cik")
        if not cik:
            raise ValueError(
                f"A CIK must be provided to fetch EDGAR data for {ticker}."
            )

        padded_cik = str(cik).zfill(10)
        file_name = f"CIK{padded_cik}.json"
        file_path = self.extracted_dir / file_name

        if not file_path.exists():
            print(
                f"Warning: No historical file found for {ticker} (CIK: {padded_cik})."
            )
            return None

        # Read the local JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _preprocess(
        self, raw_data: Optional[dict], ticker: str, **kwargs
    ) -> List[FinancialDocument]:
        """
        Converts the raw company facts JSON into FinancialDocument instances.

        Args:
            raw_data (Optional[dict]): The JSON returned by `_fetch_raw`, or None if missing.
            ticker (str): The stock ticker (e.g., 'AAPL').
        """
        if raw_data is None:
            return []

        # Note: raw_data["facts"] contains a massive nested dictionary of every XBRL tag
        # the company ever reported. You will eventually want to write a helper function
        # here to extract only the specific metrics you care about (e.g., Revenue, Assets)
        # before passing it to the text chunker.

        content = self._convert_edgar_json_to_text(raw_data)

        # Map to your strict pipeline schema
        document = FinancialDocument(
            title=f"{ticker} Historical SEC Facts",
            sentences=content,
            ticker_symbol=ticker,
            document_type="historical_company_facts",
            publish_date=datetime.now(timezone.utc),
            publisher="SEC EDGAR",
            source_url=HttpUrl(
                "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
            ),
        )

        return [document]
