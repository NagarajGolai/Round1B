FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "run_pipeline.py"]
