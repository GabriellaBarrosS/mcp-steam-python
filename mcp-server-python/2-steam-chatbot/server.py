import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o aplicativo FastAPI
app = FastAPI()

# Configura o CORS para permitir que o frontend acesse a API
# Em um ambiente de produção, restrinja as origens para o seu domínio de frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# Pega a chave da API da Groq das variáveis de ambiente
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("A variável de ambiente GROQ_API_KEY não foi definida.")

# URL PÚBLICA do seu servidor Steam MCP (a que o ngrok te dá) + "/mcp" no final.
# Ex: https://a1b2-c3d4.ngrok-free.app/mcp
# Sem isso configurado, o chatbot volta a ser um chat comum, sem saber nada de Steam.
STEAM_MCP_URL = os.environ.get("STEAM_MCP_URL", "")

# Inicializa o cliente da Groq
client = Groq(api_key=groq_api_key)

# Define o modelo de dados para a mensagem recebida do frontend
class Message(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"Status": "API do Chatbot está no ar!"}

# Define a rota do chatbot
@app.post("/chat")
async def handle_chat(message: Message):
    """
    Recebe uma mensagem do usuário, envia para a API da Groq -- incluindo
    acesso às ferramentas do Steam MCP Server, se STEAM_MCP_URL estiver
    configurada -- e retorna a resposta da IA.
    """
    try:
        tools = []
        if STEAM_MCP_URL:
            tools.append(
                {
                    "type": "mcp",
                    "server_label": "steam",
                    "server_url": STEAM_MCP_URL,
                    "server_description": (
                        "Ferramentas para consultar a Steam: perfil de jogador, "
                        "biblioteca de jogos, jogos recentes, detalhes de um "
                        "jogo, jogos em promoção e conquistas de um jogador."
                    ),
                    "require_approval": "never",
                }
            )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message.message,
                }
            ],
            # Modelo com suporte a MCP remoto (usado nos exemplos oficiais do Groq)
            model="openai/gpt-oss-120b",
            tools=tools if tools else None,
        )
        response_message = chat_completion.choices[0].message.content
        return {"response": response_message}
    except Exception as e:
        # Em caso de erro, retorna uma mensagem de erro
        return {"error": str(e)}

