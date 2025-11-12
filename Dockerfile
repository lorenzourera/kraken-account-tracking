FROM python:3.11.13-slim

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl cron tzdata ca-certificates postgresql-client gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/0.4.22/install.sh /install-uv.sh
RUN sh /install-uv.sh && rm /install-uv.sh
ENV PATH="/root/.cargo/bin:$PATH"

# Timezone
ENV TZ=Asia/Manila
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Working directory
WORKDIR /app

# Install Python dependencies (cached)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy application code
COPY app/ .

# Copy scripts and make executable
COPY scripts ./scripts
RUN chmod +x ./scripts/entrypoint.sh

# === FIXED CRON JOB WITH FULL PATH + TIMESTAMPS ===
RUN printf "%s\n" \
    "5 0 * * * root echo \"\$(date '+%Y-%m-%d %H:%M:%S %Z') - CRON START\" >> /var/log/cron.log && " \
    "                 /root/.cargo/bin/uv run --project /app main.py >> /var/log/cron.log 2>&1 && " \
    "                 echo \"\$(date '+%Y-%m-%d %H:%M:%S %Z') - CRON SUCCESS\" >> /var/log/cron.log || " \
    "                 echo \"\$(date '+%Y-%m-%d %H:%M:%S %Z') - CRON FAILED\" >> /var/log/cron.log" \
    > /etc/cron.d/daily-pull \
    && chmod 0644 /etc/cron.d/daily-pull \
    && crontab /etc/cron.d/daily-pull \
    && touch /var/log/cron.log \
    && chmod 666 /var/log/cron.log

# === BEST entrypoint.sh FOR CRON IN DOCKER ===
# Save this as scripts/entrypoint.sh
RUN printf "%s\n" \
    '#!/bin/sh' \
    'set -e' \
    '' \
    'echo "Starting cron daemon..."' \
    'cron' \
    '' \
    '# Show what will run' \
    'echo "Crontab:"' \
    'crontab -l' \
    '' \
    '# Optional: live tail the log' \
    'tail -F /var/log/cron.log &' \
    '' \
    '# Keep container alive (or run your main process here)' \
    'exec "$@"' \
    > /app/scripts/entrypoint.sh \
    && chmod +x /app/scripts/entrypoint.sh

# Entry point
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["sleep", "infinity"]   # Remove this line if you have a real long-running process