FROM python:3.11-slim
WORKDIR /srv
COPY app ./app
ENV PORT=8080 PYTHONUNBUFFERED=1
CMD ["python3", "-m", "app.server"]
