import yfinance as yf
from datetime import datetime
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal


class ExternalAPIService:
    @staticmethod
    def fetch_asset_info(asset_symbol, asset_type):
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
        try:
            ticker = yf.Ticker(asset_symbol)
            info = ticker.info

            return {
                'name': info.get('longName', asset_symbol),
                'last_price': Decimal(str(info.get('bid', 0)))
            }
        
        except Exception as e:
            print(f"Error fetching asset info for {asset_symbol}: {e}")
            raise ValueError(f"Unable to fetch info for asset {asset_symbol}")


    @staticmethod
    def _fetch_au_stock_info(asset_symbol):
        try:
            ticker = yf.Ticker(asset_symbol)
            info = ticker.info

            return {
                'name': info.get('longName', asset_symbol),
                'last_price': Decimal(str(info.get('bid', 0)))
            }
        
        except Exception as e:
            print(f"Error fetching asset info for {asset_symbol}: {e}")
            raise ValueError(f"Unable to fetch info for asset {asset_symbol}")
        


    @staticmethod
    def _fetch_crypto_info(asset_symbol):
        
        try:
            ticker = yf.Ticker(asset_symbol)
            info = ticker.info

            return {
                'name': info.get('name', asset_symbol),
                'last_price': Decimal(str(info.get('open', 0))) # Using open price as current price for crypto
            }
        
        except Exception as e:
            print(f"Error fetching asset info for {asset_symbol}: {e}")
            raise ValueError(f"Unable to fetch info for asset {asset_symbol}")
        
