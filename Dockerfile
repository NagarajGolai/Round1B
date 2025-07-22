FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY extract_outline.py ./
ENTRYPOINT ["python", "extract_outline.py"] 