FROM python:3.12-alpine

WORKDIR /app

COPY /backend /app/backend
COPY /tests /app/tests
COPY /alembic.ini /app
COPY /requirements.txt /app


RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN addgroup -S api && adduser -S api -G api
USER api

CMD ["python3", "-m", "backend.main", "--host", "0.0.0.0", "--port", "8000"]