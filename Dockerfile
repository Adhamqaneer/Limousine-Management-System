FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src HSPACE_ENV=production
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 hspace
COPY --chown=hspace:hspace src ./src
COPY --chown=hspace:hspace manage.py ./
RUN mkdir -p /app/media && chown hspace:hspace /app/media
USER hspace
EXPOSE 8000
CMD ["python","-m","uvicorn","limousine.presentation.web.app:app","--host","0.0.0.0","--port","8000","--no-access-log"]
