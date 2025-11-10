"""Kraken exchange connector"""
import ccxt
from datetime import datetime
from decimal import Decimal
from pprint import pprint


class KrakenConnector:
    # USD-equivalent currencies that should be valued at 1:1
    USD_EQUIVALENTS = {
        "USD", "ZUSD", "USDT", "USDC",
        "USD.F", "ZUSD.F", "USDT.F", "USDC.F"
    }
    
    def __init__(self, api_key: str, api_secret: str, account_id: str = None):
        self.exchange = ccxt.kraken(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            }
        )
        # Store account identifier
        self.account_id = account_id if account_id else api_key[-8:]

    def _calculate_usd_value(self, currency: str, amount: float, tickers: dict) -> Decimal:
        """
        Calculate USD value for a given currency and amount
        
        Args:
            currency: Currency code (e.g., 'BTC', 'ETH', 'USD')
            amount: Amount of the currency
            tickers: Dictionary of ticker data from exchange
            
        Returns:
            Decimal: USD value of the amount
        """
        # Clean currency code (remove .F suffix if present)
        clean_currency = currency.split(".")[0] if "." in currency else currency
        
        # USD equivalents are 1:1
        if currency in self.USD_EQUIVALENTS:
            return Decimal(str(amount))
        
        # Try to find USD pair for other currencies
        symbol = f"{clean_currency}/USD"
        if symbol in tickers:
            price = Decimal(str(tickers[symbol]["last"]))
            return price * Decimal(str(amount))
        
        # If no USD pair found, print warning and return 0
        print(f"{clean_currency} not in tickers, can't get USD price")
        return Decimal("0")

    def get_account_balance(self):
        """
        Fetch current account balance from Kraken

        Returns dict with:
            - exchange: 'kraken'
            - account_id: account identifier
            - timestamp: datetime
            - total_balance_usd: Decimal
            - balances: dict of {currency: {amount, usd_value}}
            - raw_data: full API response
        """
        try:
            # Fetch balance and tickers
            balance = self.exchange.fetch_balance()
            tickers = self.exchange.fetch_tickers()
            
            pprint(balance)

            # Calculate total in USD and build balances dict
            total_usd = Decimal("0")
            balances = {}

            for currency, amount in balance["total"].items():
                if amount > 0:
                    # Clean currency code for display
                    clean_currency = currency.split(".")[0] if "." in currency else currency
                    
                    # Calculate USD value
                    usd_value = self._calculate_usd_value(currency, amount, tickers)
                    
                    # Add to balances dict
                    balances[clean_currency] = {
                        "amount": Decimal(str(amount)),
                        "usd_value": usd_value
                    }
                    
                    # Add to total
                    total_usd += usd_value

            return {
                "exchange": "kraken",
                "account_id": self.account_id,
                "timestamp": datetime.now(),
                "total_balance_usd": total_usd,
                "balances": balances,
                "raw_data": balance,
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