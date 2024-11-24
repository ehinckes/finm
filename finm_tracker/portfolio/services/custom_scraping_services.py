import requests
from bs4 import BeautifulSoup
import re

class CustomScrapingService:
    """
    A service class that scrapes Yahoo Finance for top market movers data.
    Provides functionality to fetch both stock and cryptocurrency gainers/losers.
    """
     
    @staticmethod
    def fetch_stock_movers(movement):
        """
        Scrapes Yahoo Finance for top stock movers (gainers or losers).
        
        Args:
            movement (str): Type of movement to fetch - either 'gainers' or 'losers'
            
        Returns:
            list: List of dictionaries containing mover data with keys:
                 'Symbol', 'Price', 'Change', 'Percent_Change', 'Volume'
                 Returns empty list if scraping fails
                 
        Raises:
            ValueError: If movement parameter is neither 'gainers' nor 'losers'
        """
        # Validate and construct the URL based on movement type
        if movement == "gainers" or movement == "losers":
            url = f"https://finance.yahoo.com/markets/stocks/{movement}"
        else:
            raise ValueError("Invalid movement type. Use 'gainers' or 'losers'.")
        
        # Set headers to mimic a browser request to avoid blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            # Make the HTTP request and parse the response
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raises exception for bad status codes
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the market movers table using regex pattern matching
            table = soup.find('table', {'class': re.compile('markets-table')})
            if not table:
                print(f"Could not find the table on the page: {url}")
                return []
            
            # Extract top 3 rows (excluding header row)
            rows = table.find_all('tr')[1:4]
            movers = []
            
            # Process each row to extract relevant data
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 5:
                    # Extract and clean data from each column
                    symbol = columns[0].text.strip().split(' ')[0]
                    price = columns[1].text.strip().split(' ')[0]
                    change = columns[2].text.strip()
                    percent_change = columns[3].text.strip()
                    volume = columns[4].text.strip() if len(columns) > 4 else "N/A"

                    # Build dictionary with extracted data
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
        """
        Scrapes Yahoo Finance for top cryptocurrency movers (gainers or losers).
        
        Args:
            movement (str): Type of movement to fetch - either 'gainers' or 'losers'
            
        Returns:
            list: List of dictionaries containing mover data with keys:
                 'Symbol', 'Price', 'Change', 'Percent_Change', 'Volume'
                 Returns empty list if scraping fails
                 
        Raises:
            ValueError: If movement parameter is neither 'gainers' nor 'losers'
        """
        # Similar URL construction and validation as fetch_stock_movers
        if movement == "gainers" or movement == "losers":
            url = f"https://finance.yahoo.com/markets/crypto/{movement}"
        else:
            raise ValueError("Invalid movement type. Use 'gainers' or 'losers'.")
        
        # Use the same browser headers to avoid blocking
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
            
            # Extract top 3 rows (excluding header row)
            rows = table.find_all('tr')[1:4]
            movers = []
            
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 5:
                    # Special handling for crypto symbols which may have currency indicators
                    symbol_data = columns[0].text.strip().split()
                    # If first character is a currency symbol (length 1), take the second part
                    if len(symbol_data) > 1 and len(symbol_data[0]) == 1:
                        symbol = symbol_data[1]
                    else:
                        symbol = symbol_data[0]

                    # Extract other data points
                    price = columns[1].text.strip().split(' ')[0]
                    change = columns[2].text.strip()
                    percent_change = columns[3].text.strip()
                    # Note: Crypto table has volume in column 7 (index 6)
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
