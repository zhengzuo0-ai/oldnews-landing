FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import fastapi; import uvicorn; import supabase; print('All packages OK')"

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "python start.py"]
