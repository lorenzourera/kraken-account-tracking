# import logging
# from config import DATABASE_URL, KRAKEN_API_KEY, KRAKEN_API_SECRET, ACCOUNT_ID
# from kraken import KrakenConnector
# from database import Database
# from decimal import Decimal
# import config as cfg

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# def calculate_and_save_return(db: Database, current_snapshot: dict):
#     """
#     Calculate and save daily return based on current and previous snapshots

#     Args:
#         db: Database instance
#         current_snapshot: The snapshot just saved
#     """
#     exchange = current_snapshot["exchange"]
#     account_id = current_snapshot["account_id"]
#     current_date = current_snapshot["timestamp"].date()
#     current_balance = Decimal(str(current_snapshot["total_balance_usd"]))

#     # Get previous snapshot
#     previous_snapshot = db.get_previous_balance(exchange, account_id, current_date)

#     if not previous_snapshot:
#         logger.info("No previous snapshot found - skipping return calculation (first day)")
#         return

#     previous_balance = Decimal(str(previous_snapshot["total_balance_usd"]))
#     previous_date = previous_snapshot["snapshot_date"]

#     # Calculate returns
#     daily_return_usd = current_balance - previous_balance

#     # Avoid division by zero
#     if previous_balance == 0:
#         logger.warning("Previous balance is zero - cannot calculate percentage return")
#         daily_return_pct = Decimal("0")
#     else:
#         daily_return_pct = (daily_return_usd / previous_balance) * Decimal("100")

#     # Prepare return data
#     return_data = {
#         "exchange": exchange,
#         "account_id": account_id,
#         "return_date": current_date,
#         "previous_date": previous_date,
#         "current_balance_usd": float(current_balance),
#         "previous_balance_usd": float(previous_balance),
#         "daily_return_usd": float(daily_return_usd),
#         "daily_return_pct": float(daily_return_pct),
#         "timestamp": current_snapshot["timestamp"]
#     }

#     # Save to database
#     db.save_daily_return(return_data)

#     logger.info(
#         f"Return calculated: ${daily_return_usd:,.2f} ({daily_return_pct:.2f}%) "
#         f"vs {previous_date}"
#     )


# def run_daily_snapshot():
#     logger.info("Starting daily Kraken balance snapshot...")
#     account_id = cfg.get_account_id(KRAKEN_API_KEY, ACCOUNT_ID)
#     connector = KrakenConnector(KRAKEN_API_KEY, KRAKEN_API_SECRET, account_id)

#     try:
#         # Fetch and save balance
#         balance = connector.get_account_balance()
#         db = Database(DATABASE_URL)

#         # Ensure returns table exists
#         db.create_returns_table()

#         # Save balance snapshot
#         db.save_balance_snapshot(balance)
#         logger.info(f"SUCCESS: Saved balance ${balance['total_balance_usd']:,.2f}")

#         # Calculate and save daily return
#         calculate_and_save_return(db, balance)

#     except Exception as e:
#         logger.error(f"FAILED: {e}")
#         raise


# if __name__ == "__main__":
#     run_daily_snapshot()

import logging
from config import DATABASE_URL, KRAKEN_API_KEY, KRAKEN_API_SECRET, ACCOUNT_ID
from kraken import KrakenConnector
from database import Database
from decimal import Decimal
import config as cfg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_and_save_return(db: Database, current_snapshot: dict):
    """
    Calculate and save daily return based on current and previous snapshots

    Args:
        db: Database instance
        current_snapshot: The snapshot just saved
    """
    exchange = current_snapshot["exchange"]
    account_id = current_snapshot["account_id"]
    current_date = current_snapshot["timestamp"].date()
    current_balance = Decimal(str(current_snapshot["total_balance_usd"]))

    # Get previous snapshot
    previous_snapshot = db.get_previous_balance(exchange, account_id, current_date)

    if not previous_snapshot:
        logger.info(
            "No previous snapshot found - skipping return calculation (first day)"
        )
        return

    previous_balance = Decimal(str(previous_snapshot["total_balance_usd"]))
    previous_date = previous_snapshot["snapshot_date"]

    # Calculate returns
    daily_return_usd = current_balance - previous_balance

    # Avoid division by zero
    if previous_balance == 0:
        logger.warning("Previous balance is zero - cannot calculate percentage return")
        daily_return_pct = Decimal("0")
    else:
        daily_return_pct = (daily_return_usd / previous_balance) * Decimal("100")

    # Prepare return data
    return_data = {
        "exchange": exchange,
        "account_id": account_id,
        "return_date": current_date,
        "previous_date": previous_date,
        "current_balance_usd": float(current_balance),
        "previous_balance_usd": float(previous_balance),
        "daily_return_usd": float(daily_return_usd),
        "daily_return_pct": float(daily_return_pct),
        "timestamp": current_snapshot["timestamp"],
    }

    # Save to database
    db.save_daily_return(return_data)

    logger.info(
        f"Return calculated: ${daily_return_usd:,.2f} ({daily_return_pct:.2f}%) "
        f"vs {previous_date}"
    )


def run_daily_snapshot():
    logger.info("Starting daily Kraken balance snapshot...")
    account_id = cfg.get_account_id(KRAKEN_API_KEY, ACCOUNT_ID)
    connector = KrakenConnector(KRAKEN_API_KEY, KRAKEN_API_SECRET, account_id)

    try:
        # Fetch and save balance
        balance = connector.get_account_balance()
        db = Database(DATABASE_URL)

        # Ensure tables exist
        db.create_returns_table()
        db.create_trades_table()

        # Save balance snapshot
        db.save_balance_snapshot(balance)
        logger.info(f"SUCCESS: Saved balance ${balance['total_balance_usd']:,.2f}")

        # Calculate and save daily return
        calculate_and_save_return(db, balance)

        # Fetch and save trades
        logger.info("Fetching trades...")
        latest_trade_ts = db.get_latest_trade_timestamp("kraken", account_id)

        if latest_trade_ts:
            logger.info(f"Fetching trades since timestamp: {latest_trade_ts}")
            # Fetch only new trades since last saved trade
            trades = connector.get_trades(since=latest_trade_ts, limit=500)
        else:
            logger.info("First trade pull - fetching all available trades")
            # First pull - get all trades (use reasonable limit)
            trades = connector.get_trades(limit=1000)

        if trades:
            new_trades_count = db.save_trades(trades, "kraken", account_id)
            logger.info(f"Trade sync complete: {new_trades_count} new trades saved")
        else:
            logger.info("No new trades found")

    except Exception as e:
        logger.error(f"FAILED: {e}")
        raise


if __name__ == "__main__":
    run_daily_snapshot()
