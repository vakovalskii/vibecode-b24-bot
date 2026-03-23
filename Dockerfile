FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir vibecode-b24-bot

COPY bot.py .

ENV VIBE_API_KEY=""

CMD ["python", "bot.py"]
