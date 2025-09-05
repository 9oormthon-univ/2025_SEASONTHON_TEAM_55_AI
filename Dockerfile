FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env .
COPY . .
RUN python create_vectorstore.py

EXPOSE 5001
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5001"]