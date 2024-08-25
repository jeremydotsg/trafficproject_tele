FROM python:3-alpine AS builder

WORKDIR /app

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2
FROM python:3-alpine AS runner

#Add Chromium
RUN apk add chromium
RUN apk add chromium-chromedriver

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

COPY --from=builder /app/venv venv
COPY . .

WORKDIR /app

EXPOSE ${PORT}

RUN python manage.py migrate
RUN python manage.py collectstatic --noinput
CMD gunicorn --bind :${PORT} --workers 2 --env DJANGO_SETTINGS_MODULE=trafficproject.settings trafficproject.wsgi
