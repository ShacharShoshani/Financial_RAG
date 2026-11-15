from abc import ABC, abstractmethod
from typing import Any, List, final
from schemas import FinancialDocument


class BaseFetcher(ABC):
    """
    Abstract base class for all financial data source fetchers.
    Forces every concrete scraper and client to return a list of standardized FinancialDocument objects.

    Subclasses implement two steps, which `fetch` runs in order:
        1. `_fetch_raw`: retrieve the raw data from the source.
        2. `_preprocess`: convert that raw data into FinancialDocument instances.

    `fetch` itself must not be overridden.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "fetch" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must not override 'fetch'; "
                "implement '_fetch_raw' and '_preprocess' instead."
            )

    @final
    def fetch(self, ticker: str, **kwargs) -> List[FinancialDocument]:
        """
        Fetch data for the given ticker from the datasource and convert it
        to FinancialDocument instances.

        Args:
            ticker (str): The stock ticker symbol (e.g., 'AAPL', 'MSFT').
            **kwargs: Additional parameters specific to the data source (e.g., date ranges, limits).

        Returns:
            List[FinancialDocument]: A list of clean, standardized documents ready for vector embedding.
        """
        raw_data = self._fetch_raw(ticker, **kwargs)
        return self._preprocess(raw_data, ticker, **kwargs)

    @abstractmethod
    def _fetch_raw(self, ticker: str, **kwargs) -> Any:
        """
        Retrieve the raw, unprocessed data for the given ticker from the datasource.

        Args:
            ticker (str): The stock ticker symbol.
            **kwargs: The same source-specific parameters passed to `fetch`.

        Returns:
            Any: The raw data in whatever shape the source provides it.
        """

    @abstractmethod
    def _preprocess(self, raw_data: Any, ticker: str, **kwargs) -> List[FinancialDocument]:
        """
        Convert the raw data returned by `_fetch_raw` into FinancialDocument instances.

        Args:
            raw_data (Any): The value returned by `_fetch_raw`.
            ticker (str): The stock ticker symbol.
            **kwargs: The same source-specific parameters passed to `fetch`.

        Returns:
            List[FinancialDocument]: A list of clean, standardized documents ready for vector embedding.
        """
