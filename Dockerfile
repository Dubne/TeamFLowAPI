FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/media /app/staticfiles && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "TeamFlowAPI.wsgi:application", "--bind", "0.0.0.0:8000"]