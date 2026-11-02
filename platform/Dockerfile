FROM node:22-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    DSH_HOME=/data/dsh \
    HOME=/data/home

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git ripgrep curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# DeepSeek Harness: тот самый агент, который читает/меняет файлы проекта.
RUN npm install -g @deepseek-ai/dsh@0.2.1-rc.2

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY app ./app
COPY static ./static

RUN mkdir -p /data /data/dsh /data/home

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
