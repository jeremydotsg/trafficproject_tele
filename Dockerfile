# Use a base image with Python
FROM python:3-alpine AS builder

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3-alpine AS runner

# Install Firefox and geckodriver
RUN apk add firefox
RUN apk add geckodriver

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv venv
COPY . .

EXPOSE ${PORT}

# Run database migrations and collect static files
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Start the application using Waitress
CMD waitress-serve --port=${PORT} trafficproject.wsgi:application
