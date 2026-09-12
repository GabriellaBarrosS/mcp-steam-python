# Steam MCP + Chatbot (Groq)

Projeto com **duas partes separadas**, cada uma com seu próprio `server.py`
independente. Veja `LEIA-ME-PRIMEIRO.txt` para a ordem de execução.

```
mcp-server-python/
│
├── 1-steam-tools-server/   # Servidor MCP: expõe 6 ferramentas da Steam
│   ├── server.py           # FastMCP + Steam Web API (porta 8090, rota /mcp)
│   ├── requirements.txt
│   └── .env                # STEAM_API_KEY, PORT
│
├── 2-steam-chatbot/        # Interface de chat que usa o Groq (IA)
│   ├── server.py           # FastAPI + Groq (porta 8000, rota /chat)
│   ├── index.html          # Frontend simples
│   ├── static/
│   ├── requirements.txt
│   └── .env                # GROQ_API_KEY, STEAM_MCP_URL
│
├── Dockerfile              # Builda o servidor de ferramentas (1-steam-tools-server)
└── LEIA-ME-PRIMEIRO.txt    # Ordem de execução, passo a passo
```
3
## Como as duas partes se conectam

1. **`1-steam-tools-server`** roda um servidor **MCP** (protocolo real de
   ferramentas, via `mcp[cli]`/`FastMCP`), com 6 tools que consultam a Steam
   Web API: perfil, biblioteca, jogos recentes, detalhes de jogo, promoções e
   conquistas. Ele expõe tudo em `http://localhost:8090/mcp`.
2. Você expõe essa porta publicamente com `ngrok http 8090` (a Groq precisa
   de uma URL https pública para chamar o MCP).
3. **`2-steam-chatbot`** roda uma API de chat comum (FastAPI + Groq). Ela
   NÃO implementa o protocolo MCP — ela só *aponta* para a URL do ngrok
   (variável `STEAM_MCP_URL` no `.env`) e manda isso pra Groq, que se
   conecta no servidor MCP para poder usar as ferramentas da Steam durante
   a conversa.
4. O `index.html` dessa pasta é o frontend que você abre no navegador para
   conversar com o bot.

⚠️ **Nunca copie o `server.py` de uma pasta para a outra** — são coisas
diferentes (uma fala MCP, a outra fala com a Groq). Foi exatamente essa
troca que causava o erro `Misdirected Request` ao carregar as tools do
servidor `steam`.

## Rodando

Veja o passo a passo completo em `LEIA-ME-PRIMEIRO.txt` e nos `LEIA-ME.txt`
dentro de cada subpasta. Resumo:

```bash
# Terminal 1
cd 1-steam-tools-server
python -m venv venv && venv\Scripts\activate   # (ou source venv/bin/activate no Linux/Mac)
pip install -r requirements.txt
python server.py
# -> Uvicorn rodando em http://0.0.0.0:8090

# Terminal 2
ngrok http 8090
# copie a URL https gerada

# Terminal 3
cd 2-steam-chatbot
# cole a URL do ngrok + "/mcp" no .env, campo STEAM_MCP_URL
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

Depois, abra `2-steam-chatbot/index.html` no navegador e converse.

## Deploy do servidor de ferramentas (opcional)

Se não quiser depender do ngrok, dá pra hospedar o `1-steam-tools-server`
em algo como Cloud Run usando o `Dockerfile` da raiz:

```bash
docker build -t steam-mcp .
docker run -p 8080:8080 -e STEAM_API_KEY=xxxx steam-mcp
```

Nesse caso, use a URL pública do deploy (+ `/mcp`) no `STEAM_MCP_URL` do
chatbot, em vez da URL do ngrok.
