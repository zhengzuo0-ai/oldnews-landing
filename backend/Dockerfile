FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import fastapi; import uvicorn; import supabase; print('All packages OK')"

COPY . .

# Startup: print debug info then launch
CMD python -c "import sys; print(f'Python {sys.version}'); import main; print('Import OK')" && \
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
