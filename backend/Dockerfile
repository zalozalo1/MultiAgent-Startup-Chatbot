FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY ai/pyproject.toml /app/ai/pyproject.toml
COPY ai/README.md /app/ai/README.md
COPY ai/src /app/ai/src

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app

RUN pip install ./ai ./backend

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
