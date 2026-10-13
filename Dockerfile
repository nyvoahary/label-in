FROM python:3.12.13 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app


RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt
FROM python:3.12.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8080
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .
RUN mkdir -p /app/datasets
EXPOSE 8080
CMD ["/app/.venv/bin/python", "app.py", "datasets"]
