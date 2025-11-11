FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11 and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

# Make python3.11 the default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

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
ENTRYPOINT ["scripts/entrypoint.sh"]