# """Kraken exchange connector"""
# import ccxt
# from datetime import datetime
# from decimal import Decimal
# from pprint import pprint


# class KrakenConnector:
#     # USD-equivalent currencies that should be valued at 1:1
#     USD_EQUIVALENTS = {
#         "USD", "ZUSD", "USDT", "USDC",
#         "USD.F", "ZUSD.F", "USDT.F", "USDC.F"
#     }
    
#     def __init__(self, api_key: str, api_secret: str, account_id: str = None):
#         self.exchange = ccxt.kraken(
#             {
#                 "apiKey": api_key,
#                 "secret": api_secret,
#                 "enableRateLimit": True,
#             }
#         )
#         # Store account identifier
#         self.account_id = account_id if account_id else api_key[-8:]

#     def _calculate_usd_value(self, currency: str, amount: float, tickers: dict) -> Decimal:
#         """
#         Calculate USD value for a given currency and amount
        
#         Args:
#             currency: Currency code (e.g., 'BTC', 'ETH', 'USD')
#             amount: Amount of the currency
#             tickers: Dictionary of ticker data from exchange
            
#         Returns:
#             Decimal: USD value of the amount
#         """
#         # Clean currency code (remove .F suffix if present)
#         clean_currency = currency.split(".")[0] if "." in currency else currency
        
#         # USD equivalents are 1:1
#         if currency in self.USD_EQUIVALENTS:
#             return Decimal(str(amount))
        
#         # Try to find USD pair for other currencies
#         symbol = f"{clean_currency}/USD"
#         if symbol in tickers:
#             price = Decimal(str(tickers[symbol]["last"]))
#             return price * Decimal(str(amount))
        
#         # If no USD pair found, print warning and return 0
#         print(f"{clean_currency} not in tickers, can't get USD price")
#         return Decimal("0")

#     def get_account_balance(self):
#         """
#         Fetch current account balance from Kraken

#         Returns dict with:
#             - exchange: 'kraken'
#             - account_id: account identifier
#             - timestamp: datetime
#             - total_balance_usd: Decimal
#             - balances: dict of {currency: {amount, usd_value}}
#             - raw_data: full API response
#         """
#         try:
#             # Fetch balance and tickers
#             balance = self.exchange.fetch_balance()
#             tickers = self.exchange.fetch_tickers()
            
#             pprint(balance)

#             # Calculate total in USD and build balances dict
#             total_usd = Decimal("0")
#             balances = {}

#             for currency, amount in balance["total"].items():
#                 if amount > 0:
#                     # Clean currency code for display
#                     clean_currency = currency.split(".")[0] if "." in currency else currency
                    
#                     # Calculate USD value
#                     usd_value = self._calculate_usd_value(currency, amount, tickers)
                    
#                     # Add to balances dict
#                     balances[clean_currency] = {
#                         "amount": Decimal(str(amount)),
#                         "usd_value": usd_value
#                     }
                    
#                     # Add to total
#                     total_usd += usd_value

#             return {
#                 "exchange": "kraken",
#                 "account_id": self.account_id,
#                 "timestamp": datetime.now(),
#                 "total_balance_usd": total_usd,
#                 "balances": balances,
#                 "raw_data": balance,
#             }

#         except Exception as e:
#             raise Exception(f"Failed to fetch Kraken balance: {str(e)}")

#     def test_connection(self):
#         """Test if API credentials work"""
#         try:
#             self.exchange.fetch_balance()
#             return True
#         except Exception as e:
#             print(f"Connection test failed: {str(e)}")
#             return False


# # For Testing Purposes
# if __name__ == "__main__":
#     from config import KRAKEN_API_KEY, KRAKEN_API_SECRET
#     from pprint import pprint

#     client = KrakenConnector(api_key=KRAKEN_API_KEY, api_secret=KRAKEN_API_SECRET)
#     balances = client.get_account_balance()
#     pprint(balances)


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

    def get_trades(self, symbol: str = None, since: int = None, limit: int = 100):
        """
        Fetch historical trades from Kraken
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD', 'ETH/USD'). If None, fetches all trades.
            since: Timestamp in milliseconds to fetch trades from. If None, fetches recent trades.
            limit: Maximum number of trades to fetch (default: 100)
            
        Returns:
            List of trade dictionaries with:
                - id: Trade ID
                - timestamp: datetime
                - datetime: ISO datetime string
                - symbol: Trading pair
                - type: 'limit' or 'market'
                - side: 'buy' or 'sell'
                - price: Trade price
                - amount: Trade amount
                - cost: Total cost (price * amount)
                - fee: Fee paid
                - fee_currency: Currency of the fee
        """
        try:
            if symbol:
                # Fetch trades for specific symbol
                trades = self.exchange.fetch_my_trades(symbol=symbol, since=since, limit=limit)
            else:
                # Fetch all trades (this may take a while)
                trades = self.exchange.fetch_my_trades(since=since, limit=limit)
            
            return trades
        
        except Exception as e:
            raise Exception(f"Failed to fetch Kraken trades: {str(e)}")

    def print_trades(self, trades: list, detailed: bool = False):
        """
        Pretty print trades to console
        
        Args:
            trades: List of trade dictionaries from get_trades()
            detailed: If True, prints all details. If False, prints summary.
        """
        if not trades:
            print("No trades found")
            return
        
        print(f"\n{'='*80}")
        print(f"TRADE HISTORY - {len(trades)} trades")
        print(f"{'='*80}\n")
        
        if detailed:
            # Detailed view - one trade per section
            for i, trade in enumerate(trades, 1):
                print(f"Trade #{i}")
                print(f"  ID: {trade.get('id', 'N/A')}")
                print(f"  Date: {trade.get('datetime', 'N/A')}")
                print(f"  Symbol: {trade.get('symbol', 'N/A')}")
                print(f"  Side: {trade.get('side', 'N/A').upper()}")
                print(f"  Type: {trade.get('type', 'N/A')}")
                print(f"  Amount: {trade.get('amount', 0):,.8f}")
                print(f"  Price: ${trade.get('price', 0):,.2f}")
                print(f"  Cost: ${trade.get('cost', 0):,.2f}")
                
                fee = trade.get('fee', {})
                if fee:
                    fee_cost = fee.get('cost', 0)
                    fee_currency = fee.get('currency', 'N/A')
                    print(f"  Fee: {fee_cost} {fee_currency}")
                
                print(f"{'-'*80}\n")
        else:
            # Summary table view
            print(f"{'Date':<20} {'Symbol':<12} {'Side':<6} {'Amount':>15} {'Price':>12} {'Cost':>12}")
            print(f"{'-'*80}")
            
            for trade in trades:
                date_str = trade.get('datetime', 'N/A')[:19] if trade.get('datetime') else 'N/A'
                symbol = trade.get('symbol', 'N/A')
                side = trade.get('side', 'N/A').upper()
                amount = trade.get('amount', 0)
                price = trade.get('price', 0)
                cost = trade.get('cost', 0)
                
                # Add color/symbol for buy/sell
                side_display = f"{'🟢' if side == 'BUY' else '🔴'} {side}"
                
                print(f"{date_str:<20} {symbol:<12} {side_display:<6} {amount:>15,.8f} ${price:>11,.2f} ${cost:>11,.2f}")
            
            print(f"{'-'*80}")
            
            # Summary statistics
            total_buys = sum(1 for t in trades if t.get('side') == 'buy')
            total_sells = sum(1 for t in trades if t.get('side') == 'sell')
            total_volume = sum(t.get('cost', 0) for t in trades)
            
            print(f"\nSummary:")
            print(f"  Total Trades: {len(trades)}")
            print(f"  Buys: {total_buys} | Sells: {total_sells}")
            print(f"  Total Volume: ${total_volume:,.2f}")

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
    trades = client.get_trades()
    client.print_trades(trades)