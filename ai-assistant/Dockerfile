FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

# Створюємо користувача заздалегідь
RUN useradd -u 10100 -m appuser

# Копіюємо проект
COPY . .

# Створюємо окрему папку для бази даних всередині контейнера
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
