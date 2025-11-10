# # """Database operations"""

# # import psycopg2
# # from psycopg2.extras import RealDictCursor
# # from contextlib import contextmanager
# # import json
# # from decimal import Decimal


# # class Database:
# #     def __init__(self, connection_string: str):
# #         self.connection_string = connection_string

# #     def _decimal_to_str(self, obj):
# #         """Recursively convert Decimal → str for JSON safety"""
# #         if isinstance(obj, Decimal):
# #             return str(obj)
# #         if isinstance(obj, dict):
# #             return {k: self._decimal_to_str(v) for k, v in obj.items()}
# #         if isinstance(obj, list):
# #             return [self._decimal_to_str(v) for v in obj]
# #         return obj

# #     @contextmanager
# #     def get_connection(self):
# #         """Context manager for database connections"""
# #         conn = psycopg2.connect(self.connection_string)
# #         try:
# #             yield conn
# #             conn.commit()
# #         except Exception:
# #             conn.rollback()
# #             raise
# #         finally:
# #             conn.close()

# #     def save_balance_snapshot(self, snapshot: dict):
# #         """Save balance snapshot to database"""
# #         query = """
# #             INSERT INTO balance_snapshots (
# #                 exchange, account_id, snapshot_date, timestamp,
# #                 total_balance_usd, balances, raw_data
# #             ) VALUES (
# #                 %(exchange)s, %(account_id)s, %(snapshot_date)s, %(timestamp)s,
# #                 %(total_balance_usd)s, %(balances)s, %(raw_data)s
# #             )
# #             ON CONFLICT (exchange, account_id, snapshot_date) 
# #             DO UPDATE SET
# #                 timestamp = EXCLUDED.timestamp,
# #                 total_balance_usd = EXCLUDED.total_balance_usd,
# #                 balances = EXCLUDED.balances,
# #                 raw_data = EXCLUDED.raw_data
# #         """

# #         with self.get_connection() as conn:
# #             with conn.cursor() as cur:
# #                 cur.execute(
# #                     query,
# #                     {
# #                         "exchange": snapshot["exchange"],
# #                         "account_id": snapshot["account_id"],
# #                         "snapshot_date": snapshot["timestamp"].date(),
# #                         "timestamp": snapshot["timestamp"],
# #                         "total_balance_usd": snapshot["total_balance_usd"],
# #                         "balances": json.dumps(
# #                             self._decimal_to_str(snapshot["balances"])
# #                         ),
# #                         "raw_data": json.dumps(
# #                             self._decimal_to_str(snapshot.get("raw_data", {}))
# #                         ),
# #                     },
# #                 )

# #         print(
# #             f"Saved balance snapshot for {snapshot['account_id']} on {snapshot['timestamp'].date()}"
# #         )

# #     def get_latest_balance(self, exchange: str = "kraken", account_id: str = None):
# #         """Get most recent balance snapshot"""
# #         if account_id:
# #             query = """
# #                 SELECT * FROM balance_snapshots
# #                 WHERE exchange = %s AND account_id = %s
# #                 ORDER BY snapshot_date DESC
# #                 LIMIT 1
# #             """
# #             params = [exchange, account_id]
# #         else:
# #             # Get latest across all accounts for this exchange
# #             query = """
# #                 SELECT * FROM balance_snapshots
# #                 WHERE exchange = %s
# #                 ORDER BY snapshot_date DESC
# #                 LIMIT 1
# #             """
# #             params = [exchange]

# #         with self.get_connection() as conn:
# #             with conn.cursor(cursor_factory=RealDictCursor) as cur:
# #                 cur.execute(query, params)
# #                 row = cur.fetchone()
# #                 if row:
# #                     result = dict(row)
# #                     return result
# #                 return None

# #     def get_all_balances(
# #         self, exchange: str = "kraken", account_id: str = None, limit: int = 30
# #     ):
# #         """Get recent balance snapshots"""
# #         if account_id:
# #             query = """
# #                 SELECT * FROM balance_snapshots
# #                 WHERE exchange = %s AND account_id = %s
# #                 ORDER BY snapshot_date DESC
# #                 LIMIT %s
# #             """
# #             params = [exchange, account_id, limit]
# #         else:
# #             query = """
# #                 SELECT * FROM balance_snapshots
# #                 WHERE exchange = %s
# #                 ORDER BY snapshot_date DESC
# #                 LIMIT %s
# #             """
# #             params = [exchange, limit]

# #         with self.get_connection() as conn:
# #             with conn.cursor(cursor_factory=RealDictCursor) as cur:
# #                 cur.execute(query, params)
# #                 results = []
# #                 for row in cur.fetchall():
# #                     result = dict(row)
# #                     results.append(result)
# #                 return results

# #     def list_accounts(self, exchange: str = "kraken"):
# #         """List all accounts for an exchange"""
# #         query = """
# #             SELECT DISTINCT account_id, 
# #                    MAX(snapshot_date) as last_snapshot,
# #                    COUNT(*) as snapshot_count
# #             FROM balance_snapshots
# #             WHERE exchange = %s
# #             GROUP BY account_id
# #             ORDER BY last_snapshot DESC
# #         """

# #         with self.get_connection() as conn:
# #             with conn.cursor(cursor_factory=RealDictCursor) as cur:
# #                 cur.execute(query, [exchange])
# #                 return [dict(row) for row in cur.fetchall()]

# """Database operations"""

# import psycopg2
# from psycopg2.extras import RealDictCursor
# from contextlib import contextmanager
# import json
# from decimal import Decimal


# class Database:
#     def __init__(self, connection_string: str):
#         self.connection_string = connection_string

#     def _decimal_to_str(self, obj):
#         """Recursively convert Decimal → str for JSON safety"""
#         if isinstance(obj, Decimal):
#             return str(obj)
#         if isinstance(obj, dict):
#             return {k: self._decimal_to_str(v) for k, v in obj.items()}
#         if isinstance(obj, list):
#             return [self._decimal_to_str(v) for v in obj]
#         return obj

#     @contextmanager
#     def get_connection(self):
#         """Context manager for database connections"""
#         conn = psycopg2.connect(self.connection_string)
#         try:
#             yield conn
#             conn.commit()
#         except Exception:
#             conn.rollback()
#             raise
#         finally:
#             conn.close()

#     def create_returns_table(self):
#         """Create daily_returns table if it doesn't exist"""
#         query = """
#             CREATE TABLE IF NOT EXISTS daily_returns (
#                 id SERIAL PRIMARY KEY,
#                 exchange VARCHAR(50) NOT NULL,
#                 account_id VARCHAR(100) NOT NULL,
#                 return_date DATE NOT NULL,
#                 previous_date DATE NOT NULL,
#                 current_balance_usd NUMERIC(20,2) NOT NULL,
#                 previous_balance_usd NUMERIC(20,2) NOT NULL,
#                 daily_return_usd NUMERIC(20,2) NOT NULL,
#                 daily_return_pct NUMERIC(10,4) NOT NULL,
#                 timestamp TIMESTAMP NOT NULL,
#                 UNIQUE(exchange, account_id, return_date)
#             );
            
#             CREATE INDEX IF NOT EXISTS idx_returns_exchange_account 
#             ON daily_returns(exchange, account_id, return_date DESC);
#         """
        
#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(query)
        
#         print("Daily returns table created/verified")

#     def save_balance_snapshot(self, snapshot: dict):
#         """Save balance snapshot to database"""
#         query = """
#             INSERT INTO balance_snapshots (
#                 exchange, account_id, snapshot_date, timestamp,
#                 total_balance_usd, balances, raw_data
#             ) VALUES (
#                 %(exchange)s, %(account_id)s, %(snapshot_date)s, %(timestamp)s,
#                 %(total_balance_usd)s, %(balances)s, %(raw_data)s
#             )
#             ON CONFLICT (exchange, account_id, snapshot_date) 
#             DO UPDATE SET
#                 timestamp = EXCLUDED.timestamp,
#                 total_balance_usd = EXCLUDED.total_balance_usd,
#                 balances = EXCLUDED.balances,
#                 raw_data = EXCLUDED.raw_data
#         """

#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(
#                     query,
#                     {
#                         "exchange": snapshot["exchange"],
#                         "account_id": snapshot["account_id"],
#                         "snapshot_date": snapshot["timestamp"].date(),
#                         "timestamp": snapshot["timestamp"],
#                         "total_balance_usd": snapshot["total_balance_usd"],
#                         "balances": json.dumps(
#                             self._decimal_to_str(snapshot["balances"])
#                         ),
#                         "raw_data": json.dumps(
#                             self._decimal_to_str(snapshot.get("raw_data", {}))
#                         ),
#                     },
#                 )

#         print(
#             f"Saved balance snapshot for {snapshot['account_id']} on {snapshot['timestamp'].date()}"
#         )

#     def get_previous_balance(self, exchange: str, account_id: str, current_date):
#         """
#         Get the most recent balance snapshot before the given date
        
#         Args:
#             exchange: Exchange name (e.g., 'kraken')
#             account_id: Account identifier
#             current_date: The date to look before (datetime.date or datetime)
            
#         Returns:
#             Dict with balance snapshot data, or None if no previous snapshot exists
#         """
#         query = """
#             SELECT * FROM balance_snapshots
#             WHERE exchange = %s 
#             AND account_id = %s 
#             AND snapshot_date < %s
#             ORDER BY snapshot_date DESC
#             LIMIT 1
#         """
        
#         # Handle both datetime and date objects
#         if hasattr(current_date, 'date'):
#             current_date = current_date.date()
        
#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, [exchange, account_id, current_date])
#                 row = cur.fetchone()
#                 if row:
#                     return dict(row)
#                 return None

#     def save_daily_return(self, return_data: dict):
#         """
#         Save daily return record to database
        
#         Args:
#             return_data: Dict containing:
#                 - exchange
#                 - account_id
#                 - return_date
#                 - previous_date
#                 - current_balance_usd
#                 - previous_balance_usd
#                 - daily_return_usd
#                 - daily_return_pct
#                 - timestamp
#         """
#         query = """
#             INSERT INTO daily_returns (
#                 exchange, account_id, return_date, previous_date,
#                 current_balance_usd, previous_balance_usd,
#                 daily_return_usd, daily_return_pct, timestamp
#             ) VALUES (
#                 %(exchange)s, %(account_id)s, %(return_date)s, %(previous_date)s,
#                 %(current_balance_usd)s, %(previous_balance_usd)s,
#                 %(daily_return_usd)s, %(daily_return_pct)s, %(timestamp)s
#             )
#             ON CONFLICT (exchange, account_id, return_date)
#             DO UPDATE SET
#                 previous_date = EXCLUDED.previous_date,
#                 current_balance_usd = EXCLUDED.current_balance_usd,
#                 previous_balance_usd = EXCLUDED.previous_balance_usd,
#                 daily_return_usd = EXCLUDED.daily_return_usd,
#                 daily_return_pct = EXCLUDED.daily_return_pct,
#                 timestamp = EXCLUDED.timestamp
#         """
        
#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(query, return_data)
        
#         print(
#             f"Saved daily return for {return_data['account_id']} on {return_data['return_date']}: "
#             f"{return_data['daily_return_pct']:.2f}%"
#         )

#     def get_latest_return(self, exchange: str = "kraken", account_id: str = None):
#         """Get most recent daily return"""
#         if account_id:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY return_date DESC
#                 LIMIT 1
#             """
#             params = [exchange, account_id]
#         else:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s
#                 ORDER BY return_date DESC
#                 LIMIT 1
#             """
#             params = [exchange]
        
#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 row = cur.fetchone()
#                 if row:
#                     return dict(row)
#                 return None

#     def get_all_returns(
#         self, exchange: str = "kraken", account_id: str = None, limit: int = 100
#     ):
#         """Get historical daily returns"""
#         if account_id:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY return_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, account_id, limit]
#         else:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s
#                 ORDER BY return_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, limit]
        
#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 results = []
#                 for row in cur.fetchall():
#                     result = dict(row)
#                     results.append(result)
#                 return results

#     def get_latest_balance(self, exchange: str = "kraken", account_id: str = None):
#         """Get most recent balance snapshot"""
#         if account_id:
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT 1
#             """
#             params = [exchange, account_id]
#         else:
#             # Get latest across all accounts for this exchange
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT 1
#             """
#             params = [exchange]

#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 row = cur.fetchone()
#                 if row:
#                     result = dict(row)
#                     return result
#                 return None

#     def get_all_balances(
#         self, exchange: str = "kraken", account_id: str = None, limit: int = 30
#     ):
#         """Get recent balance snapshots"""
#         if account_id:
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, account_id, limit]
#         else:
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, limit]

#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 results = []
#                 for row in cur.fetchall():
#                     result = dict(row)
#                     results.append(result)
#                 return results

#     def list_accounts(self, exchange: str = "kraken"):
#         """List all accounts for an exchange"""
#         query = """
#             SELECT DISTINCT account_id, 
#                    MAX(snapshot_date) as last_snapshot,
#                    COUNT(*) as snapshot_count
#             FROM balance_snapshots
#             WHERE exchange = %s
#             GROUP BY account_id
#             ORDER BY last_snapshot DESC
#         """

#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, [exchange])
#                 return [dict(row) for row in cur.fetchall()]

# """Database operations"""

# import psycopg2
# from psycopg2.extras import RealDictCursor
# from contextlib import contextmanager
# import json
# from decimal import Decimal


# class Database:
#     def __init__(self, connection_string: str):
#         self.connection_string = connection_string

#     def _decimal_to_str(self, obj):
#         """Recursively convert Decimal → str for JSON safety"""
#         if isinstance(obj, Decimal):
#             return str(obj)
#         if isinstance(obj, dict):
#             return {k: self._decimal_to_str(v) for k, v in obj.items()}
#         if isinstance(obj, list):
#             return [self._decimal_to_str(v) for v in obj]
#         return obj

#     @contextmanager
#     def get_connection(self):
#         """Context manager for database connections"""
#         conn = psycopg2.connect(self.connection_string)
#         try:
#             yield conn
#             conn.commit()
#         except Exception:
#             conn.rollback()
#             raise
#         finally:
#             conn.close()

#     def create_returns_table(self):
#         """Create daily_returns table if it doesn't exist"""
#         query = """
#             CREATE TABLE IF NOT EXISTS daily_returns (
#                 id SERIAL PRIMARY KEY,
#                 exchange VARCHAR(50) NOT NULL,
#                 account_id VARCHAR(100) NOT NULL,
#                 return_date DATE NOT NULL,
#                 previous_date DATE NOT NULL,
#                 current_balance_usd NUMERIC(20,2) NOT NULL,
#                 previous_balance_usd NUMERIC(20,2) NOT NULL,
#                 daily_return_usd NUMERIC(20,2) NOT NULL,
#                 daily_return_pct NUMERIC(10,4) NOT NULL,
#                 timestamp TIMESTAMP NOT NULL,
#                 UNIQUE(exchange, account_id, return_date)
#             );
            
#             CREATE INDEX IF NOT EXISTS idx_returns_exchange_account 
#             ON daily_returns(exchange, account_id, return_date DESC);
#         """
        
#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(query)
        
#         print("Daily returns table created/verified")

#     def create_trades_table(self):
#         """Create trades table if it doesn't exist"""
#         query = """
#             CREATE TABLE IF NOT EXISTS trades (
#                 id SERIAL PRIMARY KEY,
#                 exchange VARCHAR(50) NOT NULL,
#                 account_id VARCHAR(100) NOT NULL,
#                 trade_id VARCHAR(100) NOT NULL,
#                 trade_timestamp TIMESTAMP NOT NULL,
#                 symbol VARCHAR(20) NOT NULL,
#                 side VARCHAR(10) NOT NULL,
#                 type VARCHAR(20),
#                 price NUMERIC(20,8) NOT NULL,
#                 amount NUMERIC(20,8) NOT NULL,
#                 cost NUMERIC(20,2) NOT NULL,
#                 fee_cost NUMERIC(20,8),
#                 fee_currency VARCHAR(10),
#                 raw_data JSONB,
#                 UNIQUE(exchange, account_id, trade_id)
#             );
            
#             CREATE INDEX IF NOT EXISTS idx_trades_exchange_account 
#             ON trades(exchange, account_id, trade_timestamp DESC);
            
#             CREATE INDEX IF NOT EXISTS idx_trades_symbol 
#             ON trades(symbol, trade_timestamp DESC);
#         """
        
#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(query)
        
#         print("Trades table created/verified")

#     def save_balance_snapshot(self, snapshot: dict):
#         """Save balance snapshot to database"""
#         query = """
#             INSERT INTO balance_snapshots (
#                 exchange, account_id, snapshot_date, timestamp,
#                 total_balance_usd, balances, raw_data
#             ) VALUES (
#                 %(exchange)s, %(account_id)s, %(snapshot_date)s, %(timestamp)s,
#                 %(total_balance_usd)s, %(balances)s, %(raw_data)s
#             )
#             ON CONFLICT (exchange, account_id, snapshot_date) 
#             DO UPDATE SET
#                 timestamp = EXCLUDED.timestamp,
#                 total_balance_usd = EXCLUDED.total_balance_usd,
#                 balances = EXCLUDED.balances,
#                 raw_data = EXCLUDED.raw_data
#         """

#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(
#                     query,
#                     {
#                         "exchange": snapshot["exchange"],
#                         "account_id": snapshot["account_id"],
#                         "snapshot_date": snapshot["timestamp"].date(),
#                         "timestamp": snapshot["timestamp"],
#                         "total_balance_usd": snapshot["total_balance_usd"],
#                         "balances": json.dumps(
#                             self._decimal_to_str(snapshot["balances"])
#                         ),
#                         "raw_data": json.dumps(
#                             self._decimal_to_str(snapshot.get("raw_data", {}))
#                         ),
#                     },
#                 )

#         print(
#             f"Saved balance snapshot for {snapshot['account_id']} on {snapshot['timestamp'].date()}"
#         )

#     def get_previous_balance(self, exchange: str, account_id: str, current_date):
#         """
#         Get the most recent balance snapshot before the given date
        
#         Args:
#             exchange: Exchange name (e.g., 'kraken')
#             account_id: Account identifier
#             current_date: The date to look before (datetime.date or datetime)
            
#         Returns:
#             Dict with balance snapshot data, or None if no previous snapshot exists
#         """
#         query = """
#             SELECT * FROM balance_snapshots
#             WHERE exchange = %s 
#             AND account_id = %s 
#             AND snapshot_date < %s
#             ORDER BY snapshot_date DESC
#             LIMIT 1
#         """
        
#         # Handle both datetime and date objects
#         if hasattr(current_date, 'date'):
#             current_date = current_date.date()
        
#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, [exchange, account_id, current_date])
#                 row = cur.fetchone()
#                 if row:
#                     return dict(row)
#                 return None

#     def save_daily_return(self, return_data: dict):
#         """
#         Save daily return record to database
        
#         Args:
#             return_data: Dict containing:
#                 - exchange
#                 - account_id
#                 - return_date
#                 - previous_date
#                 - current_balance_usd
#                 - previous_balance_usd
#                 - daily_return_usd
#                 - daily_return_pct
#                 - timestamp
#         """
#         query = """
#             INSERT INTO daily_returns (
#                 exchange, account_id, return_date, previous_date,
#                 current_balance_usd, previous_balance_usd,
#                 daily_return_usd, daily_return_pct, timestamp
#             ) VALUES (
#                 %(exchange)s, %(account_id)s, %(return_date)s, %(previous_date)s,
#                 %(current_balance_usd)s, %(previous_balance_usd)s,
#                 %(daily_return_usd)s, %(daily_return_pct)s, %(timestamp)s
#             )
#             ON CONFLICT (exchange, account_id, return_date)
#             DO UPDATE SET
#                 previous_date = EXCLUDED.previous_date,
#                 current_balance_usd = EXCLUDED.current_balance_usd,
#                 previous_balance_usd = EXCLUDED.previous_balance_usd,
#                 daily_return_usd = EXCLUDED.daily_return_usd,
#                 daily_return_pct = EXCLUDED.daily_return_pct,
#                 timestamp = EXCLUDED.timestamp
#         """
        
#         with self.get_connection() as conn:
#             with conn.cursor() as cur:
#                 cur.execute(query, return_data)
        
#         print(
#             f"Saved daily return for {return_data['account_id']} on {return_data['return_date']}: "
#             f"{return_data['daily_return_pct']:.2f}%"
#         )

#     def get_latest_return(self, exchange: str = "kraken", account_id: str = None):
#         """Get most recent daily return"""
#         if account_id:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY return_date DESC
#                 LIMIT 1
#             """
#             params = [exchange, account_id]
#         else:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s
#                 ORDER BY return_date DESC
#                 LIMIT 1
#             """
#             params = [exchange]
        
#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 row = cur.fetchone()
#                 if row:
#                     return dict(row)
#                 return None

#     def get_all_returns(
#         self, exchange: str = "kraken", account_id: str = None, limit: int = 100
#     ):
#         """Get historical daily returns"""
#         if account_id:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY return_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, account_id, limit]
#         else:
#             query = """
#                 SELECT * FROM daily_returns
#                 WHERE exchange = %s
#                 ORDER BY return_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, limit]
        
#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 results = []
#                 for row in cur.fetchall():
#                     result = dict(row)
#                     results.append(result)
#                 return results

#     def get_latest_balance(self, exchange: str = "kraken", account_id: str = None):
#         """Get most recent balance snapshot"""
#         if account_id:
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT 1
#             """
#             params = [exchange, account_id]
#         else:
#             # Get latest across all accounts for this exchange
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT 1
#             """
#             params = [exchange]

#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 row = cur.fetchone()
#                 if row:
#                     result = dict(row)
#                     return result
#                 return None

#     def get_all_balances(
#         self, exchange: str = "kraken", account_id: str = None, limit: int = 30
#     ):
#         """Get recent balance snapshots"""
#         if account_id:
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s AND account_id = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, account_id, limit]
#         else:
#             query = """
#                 SELECT * FROM balance_snapshots
#                 WHERE exchange = %s
#                 ORDER BY snapshot_date DESC
#                 LIMIT %s
#             """
#             params = [exchange, limit]

#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, params)
#                 results = []
#                 for row in cur.fetchall():
#                     result = dict(row)
#                     results.append(result)
#                 return results

#     def list_accounts(self, exchange: str = "kraken"):
#         """List all accounts for an exchange"""
#         query = """
#             SELECT DISTINCT account_id, 
#                    MAX(snapshot_date) as last_snapshot,
#                    COUNT(*) as snapshot_count
#             FROM balance_snapshots
#             WHERE exchange = %s
#             GROUP BY account_id
#             ORDER BY last_snapshot DESC
#         """

#         with self.get_connection() as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cur:
#                 cur.execute(query, [exchange])
#                 return [dict(row) for row in cur.fetchall()]

"""Database operations"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import json
from decimal import Decimal
from typing import List, Dict, Optional


class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _decimal_to_str(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._decimal_to_str(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._decimal_to_str(v) for v in obj]
        return obj

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_returns_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS daily_returns (
                id SERIAL PRIMARY KEY,
                exchange VARCHAR(50) NOT NULL,
                account_id VARCHAR(100) NOT NULL,
                return_date DATE NOT NULL,
                previous_date DATE NOT NULL,
                current_balance_usd NUMERIC(20,2) NOT NULL,
                previous_balance_usd NUMERIC(20,2) NOT NULL,
                daily_return_usd NUMERIC(20,2) NOT NULL,
                daily_return_pct NUMERIC(10,4) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                UNIQUE(exchange, account_id, return_date)
            );
            CREATE INDEX IF NOT EXISTS idx_returns_exchange_account 
            ON daily_returns(exchange, account_id, return_date DESC);
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
        print("Daily returns table created/verified")

    def create_trades_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                exchange VARCHAR(50) NOT NULL,
                account_id VARCHAR(100) NOT NULL,
                trade_id VARCHAR(100) NOT NULL,
                trade_timestamp TIMESTAMP NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL,
                type VARCHAR(20),
                price NUMERIC(20,8) NOT NULL,
                amount NUMERIC(20,8) NOT NULL,
                cost NUMERIC(20,2) NOT NULL,
                fee_cost NUMERIC(20,8),
                fee_currency VARCHAR(10),
                raw_data JSONB,
                UNIQUE(exchange, account_id, trade_id)
            );
            CREATE INDEX IF NOT EXISTS idx_trades_exchange_account 
            ON trades(exchange, account_id, trade_timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_trades_symbol 
            ON trades(symbol, trade_timestamp DESC);
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
        print("Trades table created/verified")

    def create_balance_snapshots_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS balance_snapshots (
                id SERIAL PRIMARY KEY,
                exchange VARCHAR(50) NOT NULL,
                account_id VARCHAR(100) NOT NULL,
                snapshot_date DATE NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                total_balance_usd NUMERIC(20,2) NOT NULL,
                balances JSONB,
                raw_data JSONB,
                UNIQUE(exchange, account_id, snapshot_date)
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_exchange_account 
            ON balance_snapshots(exchange, account_id, snapshot_date DESC);
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
        print("Balance snapshots table created/verified")

    def save_balance_snapshot(self, snapshot: dict):
        query = """
            INSERT INTO balance_snapshots (
                exchange, account_id, snapshot_date, timestamp,
                total_balance_usd, balances, raw_data
            ) VALUES (
                %(exchange)s, %(account_id)s, %(snapshot_date)s, %(timestamp)s,
                %(total_balance_usd)s, %(balances)s, %(raw_data)s
            )
            ON CONFLICT (exchange, account_id, snapshot_date) 
            DO UPDATE SET
                timestamp = EXCLUDED.timestamp,
                total_balance_usd = EXCLUDED.total_balance_usd,
                balances = EXCLUDED.balances,
                raw_data = EXCLUDED.raw_data
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    {
                        "exchange": snapshot["exchange"],
                        "account_id": snapshot["account_id"],
                        "snapshot_date": snapshot["timestamp"].date(),
                        "timestamp": snapshot["timestamp"],
                        "total_balance_usd": snapshot["total_balance_usd"],
                        "balances": json.dumps(self._decimal_to_str(snapshot["balances"])),
                        "raw_data": json.dumps(self._decimal_to_str(snapshot.get("raw_data", {}))),
                    },
                )
        print(f"Saved balance snapshot for {snapshot['account_id']} on {snapshot['timestamp'].date()}")

    def get_previous_balance(self, exchange: str, account_id: str, current_date):
        query = """
            SELECT * FROM balance_snapshots
            WHERE exchange = %s AND account_id = %s AND snapshot_date < %s
            ORDER BY snapshot_date DESC LIMIT 1
        """
        if hasattr(current_date, "date"):
            current_date = current_date.date()
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (exchange, account_id, current_date))
                row = cur.fetchone()
                return dict(row) if row else None

    def save_daily_return(self, return_data: dict):
        query = """
            INSERT INTO daily_returns (
                exchange, account_id, return_date, previous_date,
                current_balance_usd, previous_balance_usd,
                daily_return_usd, daily_return_pct, timestamp
            ) VALUES (
                %(exchange)s, %(account_id)s, %(return_date)s, %(previous_date)s,
                %(current_balance_usd)s, %(previous_balance_usd)s,
                %(daily_return_usd)s, %(daily_return_pct)s, %(timestamp)s
            )
            ON CONFLICT (exchange, account_id, return_date)
            DO UPDATE SET
                previous_date = EXCLUDED.previous_date,
                current_balance_usd = EXCLUDED.current_balance_usd,
                previous_balance_usd = EXCLUDED.previous_balance_usd,
                daily_return_usd = EXCLUDED.daily_return_usd,
                daily_return_pct = EXCLUDED.daily_return_pct,
                timestamp = EXCLUDED.timestamp
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, return_data)
        print(f"Saved daily return for {return_data['account_id']} on {return_data['return_date']}: {return_data['daily_return_pct']:.2f}%")

    def get_latest_return(self, exchange: str = "kraken", account_id: str = None):
        query = """
            SELECT * FROM daily_returns
            WHERE exchange = %s AND account_id = %s
            ORDER BY return_date DESC LIMIT 1
        """ if account_id else """
            SELECT * FROM daily_returns
            WHERE exchange = %s
            ORDER BY return_date DESC LIMIT 1
        """
        params = [exchange, account_id] if account_id else [exchange]
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return dict(row) if row else None

    def get_all_returns(self, exchange: str = "kraken", account_id: str = None, limit: int = 100):
        query = """
            SELECT * FROM daily_returns
            WHERE exchange = %s AND account_id = %s
            ORDER BY return_date DESC LIMIT %s
        """ if account_id else """
            SELECT * FROM daily_returns
            WHERE exchange = %s
            ORDER BY return_date DESC LIMIT %s
        """
        params = [exchange, account_id, limit] if account_id else [exchange, limit]
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def get_latest_balance(self, exchange: str = "kraken", account_id: str = None):
        query = """
            SELECT * FROM balance_snapshots
            WHERE exchange = %s AND account_id = %s
            ORDER BY snapshot_date DESC LIMIT 1
        """ if account_id else """
            SELECT * FROM balance_snapshots
            WHERE exchange = %s
            ORDER BY snapshot_date DESC LIMIT 1
        """
        params = [exchange, account_id] if account_id else [exchange]
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return dict(row) if row else None

    def get_all_balances(self, exchange: str = "kraken", account_id: str = None, limit: int = 30):
        query = """
            SELECT * FROM balance_snapshots
            WHERE exchange = %s AND account_id = %s
            ORDER BY snapshot_date DESC LIMIT %s
        """ if account_id else """
            SELECT * FROM balance_snapshots
            WHERE exchange = %s
            ORDER BY snapshot_date DESC LIMIT %s
        """
        params = [exchange, account_id, limit] if account_id else [exchange, limit]
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def list_accounts(self, exchange: str = "kraken"):
        query = """
            SELECT DISTINCT account_id, 
                   MAX(snapshot_date) as last_snapshot,
                   COUNT(*) as snapshot_count
            FROM balance_snapshots
            WHERE exchange = %s
            GROUP BY account_id
            ORDER BY last_snapshot DESC
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, [exchange])
                return [dict(row) for row in cur.fetchall()]

    def get_latest_trade_timestamp(self, exchange: str, account_id: str) -> Optional[int]:
        query = """
            SELECT trade_timestamp
            FROM trades
            WHERE exchange = %s AND account_id = %s
            ORDER BY trade_timestamp DESC
            LIMIT 1
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (exchange, account_id))
                row = cur.fetchone()
                if row:
                    return int(row[0].timestamp() * 1000)
                return None

    def save_trades(self, trades: List[Dict], exchange: str, account_id: str) -> int:
        if not trades:
            return 0

        query = """
            INSERT INTO trades (
                exchange, account_id, trade_id, trade_timestamp, symbol,
                side, type, price, amount, cost, fee_cost, fee_currency, raw_data
            ) VALUES (
                %(exchange)s, %(account_id)s, %(trade_id)s, %(trade_timestamp)s, %(symbol)s,
                %(side)s, %(type)s, %(price)s, %(amount)s, %(cost)s, %(fee_cost)s, %(fee_currency)s, %(raw_data)s
            )
            ON CONFLICT (exchange, account_id, trade_id) DO NOTHING
        """

        records = []
        for t in trades:
            fee = t.get("fee") or {}
            records.append({
                "exchange": exchange,
                "account_id": account_id,
                "trade_id": t["id"],
                "trade_timestamp": t["datetime"] if isinstance(t["datetime"], str) else t["timestamp"]/1000,
                "symbol": t["symbol"],
                "side": t["side"],
                "type": t.get("type"),
                "price": t["price"],
                "amount": t["amount"],
                "cost": t["cost"],
                "fee_cost": fee.get("cost"),
                "fee_currency": fee.get("currency"),
                "raw_data": json.dumps(t),
            })

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, query, records)
                inserted = cur.rowcount
        print(f"Inserted {inserted} new trades")
        return inserted
    
    def get_all_trades(self, exchange: str = "kraken", account_id: str = None, limit: int = 100):
        query = """
            SELECT * FROM trades
            WHERE exchange = %s
        """
        params = [exchange]
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        query += " ORDER BY trade_timestamp DESC LIMIT %s"
        params.append(limit)

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]