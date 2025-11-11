FROM python:3.11.13-slim

# Install curl first (needed for uv installer)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fastest Python packager on earth)
ADD https://astral.sh/uv/0.4.22/install.sh /install-uv.sh
RUN sh /install-uv.sh && rm /install-uv.sh
ENV PATH="/root/.cargo/bin:$PATH"

# System deps: cron + postgres client + tzdata + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron tzdata ca-certificates postgresql-client gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# PH Timezone (UTC+8)
ENV TZ=Asia/Manila
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# App setup
WORKDIR /app

# Copy only what we need for install (caching)
COPY pyproject.toml uv.lock ./
COPY scripts/entrypoint.sh ./scripts/
RUN chmod +x scripts/entrypoint.sh

# Install deps with uv (cached forever)
RUN uv sync --frozen --no-cache

# Copy full app
COPY . .

RUN echo "5 0 * * * cd /app && uv run main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/daily-pull
RUN chmod 0644 /etc/cron.d/daily-pull
RUN crontab /etc/cron.d/daily-pull
RUN touch /var/log/cron.log

# Final entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]