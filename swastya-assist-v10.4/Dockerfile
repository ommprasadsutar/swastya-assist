FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=5000
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz')"
CMD ["gunicorn","-w","2","-b","0.0.0.0:5000","--access-logfile","-","--error-logfile","-","app:app"]
