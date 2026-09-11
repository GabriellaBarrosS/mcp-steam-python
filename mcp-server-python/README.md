# Steam MCP Server

Servidor MCP (Model Context Protocol) que dá a um agente de IA (ex: **Gemini
Enterprise**) acesso a dados públicos da Steam de um jogador: perfil,
biblioteca de jogos, jogos recentes, detalhes de um jogo e conquistas.

## Ferramentas (tools) expostas

| Tool | O que faz | Parâmetros |
|---|---|---|
| `steam_get_player_profile` | Nome, avatar, status online, URL do perfil | `steam_id` |
| `steam_get_owned_games` | Biblioteca completa com horas jogadas | `steam_id` |
| `steam_get_recent_games` | Jogos jogados nas últimas 2 semanas | `steam_id` |
| `steam_get_game_details` | Descrição, gêneros, preço, data de lançamento de um jogo | `app_id` |
| `steam_get_games_on_sale` | Jogos em promoção na loja agora, com % de desconto e preços | `country_code` (opcional), `max_results` (opcional) |
| `steam_get_player_achievements` | Conquistas desbloqueadas/faltando num jogo | `steam_id`, `app_id` |

`steam_id` aceita tanto o SteamID64 numérico quanto o "nome de vanidade" da
URL do perfil (o servidor resolve automaticamente via `ResolveVanityURL`).

> `steam_get_game_details` e `steam_get_games_on_sale` usam a **Steam Store
> API pública** e não exigem `STEAM_API_KEY` — funcionam mesmo sem chave.
> As outras 4 tools usam a **Steam Web API** e precisam da chave.

## 1. Pegar sua Steam API Key

1. Acesse https://steamcommunity.com/dev/apikey (logado na sua conta Steam)
2. Registre um domínio qualquer (pode ser `localhost` para testes)
3. Copie a chave gerada

## 2. Rodar localmente

```bash
cd steam-mcp
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edite o .env e cole sua STEAM_API_KEY

export $(cat .env | xargs)      # ou use "python-dotenv" / defina manualmente
python server.py
```

Se tudo estiver certo, você verá algo como:
```
Uvicorn running on http://0.0.0.0:8080
```

O endpoint MCP fica em: **http://localhost:8080/mcp**

## 3. Testar sem precisar do Gemini Enterprise

Use o **MCP Inspector** (ferramenta oficial de debug, roda no navegador):

```bash
npx @modelcontextprotocol/inspector
```

Abra o link que aparecer, escolha transporte **"Streamable HTTP"**, cole
`http://localhost:8080/mcp` e clique em **Connect**. Você verá as 5
ferramentas listadas e pode chamá-las manualmente passando um `steam_id`
de teste (pode usar o seu próprio, se o perfil for público).

## 4. Conectar no Gemini Enterprise

No Gemini Enterprise / Agentspace, ao registrar uma ferramenta MCP customizada,
você vai precisar de uma **URL pública** apontando para `/mcp` (não localhost).
Para o momento da apresentação, duas opções:

- **Mostrar rodando local** + explicar a arquitetura (suficiente para a ideia).
- **Expor temporariamente com um túnel**, por exemplo:
  ```bash
  ngrok http 8080
  ```
  e usar a URL pública gerada (`https://xxxx.ngrok.app/mcp`) no cadastro do
  Gemini Enterprise. Bom para demo, não para produção.

## 5. Deploy definitivo (depois, não precisa pro sábado)

O `Dockerfile` já está pronto para o Cloud Run:

```bash
gcloud run deploy steam-mcp \
  --source . \
  --set-env-vars STEAM_API_KEY=sua_chave_aqui \
  --allow-unauthenticated \
  --region us-central1
```

O Cloud Run injeta a variável `PORT` automaticamente — o `server.py` já lê
essa variável, então não precisa mudar nada no código.

## Por que essa arquitetura?

- **Streamable HTTP** em vez de stdio: é o transporte que serviços de nuvem
  como Gemini Enterprise conseguem falar (stdio só funciona com processos
  locais tipo Claude Desktop).
- **`steam_id` como parâmetro de cada tool**, em vez de fixo em variável de
  ambiente: assim o mesmo servidor serve qualquer jogador, não só um usuário
  fixo — importante se você quiser um dia usar isso com múltiplos usuários.
- **`stateless_http=True`**: cada chamada MCP é independente, sem sessão
  guardada em memória — combina bem com ambientes serverless como Cloud Run,
  que podem escalar a zero e voltar.

## Próximos passos possíveis (se quiser evoluir depois)

- Cache de respostas (Steam Web API tem rate limit)
- Tool para comparar dois jogadores (jogos em comum)
- Autenticação (hoje qualquer um que tenha a URL pode chamar as tools)
- Suporte a múltiplas chaves de API por usuário, em vez de uma key global
