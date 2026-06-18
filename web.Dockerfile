FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN pip install --upgrade pip

RUN pip install .

COPY . .

ENV FLASK_APP=backend/main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

EXPOSE 5000

RUN chmod +x setup.sh

CMD ["./setup.sh"]