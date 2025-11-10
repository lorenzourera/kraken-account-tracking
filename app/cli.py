"""Command-line interface for trading analytics"""

import click
import config
from kraken import KrakenConnector
from database import Database
from main import calculate_and_save_return


@click.group()
def cli():
    """Trading Analytics CLI"""
    pass


@cli.command()
def test_connection():
    """Test Kraken API connection"""
    click.echo("Testing Kraken connection...")

    account_id = config.get_account_id(config.KRAKEN_API_KEY, config.ACCOUNT_ID)
    click.echo(f"Account ID: {account_id}")

    connector = KrakenConnector(
        config.KRAKEN_API_KEY, config.KRAKEN_API_SECRET, account_id
    )

    if connector.test_connection():
        click.echo("✅ Connection successful!")
    else:
        click.echo("❌ Connection failed!")


@cli.command()
def pull_balance():
    """Pull current balance from Kraken, save to database, and calculate returns"""
    click.echo("Fetching balance from Kraken...")

    # Setup
    account_id = config.get_account_id(config.KRAKEN_API_KEY, config.ACCOUNT_ID)

    # Fetch from Kraken
    connector = KrakenConnector(
        config.KRAKEN_API_KEY, config.KRAKEN_API_SECRET, account_id
    )
    balance = connector.get_account_balance()

    click.echo(f"Account: {balance['account_id']}")
    click.echo(f"Total Balance: ${balance['total_balance_usd']:,.2f}")
    click.echo(f"Assets: {list(balance['balances'].keys())}")

    # Save to database
    click.echo("\nSaving to database...")
    db = Database(config.DATABASE_URL)
    
    # Ensure returns table exists
    db.create_returns_table()
    
    db.save_balance_snapshot(balance)
    
    # Calculate and save returns
    click.echo("Calculating returns...")
    try:
        calculate_and_save_return(db, balance)
    except Exception as e:
        click.echo(f"⚠️  Returns calculation skipped: {e}")

    click.echo("✅ Done!")


@cli.command()
@click.option("--account", default=None, help="Specific account ID")
def show_balance(account):
    """Show latest balance from database"""
    db = Database(config.DATABASE_URL)
    balance = db.get_latest_balance("kraken", account)

    if not balance:
        click.echo("No balance data found in database")
        return

    click.echo(f"\n💰 Latest Balance")
    click.echo(f"Account: {balance['account_id']}")
    click.echo(f"Date: {balance['snapshot_date']}")
    click.echo(f"Total (USD): ${balance['total_balance_usd']:,.2f}\n")
    
    # Parse balances (handle both dict and JSON string)
    import json
    balances_raw = balance["balances"]
    if isinstance(balances_raw, str):
        balances_dict = json.loads(balances_raw)
    else:
        balances_dict = balances_raw
    
    click.echo("Asset Breakdown:")
    for asset, data in balances_dict.items():
        amount = data.get("amount", 0)
        usd_value = data.get("usd_value", 0)
        click.echo(f"  {asset}: {float(amount):,.8f} (${float(usd_value):,.2f})")


@cli.command()
@click.option("--limit", default=10, help="Number of records to show")
@click.option("--account", default=None, help="Specific account ID")
def history(limit, account):
    """Show balance history"""
    db = Database(config.DATABASE_URL)
    balances = db.get_all_balances("kraken", account, limit)

    if not balances:
        click.echo("No balance history found")
        return

    click.echo(f"\n📊 Balance History (Last {len(balances)} snapshots)")
    if account:
        click.echo(f"Account: {account}")
    click.echo()
    click.echo(f"{'Date':<12} {'Account':<15} {'Total USD':>15}")
    click.echo("-" * 45)

    for balance in balances:
        click.echo(
            f"{str(balance['snapshot_date']):<12} "
            f"{balance['account_id']:<15} "
            f"${balance['total_balance_usd']:>14,.2f}"
        )


@cli.command()
@click.option("--limit", default=10, help="Number of records to show")
@click.option("--account", default=None, help="Specific account ID")
def show_returns(limit, account):
    """Show recent daily returns"""
    db = Database(config.DATABASE_URL)
    returns = db.get_all_returns("kraken", account, limit)

    if not returns:
        click.echo("No returns data found. Run 'pull_balance' to generate returns.")
        return

    click.echo(f"\n📈 Daily Returns (Last {len(returns)} days)")
    if account:
        click.echo(f"Account: {account}")
    click.echo()
    click.echo(f"{'Date':<12} {'Prev Date':<12} {'Return USD':>15} {'Return %':>10}")
    click.echo("-" * 52)

    total_return_usd = 0
    for ret in returns:
        return_usd = float(ret['daily_return_usd'])
        return_pct = float(ret['daily_return_pct'])
        total_return_usd += return_usd
        
        symbol = "+" if return_usd >= 0 else ""
        click.echo(
            f"{str(ret['return_date']):<12} "
            f"{str(ret['previous_date']):<12} "
            f"{symbol}${return_usd:>13,.2f} "
            f"{symbol}{return_pct:>8,.2f}%"
        )
    
    click.echo("-" * 52)
    avg_return = total_return_usd / len(returns) if returns else 0
    click.echo(f"{'Total:':<25} ${total_return_usd:>14,.2f}")
    click.echo(f"{'Average:':<25} ${avg_return:>14,.2f}")


@cli.command()
@click.option("--account", default=None, help="Specific account ID")
def latest_return(account):
    """Show latest daily return"""
    db = Database(config.DATABASE_URL)
    ret = db.get_latest_return("kraken", account)

    if not ret:
        click.echo("No returns data found. Run 'pull_balance' to generate returns.")
        return

    return_usd = float(ret['daily_return_usd'])
    return_pct = float(ret['daily_return_pct'])
    
    symbol = "📈" if return_usd >= 0 else "📉"
    sign = "+" if return_usd >= 0 else ""
    
    click.echo(f"\n{symbol} Latest Return")
    click.echo(f"Account: {ret['account_id']}")
    click.echo(f"Return Date: {ret['return_date']}")
    click.echo(f"Previous Date: {ret['previous_date']}")
    click.echo(f"Current Balance: ${float(ret['current_balance_usd']):,.2f}")
    click.echo(f"Previous Balance: ${float(ret['previous_balance_usd']):,.2f}")
    click.echo(f"Change: {sign}${return_usd:,.2f} ({sign}{return_pct:.2f}%)")


@cli.command()
def list_accounts():
    """List all tracked accounts"""
    db = Database(config.DATABASE_URL)
    accounts = db.list_accounts("kraken")

    if not accounts:
        click.echo("No accounts found")
        return

    click.echo("\n📋 Tracked Accounts\n")
    click.echo(f"{'Account ID':<20} {'Last Snapshot':<15} {'# Snapshots':>12}")
    click.echo("-" * 50)

    for account in accounts:
        click.echo(
            f"{account['account_id']:<20} "
            f"{str(account['last_snapshot']):<15} "
            f"{account['snapshot_count']:>12}"
        )


if __name__ == "__main__":
    cli()