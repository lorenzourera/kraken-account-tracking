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


class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _decimal_to_str(self, obj):
        """Recursively convert Decimal → str for JSON safety"""
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._decimal_to_str(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._decimal_to_str(v) for v in obj]
        return obj

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
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
        """Create daily_returns table if it doesn't exist"""
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

    def save_balance_snapshot(self, snapshot: dict):
        """Save balance snapshot to database"""
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
                        "balances": json.dumps(
                            self._decimal_to_str(snapshot["balances"])
                        ),
                        "raw_data": json.dumps(
                            self._decimal_to_str(snapshot.get("raw_data", {}))
                        ),
                    },
                )

        print(
            f"Saved balance snapshot for {snapshot['account_id']} on {snapshot['timestamp'].date()}"
        )

    def get_previous_balance(self, exchange: str, account_id: str, current_date):
        """
        Get the most recent balance snapshot before the given date
        
        Args:
            exchange: Exchange name (e.g., 'kraken')
            account_id: Account identifier
            current_date: The date to look before (datetime.date or datetime)
            
        Returns:
            Dict with balance snapshot data, or None if no previous snapshot exists
        """
        query = """
            SELECT * FROM balance_snapshots
            WHERE exchange = %s 
            AND account_id = %s 
            AND snapshot_date < %s
            ORDER BY snapshot_date DESC
            LIMIT 1
        """
        
        # Handle both datetime and date objects
        if hasattr(current_date, 'date'):
            current_date = current_date.date()
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, [exchange, account_id, current_date])
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None

    def save_daily_return(self, return_data: dict):
        """
        Save daily return record to database
        
        Args:
            return_data: Dict containing:
                - exchange
                - account_id
                - return_date
                - previous_date
                - current_balance_usd
                - previous_balance_usd
                - daily_return_usd
                - daily_return_pct
                - timestamp
        """
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
        
        print(
            f"Saved daily return for {return_data['account_id']} on {return_data['return_date']}: "
            f"{return_data['daily_return_pct']:.2f}%"
        )

    def get_latest_return(self, exchange: str = "kraken", account_id: str = None):
        """Get most recent daily return"""
        if account_id:
            query = """
                SELECT * FROM daily_returns
                WHERE exchange = %s AND account_id = %s
                ORDER BY return_date DESC
                LIMIT 1
            """
            params = [exchange, account_id]
        else:
            query = """
                SELECT * FROM daily_returns
                WHERE exchange = %s
                ORDER BY return_date DESC
                LIMIT 1
            """
            params = [exchange]
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None

    def get_all_returns(
        self, exchange: str = "kraken", account_id: str = None, limit: int = 100
    ):
        """Get historical daily returns"""
        if account_id:
            query = """
                SELECT * FROM daily_returns
                WHERE exchange = %s AND account_id = %s
                ORDER BY return_date DESC
                LIMIT %s
            """
            params = [exchange, account_id, limit]
        else:
            query = """
                SELECT * FROM daily_returns
                WHERE exchange = %s
                ORDER BY return_date DESC
                LIMIT %s
            """
            params = [exchange, limit]
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = []
                for row in cur.fetchall():
                    result = dict(row)
                    results.append(result)
                return results

    def get_latest_balance(self, exchange: str = "kraken", account_id: str = None):
        """Get most recent balance snapshot"""
        if account_id:
            query = """
                SELECT * FROM balance_snapshots
                WHERE exchange = %s AND account_id = %s
                ORDER BY snapshot_date DESC
                LIMIT 1
            """
            params = [exchange, account_id]
        else:
            # Get latest across all accounts for this exchange
            query = """
                SELECT * FROM balance_snapshots
                WHERE exchange = %s
                ORDER BY snapshot_date DESC
                LIMIT 1
            """
            params = [exchange]

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    return result
                return None

    def get_all_balances(
        self, exchange: str = "kraken", account_id: str = None, limit: int = 30
    ):
        """Get recent balance snapshots"""
        if account_id:
            query = """
                SELECT * FROM balance_snapshots
                WHERE exchange = %s AND account_id = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
            """
            params = [exchange, account_id, limit]
        else:
            query = """
                SELECT * FROM balance_snapshots
                WHERE exchange = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
            """
            params = [exchange, limit]

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = []
                for row in cur.fetchall():
                    result = dict(row)
                    results.append(result)
                return results

    def list_accounts(self, exchange: str = "kraken"):
        """List all accounts for an exchange"""
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