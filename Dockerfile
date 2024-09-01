# Use a base image with Python and Alpine Linux
FROM python:3.12.5-alpine3.20 AS builder

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
#RUN apt-get update && apt-get install -y gcc musl-dev libffi-dev libssl-dev


# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3.12.5-alpine3.20 AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

# Install system dependencies
# RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev
# Install Firefox
RUN apk add firefox

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv venv
COPY . .

EXPOSE ${PORT}

# Run database migrations and collect static files
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

WORKDIR /app

# Start the application using mod_wsgi
CMD gunicorn --bind :${PORT} --workers 2 trafficproject.wsgi