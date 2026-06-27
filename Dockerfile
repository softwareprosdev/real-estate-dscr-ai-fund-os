FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Install API deps first (layer-cached separately from source code)
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
