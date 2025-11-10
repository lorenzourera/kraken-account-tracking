"""Database operations"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import json

class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
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
                cur.execute(query, {
                    'exchange': snapshot['exchange'],
                    'account_id': snapshot['account_id'],  # NEW
                    'snapshot_date': snapshot['timestamp'].date(),
                    'timestamp': snapshot['timestamp'],
                    'total_balance_usd': snapshot['total_balance_usd'],
                    'balances': json.dumps(snapshot['balances']),
                    'raw_data': json.dumps(snapshot.get('raw_data', {}))
                })
        
        print(f"✅ Saved balance snapshot for {snapshot['account_id']} on {snapshot['timestamp'].date()}")
    
    def get_latest_balance(self, exchange: str = 'kraken', account_id: str = None):
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
    
    def get_all_balances(self, exchange: str = 'kraken', account_id: str = None, limit: int = 30):
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
                    result['balances'] = json.loads(result['balances'])
                    results.append(result)
                return results
    
    def list_accounts(self, exchange: str = 'kraken'):
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