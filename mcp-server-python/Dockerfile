# Imagem pronta para Cloud Run (usa a env PORT automaticamente).
# Este Dockerfile builda o SERVIDOR DE FERRAMENTAS (1-steam-tools-server),
# que é a parte que expõe o endpoint MCP (/mcp) e pode ficar hospedada
# na nuvem em vez de rodar via ngrok.
#
# Build:  docker build -t steam-mcp .
# Run:    docker run -p 8080:8080 -e STEAM_API_KEY=xxxx steam-mcp

FROM python:3.12-slim

WORKDIR /app

COPY 1-steam-tools-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY 1-steam-tools-server/server.py .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
