FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN chmod +x /app/lm /app/entrypoint.sh

ENV MODEL_NAME=granite4:7b-a1b-h
ENV OLLAMA_HOST=http://host.docker.internal:11434

ENTRYPOINT ["/app/entrypoint.sh"]
