# Use a base image with Python and Alpine Linux
FROM python:3.12.5-alpine3.20 AS builder

WORKDIR /app

# Create a virtual environment
RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3.12.5-alpine3.20 AS runner

# Create a non-root user (replace 'myuser' with your desired username)
RUN adduser -D -u 1000 www-user

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=80

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev
# Install Firefox ESR
RUN apk add --no-cache firefox
# Install Apache2 and apache2-dev
#RUN apk add --no-cache apache2 apache2-dev
RUN apk add nginx

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv venv
COPY . .

EXPOSE ${PORT}

# Run database migrations and collect static files
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput
#RUN pip install mod_wsgi
RUN pip install gunicorn
RUN chmod 776 /app/
RUN chown www-user:www-user /app/db.sqlite3
RUN chown www-user:www-user /app/static
RUN chmod 766 /app/db.sqlite3

COPY config/default.conf /etc/nginx/http.d/default.conf

WORKDIR /app

# Start the application using mod_wsgi
CMD sh config/start_server.sh
#CMD gunicorn --bind :${PORT} --workers 2 trafficproject.wsgi
# CMD mod_wsgi-express start-server --port=${PORT} --user=www-user --url-alias /static /app/static --application-type module trafficproject.wsgid