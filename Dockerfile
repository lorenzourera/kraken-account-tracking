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

WORKDIR /app

# .env
COPY .env ..
# Dependencies
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --frozen --no-cache

# Code
COPY app/ .
COPY scripts ./scripts
RUN chmod +x ./scripts/entrypoint.sh

# FIXED: Full path + timestamps + no escaping hell
RUN echo "5 0 * * * root echo \"\$(date '+%Y-%m-%d %H:%M:%S %Z') - CRON START\" >> /var/log/cron.log && " \
         "/root/.cargo/bin/uv run --project /app main.py >> /var/log/cron.log 2>&1 && " \
         "echo \"\$(date '+%Y-%m-%d %H:%M:%S %Z') - CRON SUCCESS\" >> /var/log/cron.log || " \
         "echo \"\$(date '+%Y-%m-%d %H:%M:%S %Z') - CRON FAILED\" >> /var/log/cron.log" \
    > /etc/cron.d/daily-pull \
    && chmod 0644 /etc/cron.d/daily-pull \
    && crontab /etc/cron.d/daily-pull \
    && touch /var/log/cron.log && chmod 666 /var/log/cron.log

# Use YOUR perfect entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]