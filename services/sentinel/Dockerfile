FROM python:3.11-slim
RUN apt-get update && apt-get install -y netcat && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY health.py .
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
CMD ["python", "health.py"]
