set -euo pipefail

echo "[$$(date -u)] Starting Kraken Account Tracking"

# Start cron daemon (daily pull at 8:05 AM PH = 00:05 UTC+8)
echo "[$$(date -u)] Starting cron daemon..."
service cron start || cron
tail -f /var/log/cron.log &

# Verify/create ALL tables via database.py
echo "[$$(date -u)] Verifying database schema via database.py..."
uv run python -c "
from database import Database
from decouple import config
db = Database(config('DATABASE_URL'))
db.create_balance_snapshots_table()
db.create_returns_table()
db.create_trades_table()
print('All tables verified/created. schema LOCKED')
"

# Run initial data pull (first deploy or after nuke)
echo "[$$(date -u)] Running initial data pull..."
if uv run main.py >> /var/log/cron.log 2>&1; then
    echo "[$$(date -u)] Initial pull: SUCCESS"
else
    echo "[$$(date -u)] Initial pull: FAILED — will retry daily at 8:05 AM PH"
fi

# Start Telegram bot — FOREVER (PID 1)
echo "[$$(date -u)] Starting Portfolio Tracking Telegram Bot — running 24/7 from PH soil..."
exec uv run telegram_bot.py