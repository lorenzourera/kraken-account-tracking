set -euo pipefail

timestamp() {
    date '+%Y-%m-%d %H:%M:%S %Z'
}

echo "[$(timestamp)] Starting Kraken Account Tracking"

# Verify/create ALL tables via database.py
echo "[$(timestamp)] Verifying database schema via database.py..."
uv run python -c "
from database import Database
from config import DATABASE_URL
db = Database(DATABASE_URL)
db.create_balance_snapshots_table()
db.create_returns_table()
db.create_trades_table()
print('All tables verified/created. schema LOCKED')
"

# Run initial data pull (first deploy or after nuke)
echo "[$(timestamp)] Running initial data pull..."
if uv run main.py >> /var/log/cron.log 2>&1; then
    echo "[$(timestamp)] Initial pull: SUCCESS"
else
    echo "[$(timestamp)] Initial pull: FAILED — will retry daily at 12:05 AM PH"
fi

# Start cron daemon in the background
echo "[$(timestamp)] Starting cron daemon..."
cron
sleep 1

# Verify cron is running
if ps aux | grep -q '[c]ron'; then
    echo "[$(timestamp)] ✓ Cron daemon confirmed running"
else
    echo "[$(timestamp)] ✗ WARNING: Cron daemon failed to start!"
fi

# Start Telegram bot — FOREVER (PID 1)
echo "[$(timestamp)] Starting Portfolio Tracking Telegram Bot — running 24/7 from PH soil..."
exec uv run telegram_bot.py