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

# Copy scripts LAST and make executable (this survives COPY . .)
COPY scripts ./scripts
RUN chmod +x ./scripts/entrypoint.sh

# Cron job
RUN echo "5 0 * * * cd /app && uv run main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/daily-pull \
    && chmod 0644 /etc/cron.d/daily-pull \
    && crontab /etc/cron.d/daily-pull \
    && touch /var/log/cron.log

# Entry point
ENTRYPOINT ["/app/scripts/entrypoint.sh"]