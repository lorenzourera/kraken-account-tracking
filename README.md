# Kraken Account Tracking

A comprehensive portfolio tracking system for Kraken exchange accounts that monitors balances, calculates daily returns, tracks trades, and provides a Telegram bot interface for real-time portfolio insights.

## Overview

This application automatically pulls your Kraken account data daily, stores historical snapshots in a PostgreSQL database, calculates performance metrics, and provides an easy-to-use Telegram bot interface for querying your portfolio on the go. Built for traders and investors who want to track their Kraken account performance over time without manual data entry.

**Key Features:**
- 🔄 Automated daily balance snapshots via cron
- 📊 Daily return calculations (USD and percentage)
- 💱 Trade history tracking and storage
- 🤖 Telegram bot interface for remote access
- 📈 CSV export functionality for external analysis
- 🐳 Fully Dockerized with PostgreSQL database
- 🌏 Timezone-aware (Asia/Manila by default)

## Functionality

### Core Components

#### 1. Balance Tracking (`app/kraken.py`)
- Connects to Kraken API using CCXT library
- Fetches current account balances for all assets
- Converts all holdings to USD equivalent values
- Handles both spot and futures positions
- Supports USD-equivalent stablecoins (USDT, USDC)

#### 2. Database Operations (`app/database.py`)
Manages three primary tables:

**`balance_snapshots`**
- Stores daily portfolio snapshots
- Tracks total balance and individual asset holdings
- Indexed for fast querying by date and account

**`daily_returns`**
- Calculates and stores day-over-day portfolio changes
- Records both absolute (USD) and percentage returns
- Links current snapshot to previous day for context

**`trades`**
- Stores complete trade history from Kraken
- Includes price, amount, fees, and metadata
- Prevents duplicate entries via unique constraints

#### 3. Daily Snapshot Job (`app/main.py`)
Runs automatically at 12:05 AM Manila time (00:05 UTC+8) via cron:
1. Fetches current account balance
2. Saves snapshot to database
3. Calculates returns vs previous day
4. Syncs new trades since last pull
5. Logs all operations

#### 4. Telegram Bot (`app/telegram_bot.py`)
Provides remote access via Telegram commands:

| Command | Description |
|---------|-------------|
| `/start` | Display welcome message and command list |
| `/pull` | Manually trigger data fetch from Kraken |
| `/balance` | Show latest portfolio balance with asset breakdown |
| `/returns` | Display recent daily returns |
| `/trades [limit]` | Show recent trades (default: 20) |
| `/export [limit]` | Export balance history as CSV |
| `/export_returns [limit]` | Export returns data as CSV |
| `/export_trades [limit]` | Export trade history as CSV |

#### 5. CLI Tool (`app/cli.py`)
Command-line interface for local/SSH access:
```bash
uv run cli.py test_connection  # Test Kraken API
uv run cli.py pull_balance      # Manual data pull
uv run cli.py show_balance      # Display latest balance
uv run cli.py history --limit 30 # View balance history
uv run cli.py show_returns --limit 10 # View returns
uv run cli.py latest_return     # Show most recent return
uv run cli.py list_accounts     # List tracked accounts
```

## Deployment

### Prerequisites
- Docker and Docker Compose installed
- Kraken API credentials (API key + secret)
- Telegram bot token (from @BotFather)
- Your Telegram user ID

### Environment Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd kraken-account-tracking
```

2. **Create `.env` file** in the project root:
```env
# Database Configuration
POSTGRES_DB_NAME=kraken_tracking
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:your_secure_password_here@db:5432/kraken_tracking

# Kraken API Credentials
KRAKEN_MAIN_API_KEY=your_kraken_api_key
KRAKEN_MAIN_API_SECRET=your_kraken_api_secret

# Optional: Custom account identifier (default: last 8 chars of API key)
ACCOUNT_ID=main_account

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ALLOWED_USER_IDS=your_telegram_user_id
```

3. **Generate Kraken API credentials**
   - Log into Kraken.com
   - Navigate to Settings → API
   - Create new API key with permissions:
     - Query Funds
     - Query Open Orders & Trades
     - Query Closed Orders & Trades
   - **Important:** Do NOT grant withdrawal or trading permissions

4. **Create Telegram bot**
   - Message @BotFather on Telegram
   - Send `/newbot` and follow prompts
   - Save the bot token to `.env`
   - Get your user ID from @userinfobot
   - Add your user ID to `ALLOWED_USER_IDS` (comma-separated for multiple users)

### Launch Application
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f tracker

# Check database status
docker-compose ps
```

The application will:
1. Start PostgreSQL database
2. Create necessary tables
3. Run initial data pull
4. Start Telegram bot
5. Schedule daily cron job for 12:05 AM Manila time

### Verify Deployment
```bash
# Check if bot is running
docker-compose logs tracker | grep "Bot handlers registered"

# Verify cron job
docker exec kraken-account-tracking crontab -l

# Test database connection
docker exec kraken-account-tracking-postgres psql -U postgres -d kraken_tracking -c "\dt"

# Send /start to your Telegram bot
```

## How to Make Certain Changes

### Change Scheduled Pull Time

The cron job is defined in the `Dockerfile`. Current schedule: `5 0 * * *` (12:05 AM Manila time)

**To modify:**
1. Edit `Dockerfile` line with `RUN echo "5 0 * * *..."`
2. Change cron expression (format: `minute hour day month weekday`)
3. Examples:
   - `0 12 * * *` → Daily at 12:00 PM
   - `0 */6 * * *` → Every 6 hours
   - `0 0,12 * * *` → 12:00 AM and 12:00 PM
4. Rebuild container: `docker-compose up -d --build`

### Change Timezone

Current timezone: `Asia/Manila` (UTC+8)

**To modify:**
1. Edit `Dockerfile` line: `ENV TZ=Asia/Manila`
2. Replace with your timezone (e.g., `America/New_York`, `Europe/London`)
3. Rebuild: `docker-compose up -d --build`

### Track Multiple Accounts

**Option 1: Multiple API Keys (Recommended)**
1. Add environment variables in `.env`:
```env
KRAKEN_ACCOUNT1_API_KEY=key1
KRAKEN_ACCOUNT1_API_SECRET=secret1
ACCOUNT1_ID=trading_account

KRAKEN_ACCOUNT2_API_KEY=key2
KRAKEN_ACCOUNT2_API_SECRET=secret2
ACCOUNT2_ID=hodl_account
```

2. Modify `app/main.py` to loop through accounts:
```python
accounts = [
    (os.getenv('KRAKEN_ACCOUNT1_API_KEY'), os.getenv('KRAKEN_ACCOUNT1_API_SECRET'), 'trading_account'),
    (os.getenv('KRAKEN_ACCOUNT2_API_KEY'), os.getenv('KRAKEN_ACCOUNT2_API_SECRET'), 'hodl_account'),
]

for api_key, api_secret, account_id in accounts:
    connector = KrakenConnector(api_key, api_secret, account_id)
    # ... rest of logic
```

**Option 2: Use ACCOUNT_ID**
- Set different `ACCOUNT_ID` values for different runs
- Data will be stored separately by account_id in the database

### Add New Telegram Commands

1. **Define command handler** in `app/telegram_bot.py`:
```python
async def my_new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "my_command")
    
    if not is_authorized(user.id):
        return
    
    # Your logic here
    await update.message.reply_text("Response text")
```

2. **Register handler** in `main()` function:
```python
app.add_handler(CommandHandler("my_command", my_new_command))
```

3. Restart container: `docker-compose restart tracker`

### Customize Return Calculation Logic

Edit `app/main.py` → `calculate_and_save_return()` function:
```python
def calculate_and_save_return(db: Database, current_snapshot: dict):
    # Current logic uses simple day-over-day comparison
    # Modify to use:
    # - Week-over-week: change get_previous_balance query
    # - Benchmark comparison: fetch external data and compare
    # - Risk-adjusted returns: add volatility calculations
    pass
```

### Export Data to External Systems

**Option 1: Direct Database Access**
```bash
# Connect to PostgreSQL
docker exec -it kraken-account-tracking-postgres psql -U postgres -d kraken_tracking

# Export to CSV
docker exec kraken-account-tracking-postgres psql -U postgres -d kraken_tracking \
  -c "COPY balance_snapshots TO STDOUT WITH CSV HEADER" > balances.csv
```

**Option 2: Use Telegram Export Commands**
- `/export` → Balance snapshots
- `/export_returns` → Daily returns
- `/export_trades` → Trade history

**Option 3: Add Custom Export**
Extend `app/database.py` with new query methods:
```python
def get_monthly_summary(self, exchange: str = "kraken"):
    query = """
        SELECT DATE_TRUNC('month', snapshot_date) as month,
               AVG(total_balance_usd) as avg_balance,
               MAX(total_balance_usd) as max_balance
        FROM balance_snapshots
        WHERE exchange = %s
        GROUP BY month
        ORDER BY month DESC
    """
    # ... implementation
```

### Change Database Retention Period

Add cleanup job to `app/main.py`:
```python
def cleanup_old_data(db: Database, days_to_keep: int = 365):
    """Remove snapshots older than specified days"""
    query = """
        DELETE FROM balance_snapshots 
        WHERE snapshot_date < CURRENT_DATE - INTERVAL '%s days'
    """
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, [days_to_keep])
```

Call in `run_daily_snapshot()` after saving data.

### Update Dependencies
```bash
# Update specific package
docker exec kraken-account-tracking uv add package_name@latest

# Update all packages
docker exec kraken-account-tracking uv lock --upgrade

# Rebuild container with new dependencies
docker-compose up -d --build
```

### Enable Debug Logging

Edit `app/telegram_bot.py` and `app/main.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ...
)

# Re-enable HTTP library logging
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("telegram").setLevel(logging.DEBUG)
```

Restart: `docker-compose restart tracker`

### Backup and Restore Database

**Backup:**
```bash
# Create backup
docker exec kraken-account-tracking-postgres pg_dump -U postgres kraken_tracking > backup_$(date +%Y%m%d).sql

# Or use the included dump
docker exec kraken-account-tracking-postgres pg_dump -U postgres kraken_tracking > db_dump.sql
```

**Restore:**
```bash
# Restore from backup
docker exec -i kraken-account-tracking-postgres psql -U postgres kraken_tracking < backup_20240101.sql
```

### Monitor Application Health

**Check logs:**
```bash
# Tracker logs
docker-compose logs -f tracker

# Database logs
docker-compose logs -f db

# Cron logs specifically
docker exec kraken-account-tracking tail -f /var/log/cron.log
```

**Database queries for health:**
```sql
-- Check latest snapshot
SELECT * FROM balance_snapshots ORDER BY snapshot_date DESC LIMIT 1;

-- Check data freshness
SELECT MAX(snapshot_date) as last_snapshot, 
       CURRENT_DATE - MAX(snapshot_date) as days_old
FROM balance_snapshots;

-- Count records
SELECT 
    (SELECT COUNT(*) FROM balance_snapshots) as snapshots,
    (SELECT COUNT(*) FROM daily_returns) as returns,
    (SELECT COUNT(*) FROM trades) as trades;
```

## Troubleshooting

**Bot not responding:**
1. Check if container is running: `docker-compose ps`
2. View logs: `docker-compose logs tracker`
3. Verify Telegram token in `.env`
4. Confirm user ID in `ALLOWED_USER_IDS`

**Cron job not running:**
1. Check cron logs: `docker exec kraken-account-tracking cat /var/log/cron.log`
2. Verify crontab: `docker exec kraken-account-tracking crontab -l`
3. Check timezone: `docker exec kraken-account-tracking date`

**API errors:**
1. Verify API key permissions on Kraken.com
2. Check rate limits (Kraken: 15 requests/sec for public, 1/sec for private)
3. Review logs: `docker-compose logs tracker | grep -i error`

**Database connection issues:**
1. Check database health: `docker-compose ps db`
2. Verify DATABASE_URL in `.env`
3. Test connection: `docker exec kraken-account-tracking-postgres pg_isready`

## Security Considerations

- **Never commit `.env` file** to version control
- Store API keys with **read-only** permissions (no trading/withdrawal)
- Restrict Telegram bot access via `ALLOWED_USER_IDS`
- Use strong `DB_PASSWORD` in production
- Consider enabling Kraken IP whitelist for API keys
- Regularly rotate API credentials
- Keep Docker images updated for security patches

## License

MIT License - Feel free to modify and distribute.

## Contributing

Contributions welcome! Please open an issue or pull request for:
- Bug fixes
- New features
- Documentation improvements
- Performance optimizations

## Support

For issues or questions:
1. Check logs first
2. Review troubleshooting section
3. Open GitHub issue with logs and error details


For custom development projects, paid engagements, or business inquires, reach me at telegram @zo125

---

**Built with:** Python 3.11 • CCXT • PostgreSQL • python-telegram-bot • Docker • uv