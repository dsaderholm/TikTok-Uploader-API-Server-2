FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    nodejs \
    npm \
    xvfb \
    python3-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    git \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Clone TikTok Uploader repository
RUN git clone https://github.com/makiisthenes/TiktokAutoUploader.git /app/TiktokAutoUploader

# Install Node.js dependencies for TikTok signature
WORKDIR /app/TiktokAutoUploader/tiktok_uploader/tiktok-signature
RUN npm install

# Back to app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r /app/TiktokAutoUploader/requirements.txt

# Copy application code
COPY app/ ./app/

# Create necessary directories in TikTok uploader directory
RUN mkdir -p /app/TiktokAutoUploader/VideosDirPath \
    /app/TiktokAutoUploader/CookiesDir \
    /app/CookiesDir

# Set up Xvfb
RUN printf '#!/bin/bash\nXvfb :99 -screen 0 1024x768x16 &\nexec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Use entrypoint script to start Xvfb before the application
ENTRYPOINT ["/entrypoint.sh"]

# Run the application
CMD ["python", "app/main.py"]