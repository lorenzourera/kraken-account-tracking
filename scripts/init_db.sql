CREATE TABLE IF NOT EXISTS balance_snapshots (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    account_id VARCHAR(100) NOT NULL,  -- NEW: Account identifier
    snapshot_date DATE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    total_balance_usd DECIMAL(20, 2) NOT NULL,
    balances JSONB NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exchange, account_id, snapshot_date)  -- UPDATED: Include account_id
);

CREATE INDEX IF NOT EXISTS idx_balance_exchange_account_date 
    ON balance_snapshots(exchange, account_id, snapshot_date DESC);