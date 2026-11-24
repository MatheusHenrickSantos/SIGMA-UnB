FROM python:3.12-slim

WORKDIR /app/codigos

ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
