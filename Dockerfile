# Use a base image with Python and Debian 12 (Bookworm)
FROM python:3.9.19-bookworm AS builder

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y gcc musl-dev libffi-dev libssl-dev

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3.9.19-bookworm AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app
# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y gcc musl-dev libffi-dev libssl-dev
# Install Firefox ESR and GeckoDriver
RUN apt-get install -y firefox-esr

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv venv
COPY . .

EXPOSE ${PORT}

# Run database migrations and collect static files
RUN pip install -r requirements.txt
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Start the application using Waitress
CMD waitress-serve --port=${PORT} trafficproject.wsgi:application
