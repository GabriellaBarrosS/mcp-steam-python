import os
import requests
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP

# Configuração

STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_API_BASE = "https://api.steampowered.com"
STEAM_STORE_BASE = "https://store.steampowered.com/api"

if not STEAM_API_KEY:
    # Avisa erro das Tools que dependem da Steam Web API
    # com uma mensagem clara se alguém tentar chamá-las sem a key.
    print(
        "[aviso] STEAM_API_KEY não definida. Configure no .env ou nas "
        "variáveis de ambiente antes de usar as ferramentas."
    )

mcp = FastMCP(
    name="steam-mcp",
    stateless_http=True,  # cada chamada é independente e não precisa de sessão
)

# Helpers internos

def _require_api_key() -> str:
    if not STEAM_API_KEY:
        raise RuntimeError(
            "STEAM_API_KEY não configurada no servidor. "
            "Defina a variável de ambiente STEAM_API_KEY."
        )
    return STEAM_API_KEY

# Resolve SteamID64 a partir de um nome de vanidade (vanity URL) ou retorna o próprio SteamID se já for numérico.
def _resolve_steam_id(steam_id_or_vanity: str) -> str:

    steam_id_or_vanity = steam_id_or_vanity.strip()
    if steam_id_or_vanity.isdigit():
        return steam_id_or_vanity

    key = _require_api_key()
    resp = requests.get(
        f"{STEAM_API_BASE}/ISteamUser/ResolveVanityURL/v0001/",
        params={"key": key, "vanityurl": steam_id_or_vanity},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("response", {})
    if data.get("success") != 1:
        raise ValueError(
            f"Não foi possível resolver '{steam_id_or_vanity}' para um SteamID. "
            "Confira se o perfil é público e o nome de vanidade está correto."
        )
    return data["steamid"]

# Converte minutos para horas, arredondando para 1 casa decimal.
def _minutes_to_hours(minutes: float) -> float:
    return round(minutes / 60, 1)

# Tools MCP

@mcp.tool()
def steam_get_player_profile(steam_id: str) -> dict:
    #Retorna informações públicas de perfil de um jogador Steam: nome, status online, avatar e URL do perfil.

    key = _require_api_key()
    resolved_id = _resolve_steam_id(steam_id)

    resp = requests.get(
        f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v0002/",
        params={"key": key, "steamids": resolved_id},
        timeout=10,
    )
    resp.raise_for_status()
    players = resp.json().get("response", {}).get("players", [])
    if not players:
        return {"error": f"Nenhum jogador encontrado para o SteamID {resolved_id}."}

    p = players[0]
    persona_states = {
        0: "Offline",
        1: "Online",
        2: "Ocupado",
        3: "Ausente",
        4: "Soneca",
        5: "Buscando troca",
        6: "Buscando jogo",
    }

    return {
        "steam_id": resolved_id,
        "name": p.get("personaname"),
        "profile_url": p.get("profileurl"),
        "avatar": p.get("avatarfull"),
        "status": persona_states.get(p.get("personastate"), "Desconhecido"),
        "currently_playing": p.get("gameextrainfo"),
        "profile_visibility": "Público" if p.get("communityvisibilitystate") == 3 else "Privado/Limitado",
    }


@mcp.tool()
def steam_get_owned_games(steam_id: str) -> dict:
    #Retorna a lista completa de jogos na biblioteca Steam de um jogador,com o tempo total jogado em horas, ordenada do mais jogado para o menos.
    key = _require_api_key()
    resolved_id = _resolve_steam_id(steam_id)

    resp = requests.get(
        f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v0001/",
        params={
            "key": key,
            "steamid": resolved_id,
            "include_appinfo": True,
            "include_played_free_games": True,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("response", {})
    games = data.get("games", [])

    games_out = sorted(
        (
            {
                "app_id": g["appid"],
                "name": g.get("name", f"App {g['appid']}"),
                "playtime_hours": _minutes_to_hours(g.get("playtime_forever", 0)),
            }
            for g in games
        ),
        key=lambda g: g["playtime_hours"],
        reverse=True,
    )

    return {
        "steam_id": resolved_id,
        "total_games": data.get("game_count", len(games_out)),
        "games": games_out,
    }


@mcp.tool()
def steam_get_recent_games(steam_id: str) -> dict:
    """
    Retorna os jogos jogados por um jogador nas últimas 2 semanas, com o
    tempo jogado nesse período em horas.

    Args:
        steam_id: SteamID64 ou nome de vanidade do perfil.
    """
    key = _require_api_key()
    resolved_id = _resolve_steam_id(steam_id)

    resp = requests.get(
        f"{STEAM_API_BASE}/IPlayerService/GetRecentlyPlayedGames/v0001/",
        params={"key": key, "steamid": resolved_id},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("response", {})
    games = data.get("games", [])

    games_out = [
        {
            "app_id": g["appid"],
            "name": g.get("name", f"App {g['appid']}"),
            "playtime_last_2weeks_hours": _minutes_to_hours(g.get("playtime_2weeks", 0)),
            "playtime_total_hours": _minutes_to_hours(g.get("playtime_forever", 0)),
        }
        for g in games
    ]

    return {
        "steam_id": resolved_id,
        "recent_games": games_out,
    }


@mcp.tool()
def steam_get_game_details(app_id: int) -> dict:
    """
    Retorna detalhes públicos de um jogo da loja Steam: nome, descrição
    curta, gêneros, data de lançamento e preço (quando disponível).
    Não requer dados de um jogador específico.

    Args:
        app_id: AppID numérico do jogo na Steam (ex: 413150 para Stardew Valley).
    """
    resp = requests.get(
        f"{STEAM_STORE_BASE}/appdetails",
        params={"appids": app_id, "l": "portuguese"},
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json().get(str(app_id), {})

    if not payload.get("success"):
        return {"error": f"Detalhes não encontrados para o AppID {app_id}."}

    d = payload["data"]
    price = d.get("price_overview")

    return {
        "app_id": app_id,
        "name": d.get("name"),
        "short_description": d.get("short_description"),
        "genres": [g["description"] for g in d.get("genres", [])],
        "release_date": d.get("release_date", {}).get("date"),
        "is_free": d.get("is_free", False),
        "price": price.get("final_formatted") if price else ("Grátis" if d.get("is_free") else "N/D"),
        "header_image": d.get("header_image"),
    }


@mcp.tool()
def steam_get_games_on_sale(country_code: str = "BR", max_results: int = 20) -> dict:
    """
    Retorna jogos atualmente em promoção na loja Steam (aba "Especiais"),
    com percentual de desconto, preço original e preço com desconto.
    Não depende de um jogador específico -- é a vitrine pública da loja.

    Args:
        country_code: código de país (ISO 3166-1 alpha-2) usado para definir
                       a moeda e os preços exibidos, ex: "BR", "US". Default "BR".
        max_results: quantidade máxima de jogos a retornar (default 20).
    """
    resp = requests.get(
        f"{STEAM_STORE_BASE}/featuredcategories",
        params={"cc": country_code, "l": "portuguese"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    specials = data.get("specials", {}).get("items", [])

    def _format_price(cents: Optional[int]) -> Optional[str]:
        if cents is None:
            return None
        return f"{cents / 100:.2f}"

    games_out = [
        {
            "app_id": item.get("id"),
            "name": item.get("name"),
            "discount_percent": item.get("discount_percent"),
            "original_price": _format_price(item.get("original_price")),
            "final_price": _format_price(item.get("final_price")),
            "currency": country_code,
            "header_image": item.get("header_image"),
            "store_url": f"https://store.steampowered.com/app/{item.get('id')}",
        }
        for item in specials[:max_results]
    ]

    return {
        "country_code": country_code,
        "total_returned": len(games_out),
        "games_on_sale": games_out,
    }


@mcp.tool()
def steam_get_player_achievements(steam_id: str, app_id: int) -> dict:
    """
    Retorna as conquistas (achievements) de um jogador para um jogo
    específico: quais foram desbloqueadas e quais ainda faltam.

    Args:
        steam_id: SteamID64 ou nome de vanidade do perfil.
        app_id: AppID numérico do jogo na Steam.
    """
    key = _require_api_key()
    resolved_id = _resolve_steam_id(steam_id)

    resp = requests.get(
        f"{STEAM_API_BASE}/ISteamUserStats/GetPlayerAchievements/v0001/",
        params={"key": key, "steamid": resolved_id, "appid": app_id, "l": "portuguese"},
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json().get("playerstats", {})

    if not body.get("success"):
        return {
            "error": body.get(
                "error",
                "Não foi possível obter conquistas (o jogo pode não ter "
                "conquistas ou o perfil pode estar privado).",
            )
        }

    achievements = body.get("achievements", [])
    unlocked = [a for a in achievements if a.get("achieved") == 1]
    locked = [a for a in achievements if a.get("achieved") != 1]

    return {
        "steam_id": resolved_id,
        "app_id": app_id,
        "game_name": body.get("gameName"),
        "total_achievements": len(achievements),
        "unlocked_count": len(unlocked),
        "unlocked": [a.get("apiname") for a in unlocked],
        "locked": [a.get("apiname") for a in locked],
    }

# Entrypoint

if __name__ == "__main__":
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    # Streamable HTTP: funciona local (http://localhost:8090/mcp) e,
    # sem mudar nada, dentro de um container no Cloud Run (usa a env PORT).
    port = int(os.environ.get("PORT", 8090))

    # CORS liberado: necessário para clientes baseados em navegador (como o
    # MCP Inspector) conseguirem fazer fetch() no servidor. Em produção,
    # troque allow_origins=["*"] pela URL específica do seu cliente.
    app = CORSMiddleware(
        mcp.streamable_http_app(),
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )

    uvicorn.run(app, host="0.0.0.0", port=port)
