FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app user

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/media /app/staticfiles && chown -R user:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "TeamFlowAPI.wsgi:application", "--bind", "0.0.0.0:8000"]