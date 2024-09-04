# Use a base image with Python and Debian Slim
FROM python:3.12.5-slim-bullseye AS builder

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
#RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3.12.5-slim-bullseye AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

# Install system dependencies
# RUN apt-get update && apt-get install -y gcc libffi-dev openssl libstdc++6 fontconfig 
RUN apt-get update && apt-get install -y curl
RUN apt-get update                             \
 && apt-get install -y --no-install-recommends \
    curl firefox-esr           \
 && rm -fr /var/lib/apt/lists/*                \
 && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz | tar xz -C /usr/local/bin \

# Verify the installation
RUN geckodriver --version

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Download and install Chrome
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/linux64/chrome-headless-shell-linux64.zip -O /tmp/chrome-headless-shell-linux64.zip && \
    unzip /tmp/chrome-headless-shell-linux64.zip -d /opt/chrome && \
    rm /tmp/chrome-headless-shell-linux64.zip && \
    ln -s /opt/chrome/chrome-headless-shell /usr/bin/google-chrome

# Download and install ChromeDriver
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/linux64/chromedriver-linux64.zip -O /tmp/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver-linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver-linux64.zip

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv venv
COPY . .

EXPOSE ${PORT}

# Run database migrations and collect static files
# RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

WORKDIR /app

# Start the application using mod_wsgi
CMD gunicorn --bind :${PORT} --workers 2 --timeout 120 trafficproject.wsgi