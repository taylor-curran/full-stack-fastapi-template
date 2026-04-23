FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Base utilities and Python tooling for backend/dev flows.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gpg \
    lsb-release \
    software-properties-common \
    sudo \
    git \
    unzip \
    python3.12 \
    python3.12-venv \
    python3-pip \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# Docker engine (docker.io), compose, and reliability extras for nested Docker in cloud agents.
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    docker-compose-v2 \
    fuse-overlayfs \
    iptables \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/docker && \
    printf '%s\n' '{' \
    '  "storage-driver": "fuse-overlayfs"' \
    '}' > /etc/docker/daemon.json && \
    update-alternatives --set iptables /usr/sbin/iptables-legacy && \
    update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

# Requested packages: Maven and PostgreSQL client/server.
RUN apt-get update && apt-get install -y --no-install-recommends \
    maven \
    postgresql \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Playwright Chromium runtime dependencies on Ubuntu 24.04.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2t64 \
    libatk-bridge2.0-0t64 \
    libatk1.0-0t64 \
    libatspi2.0-0t64 \
    libcairo-gobject2 \
    libcairo2 \
    libcups2t64 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0t64 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb-shm0 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xvfb \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Bun and uv for frontend/backend package management.
RUN curl -fsSL https://bun.sh/install | bash && \
    ln -sf /root/.bun/bin/bun /usr/local/bin/bun && \
    ln -sf /root/.bun/bin/bunx /usr/local/bin/bunx

RUN python3.12 -m pip install --no-cache-dir --break-system-packages uv

# Ensure cloud-agent user can access docker and sudo.
RUN id -u ubuntu &>/dev/null || useradd -m -s /bin/bash ubuntu
RUN groupadd -f docker && usermod -aG docker ubuntu
RUN usermod -aG sudo ubuntu
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu

