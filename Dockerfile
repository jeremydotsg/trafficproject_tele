FROM python:3-alpine AS builder

WORKDIR /app

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Stage 2
FROM python:3-alpine AS runner

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

WORKDIR /app

COPY --from=builder /app/venv venv
COPY trafficdb trafficdb
COPY trafficproject trafficproject
COPY manage.py manage.py
COPY Procfile Procfile

# Fetching the latest nginx image
FROM nginx

# Removing default nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# Copying new conf.d into conf.d nginx image
COPY nginx.conf /etc/nginx/conf.d

WORKDIR /app

EXPOSE ${PORT}

CMD python manage.py migrate
CMD python manage.py collectstatic --noinput
#CMD gunicorn --bind :${PORT} --workers 2 trafficproject.wsgi