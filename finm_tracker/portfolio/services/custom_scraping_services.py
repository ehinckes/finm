import requests
from bs4 import BeautifulSoup
import re


class CustomScrapingService:
    
    @staticmethod
    def fetch_stock_movers(movement):

        if movement == "gainers" or movement == "losers":
            url = f"https://finance.yahoo.com/markets/stocks/{movement}"
        else:
            raise ValueError("Invalid movement type. Use 'gainers' or 'losers'.")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            table = soup.find('table', {'class': re.compile('markets-table')})
            if not table:
                print(f"Could not find the table on the page: {url}")
                return []
            
            rows = table.find_all('tr')[1:4]  # Get top 3 rows, excluding header
            movers = []
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 5:
                    symbol = columns[0].text.strip().split(' ')[0]
                    price = columns[1].text.strip().split(' ')[0]
                    change = columns[2].text.strip()
                    percent_change = columns[3].text.strip()
                    volume = columns[4].text.strip() if len(columns) > 4 else "N/A"

                    movers.append({
                        'Symbol': symbol,
                        'Price': price,
                        'Change': change,
                        'Percent_Change': percent_change,
                        'Volume': volume
                    })
            return movers
        except requests.RequestException as e:
            print(f"An error occurred while fetching the data: {e}")
            return []
        
    
    @staticmethod
    def fetch_crypto_movers(movement):

        if movement == "gainers" or movement == "losers":
            url = f"https://finance.yahoo.com/markets/crypto/{movement}"
        else:
            raise ValueError("Invalid movement type. Use 'gainers' or 'losers'.")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            table = soup.find('table', {'class': re.compile('markets-table')})
            if not table:
                print(f"Could not find the table on the page: {url}")
                return []
            
            rows = table.find_all('tr')[1:4]  # Get top 3 rows, excluding header
            movers = []
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 5:

                    symbol_data = columns[0].text.strip().split()
                    # Check if the first part is a single character, and adjust accordingly
                    if len(symbol_data) > 1 and len(symbol_data[0]) == 1:
                        symbol = symbol_data[1]
                    else:
                        symbol = symbol_data[0]

                    price = columns[1].text.strip().split(' ')[0]
                    change = columns[2].text.strip()
                    percent_change = columns[3].text.strip()
                    volume = columns[6].text.strip() if len(columns) > 6 else "N/A"

                    movers.append({
                        'Symbol': symbol,
                        'Price': price,
                        'Change': change,
                        'Percent_Change': percent_change,
                        'Volume': volume
                    })
            return movers
        except requests.RequestException as e:
            print(f"An error occurred while fetching the data: {e}")
            return []