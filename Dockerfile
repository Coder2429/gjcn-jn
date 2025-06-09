FROM python:3.11-slim  # Явно указываем Python 3.11

WORKDIR /app
COPY . .

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем и активируем venv (альтернативный способ)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем зависимости с предпочтением бинарных пакетов
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

CMD ["python", "telegram_ai_bot.py"]
