"""Command-line interface for trading analytics"""
import click
import config
from kraken import KrakenConnector
from database import Database

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
        config.KRAKEN_API_KEY,
        config.KRAKEN_API_SECRET,
        account_id
    )
    
    if connector.test_connection():
        click.echo("✅ Connection successful!")
    else:
        click.echo("❌ Connection failed!")

@cli.command()
def pull_balance():
    """Pull current balance from Kraken and save to database"""
    click.echo("Fetching balance from Kraken...")
    
    # Setup
    account_id = config.get_account_id(config.KRAKEN_API_KEY, config.ACCOUNT_ID)
    
    # Fetch from Kraken
    connector = KrakenConnector(
        config.KRAKEN_API_KEY,
        config.KRAKEN_API_SECRET,
        account_id
    )
    balance = connector.get_account_balance()
    
    click.echo(f"Account: {balance['account_id']}")
    click.echo(f"Total Balance: ${balance['total_balance_usd']:,.2f}")
    click.echo(f"Assets: {list(balance['balances'].keys())}")
    
    # Save to database
    click.echo("\nSaving to database...")
    db = Database(config.DATABASE_URL)
    db.save_balance_snapshot(balance)
    
    click.echo("✅ Done!")

@cli.command()
@click.option('--account', default=None, help='Specific account ID')
def show_balance(account):
    """Show latest balance from database"""
    db = Database(config.DATABASE_URL)
    balance = db.get_latest_balance('kraken', account)
    
    if not balance:
        click.echo("No balance data found in database")
        return
    
    click.echo(f"\n💰 Latest Balance")
    click.echo(f"Account: {balance['account_id']}")
    click.echo(f"Date: {balance['snapshot_date']}")
    click.echo(f"Total (USD): ${balance['total_balance_usd']:,.2f}\n")
    click.echo("Asset Breakdown:")
    
    for asset, amount in balance['balances'].items():
        click.echo(f"  {asset}: {amount:,.8f}")

@cli.command()
@click.option('--limit', default=10, help='Number of records to show')
@click.option('--account', default=None, help='Specific account ID')
def history(limit, account):
    """Show balance history"""
    db = Database(config.DATABASE_URL)
    balances = db.get_all_balances('kraken', account, limit)
    
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
def list_accounts():
    """List all tracked accounts"""
    db = Database(config.DATABASE_URL)
    accounts = db.list_accounts('kraken')
    
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

if __name__ == '__main__':
    cli()