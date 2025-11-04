# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask flask_sqlalchemy flask_cors pydantic psycopg2-binary boto3
EXPOSE 5000
CMD ["python", "main.py"]
