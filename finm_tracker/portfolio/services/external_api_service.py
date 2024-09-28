import yfinance as yf
from django.core.cache import cache
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
import pandas as pd

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
        


    @staticmethod
    def _fetch_daily_gainers(count=25):
        url = f"https://finance.yahoo.com/gainers?count={count}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        try:
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            table = soup.find('table', {'class': 'W(100%)'})
            
            if table:
                headers = [th.text for th in table.find_all('th')]
                rows = []
                for row in table.find_all('tr')[1:]:
                    rows.append([td.text for td in row.find_all('td')])
                
                df = pd.DataFrame(rows, columns=headers)
                return df.to_dict('records')
            else:
                return []
        except Exception as e:
            print(f"Error fetching daily gainers: {str(e)}")
            return []