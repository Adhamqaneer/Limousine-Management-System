FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DJANGO_SETTINGS_MODULE=limousine.config.settings.production
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 limousine
COPY --chown=limousine:limousine src ./src
COPY --chown=limousine:limousine manage.py ./

# Static collection needs no Oracle connection or deployment credentials.
RUN DJANGO_SETTINGS_MODULE=limousine.config.settings.base python manage.py collectstatic --noinput \
    && chown -R limousine:limousine /app/staticfiles
USER limousine
EXPOSE 8000
CMD ["gunicorn", "limousine.config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--error-logfile", "-"]
