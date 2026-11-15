from abc import ABC, abstractmethod
from typing import List
from schemas import FinancialDocument


class BaseFetcher(ABC):
    """
    Abstract base class for all financial data source fetchers.
    Forces every concrete scraper and client to return a list of standardized FinancialDocument objects.
    """

    @abstractmethod
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
        pass
