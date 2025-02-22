# Use a base image with Python and Alpine Linux
FROM python:3.12.5-alpine AS builder

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
# RUN apk update && apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3.12.5-alpine AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

# Install system dependencies
RUN apk update && apk add --no-cache curl wget nodejs npm
# RUN apk add chromium chromium-chromedriver
# RUN apk add nginx
# RUN apk add firefox
# RUN npm install firefox
# RUN npm install geckodriver

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv venv
COPY . .
# COPY config/default.conf /etc/nginx/http.d/default.conf

EXPOSE ${PORT}

ARG DJANGO_SUPERUSER_USERNAME
ARG DJANGO_SUPERUSER_EMAIL
ARG DJANGO_SUPERUSER_PASSWORD

# Run database migrations and collect static files
RUN python manage.py migrate
RUN python manage.py createsuperuser --noinput
RUN python manage.py loaddata config/whitelist.json
RUN python manage.py collectstatic --noinput

WORKDIR /app

# Start the application using gunicorn
CMD gunicorn --bind :${PORT} --workers 2 --timeout 120 trafficproject.wsgi
# CMD sh /app/config/start_server.sh