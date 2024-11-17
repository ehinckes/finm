import yfinance as yf
from django.core.cache import cache
from decimal import Decimal

class ExternalAPIService:
    """
    Service class for fetching financial asset information from external sources.
    Primary data source is Yahoo Finance (yfinance) with support for US stocks,
    Australian stocks, and cryptocurrencies.
    """

    @staticmethod
    def fetch_asset_info(asset_symbol, asset_type):
        """
        Factory method to fetch asset information based on asset type.
        
        Args:
            asset_symbol (str): The ticker symbol of the asset
            asset_type (str): Type of asset - 'stock_us', 'stock_au', or 'crypto'
            
        Returns:
            dict: Asset information including name, last price, and sector
            
        Raises:
            ValueError: If asset_type is invalid or if asset info cannot be fetched
        """
        if asset_type == 'stock_us':
            return ExternalAPIService._fetch_us_stock_info(asset_symbol)
        elif asset_type == 'stock_au':
            return ExternalAPIService._fetch_au_stock_info(asset_symbol)
        elif asset_type == 'crypto':
            return ExternalAPIService._fetch_crypto_info(asset_symbol)
        else:
            raise ValueError("Invalid asset type")
        
    @staticmethod
    def _fetch_us_stock_info(asset_symbol):
        """
        Fetches information for US stocks using yfinance.
        
        Args:
            asset_symbol (str): The stock ticker symbol
            
        Returns:
            dict: Contains:
                - name: Company's full name
                - last_price: Current bid price as Decimal
                - sector: Company's sector or 'Unknown'
                
        Raises:
            ValueError: If unable to fetch stock information
        """
        try:
            ticker = yf.Ticker(asset_symbol)
            info = ticker.info

            return {
                'name': info.get('longName', asset_symbol),
                'last_price': Decimal(str(info.get('bid', 0))),
                'sector': info.get('sector', 'Unknown')
            }
        
        except Exception as e:
            print(f"Error fetching asset info for {asset_symbol}: {e}")
            raise ValueError(f"Unable to fetch info for asset {asset_symbol}")

    @staticmethod
    def _fetch_au_stock_info(asset_symbol):
        """
        Fetches information for Australian stocks using yfinance.
        Note: Uses same structure as US stocks but simplifies sector to "Aus Equity"
        
        Args:
            asset_symbol (str): The ASX stock ticker symbol
            
        Returns:
            dict: Contains:
                - name: Company's full name
                - last_price: Current bid price as Decimal
                - sector: Always "Aus Equity"
                
        Raises:
            ValueError: If unable to fetch stock information
        """
        try:
            ticker = yf.Ticker(asset_symbol)
            info = ticker.info

            return {
                'name': info.get('longName', asset_symbol),
                'last_price': Decimal(str(info.get('bid', 0))),
                'sector': "Aus Equity"
            }
        
        except Exception as e:
            print(f"Error fetching asset info for {asset_symbol}: {e}")
            raise ValueError(f"Unable to fetch info for asset {asset_symbol}")

    @staticmethod
    def _fetch_crypto_info(asset_symbol):
        """
        Fetches information for cryptocurrencies using yfinance.
        Note: Uses 'open' price instead of 'bid' for current price
        
        Args:
            asset_symbol (str): The cryptocurrency symbol
            
        Returns:
            dict: Contains:
                - name: Cryptocurrency name
                - last_price: Current open price as Decimal
                - sector: Always "Cryptocurrency"
                
        Raises:
            ValueError: If unable to fetch cryptocurrency information
        """
        try:
            ticker = yf.Ticker(asset_symbol)
            info = ticker.info

            return {
                'name': info.get('name', asset_symbol),
                'last_price': Decimal(str(info.get('open', 0))),  # Using open price as current price for crypto
                'sector': "Cryptocurrency"
            }
        
        except Exception as e:
            print(f"Error fetching asset info for {asset_symbol}: {e}")
            raise ValueError(f"Unable to fetch info for asset {asset_symbol}")

    @staticmethod
    def fetch_latest_price(asset_symbol, asset_type):
        """
        Fetches only the latest price for a given asset, optimized for bulk updates.
        
        Args:
            asset_symbol (str): The ticker symbol of the asset
            asset_type (str): Type of asset - 'stock_us', 'stock_au', or 'crypto'
            
        Returns:
            Decimal: Latest price of the asset
            
        Raises:
            ValueError: If unable to fetch price
        """
        try:
            ticker = yf.Ticker(asset_symbol)
            
            # For crypto we use 'open' price, for stocks we use 'bid'
            if asset_type == 'crypto':
                price = ticker.info.get('open', 0)
            else:
                price = ticker.info.get('bid', 0)
                
            return Decimal(str(price))
        
        except Exception as e:
            print(f"Error fetching price for {asset_symbol}: {e}")
            return None  # Return None instead of raising error for bulk operations
