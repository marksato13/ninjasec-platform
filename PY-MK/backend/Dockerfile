FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --chown=app:app app ./app
COPY --chown=app:app alembic.ini ./alembic.ini

USER app

EXPOSE 8024

CMD ["sh", "-c", "python -m app.db.migrate && exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8024"]
