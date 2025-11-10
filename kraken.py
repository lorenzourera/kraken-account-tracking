"""Kraken exchange connector"""
import ccxt
from datetime import datetime
from decimal import Decimal

class KrakenConnector:
    def __init__(self, api_key: str, api_secret: str, account_id: str = None):
        self.exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        # Store account identifier
        self.account_id = account_id if account_id else api_key[-8:]
    
    def get_account_balance(self):
        """
        Fetch current account balance from Kraken
        
        Returns dict with:
            - exchange: 'kraken'
            - account_id: account identifier
            - timestamp: datetime
            - total_balance_usd: Decimal
            - balances: dict of {currency: amount}
            - raw_data: full API response
        """
        try:
            # Fetch balance
            balance = self.exchange.fetch_balance()
            
            # Get USD prices for all assets
            tickers = self.exchange.fetch_tickers()
            # pprint(f)
            # pprint(tickers)
            
            # Calculate total in USD
            total_usd = Decimal('0')
            balances = {}
            
            for currency, amount in balance['total'].items():
                if "." in currency:
                    currency = currency.split(".")[0] # if ETH.F -> ETH
                if amount > 0:
                    balances[currency] = float(amount)
                    
                    # Convert to USD
                    if currency in ['USD', 'ZUSD', "USDT", "USDC", "USD.F", "ZUSD.F", "USDT.F", "USDC.F"]:
                        total_usd += Decimal(str(amount))
                    else:
                        # Try to find USD pair
                        symbol = f"{currency}/USD"
                        if symbol in tickers:
                            price = Decimal(str(tickers[symbol]['last']))
                            # print(f"USD Price: {price}")
                            total_usd += price * Decimal(str(amount))
                        else:
                            print(f"{currency} not in tickers, cant get USD price")
            
            return {
                'exchange': 'kraken',
                'account_id': self.account_id,  # NEW
                'timestamp': datetime.now(),
                'total_balance_usd': total_usd,
                'balances': balances,
                'raw_data': balance
            }
        
        except Exception as e:
            raise Exception(f"Failed to fetch Kraken balance: {str(e)}")
    
    def test_connection(self):
        """Test if API credentials work"""
        try:
            self.exchange.fetch_balance()
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
        

# For Testing Purposes
if __name__ == "__main__":
    from config import KRAKEN_API_KEY, KRAKEN_API_SECRET
    from pprint import pprint

    client = KrakenConnector(api_key=KRAKEN_API_KEY, api_secret=KRAKEN_API_SECRET)
    balances = client.get_account_balance()
    pprint(balances)