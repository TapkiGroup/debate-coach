# app/backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx python-dotenv pydantic
EXPOSE 8000
CMD ["uvicorn", "src.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
