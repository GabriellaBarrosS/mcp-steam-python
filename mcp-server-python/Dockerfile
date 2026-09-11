# Imagem pronta para Cloud Run (usa a env PORT automaticamente).
# Build:  docker build -t steam-mcp .
# Run:    docker run -p 8080:8080 -e STEAM_API_KEY=xxxx steam-mcp
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
