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
 && apt-get purge -y curl

# Verify the installation
RUN geckodriver --version

# Install PhantomJS
#RUN npm install -g phantomjs-prebuilt --unsafe-perm
#RUN export OPENSSL_CONF=/dev/null
#ENV OPENSSL_CONF=/dev/null
## Verify the installation
#RUN phantomjs --version

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
CMD gunicorn --bind :${PORT} --workers 2 trafficproject.wsgi