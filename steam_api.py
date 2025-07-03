# app.py

import requests
import re
from flask import Flask, render_template, request
from api import STEAM_API_KEY
from datetime import datetime
from bs4 import BeautifulSoup
from badge_utils import badge_from_xp


app = Flask(__name__)

def badgeschecker(url):
    linkprofile = f"https://steamcommunity.com/profiles/{url}"
    response = requests.get(linkprofile)
    soup = BeautifulSoup(response.text, 'html.parser')

    badge_count = soup.find('span', class_='profile_count_link_total')
    if badge_count:
        return badge_count.text.strip()
    else:
        return None


def converterbadgeforlvl(player_lvl):
    if isinstance(player_lvl, int):
       if player_lvl >= 100:
           format_lvl = ((player_lvl // 100) * 100)
           color_lvl = player_lvl % 100 // 10 * 10
       else:
           format_lvl = (player_lvl // 10) * 10
           color_lvl = player_lvl % 10
    else:
        format_lvl = None
        color_lvl = None
    return color_lvl, format_lvl

def process_search_input(user_input):
    """Verifica o formato da entrada e retorna um Steam ID64 válido."""
    steam_id_pattern = re.compile(r"^\d{17}$")  # Steam ID64: 17 dígitos

    if steam_id_pattern.match(user_input):
        return user_input  # Já é Steam ID válido

    if "steamcommunity.com/id/" in user_input:
        custom_name = user_input.split("/id/")[1].split("/")[0]
        return resolve_vanity_url(custom_name)

    if "steamcommunity.com/profiles/" in user_input:
        steam_id64 = user_input.split("/profiles/")[1].split("/")[0]
        return steam_id64  # Já é Steam ID válido

    return resolve_vanity_url(user_input)

def get_location_dict(profile_url):
    try:
        response = requests.get(profile_url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')

        location_div = soup.find("div", class_="header_location")
        if location_div:
            location_text = location_div.get_text(strip=True)
            parts = [p.strip() for p in location_text.split(',')]

            location_data = {}

            if len(parts) == 3:
                location_data["city"] = parts[0]
                location_data["state"] = parts[1]
                location_data["country"] = parts[2]
            elif len(parts) == 2:
                location_data["state"] = parts[0]
                location_data["country"] = parts[1]
            elif len(parts) == 1:
                location_data["country"] = parts[0]

            return location_data
        else:
            return None  # Sem localização visível
    except Exception as e:
        print(f"[ERRO] Falha ao obter localização: {e}")
        return None


def resolve_vanity_url(vanity_url):
    """Converte nome customizado da Steam para Steam ID64."""
    url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={vanity_url}"
    response = requests.get(url).json()

    if response.get("response", {}).get("success") == 1:
        return response.get("response", {}).get("steamid")
    else:
        return None

def get_custom_url(steam_id):
    url = f"https://steamcommunity.com/profiles/{steam_id}"
    try:
        response = requests.get(url, allow_redirects=True)
        final_url = response.url  # Link final após o redirecionamento

        if "/id/" in final_url:
            vanity = final_url.split("/id/")[1].split("/")[0]
            return vanity
        else:
            return None  # Não tem vanity
    except:
        return None

def get_badge_xp(steam_id, idbadge):
    """Obtém o XP da Insígnia de Colecionador de Jogos via Steam Web API."""
    url = f"https://api.steampowered.com/IPlayerService/GetBadges/v1/?key={STEAM_API_KEY}&steamid={steam_id}"
    try:
        response = requests.get(url).json()
        badges = response.get("response", {}).get("badges", [])

        for badge in badges:
            if badge["badgeid"] == idbadge:  # ID fixo da Insígnia “Game Collector”
                return badge.get("xp", 0)

        return 0
    except requests.exceptions.RequestException:
        return 0


def conversor_timestamp(creation_date, inputconfig):
    """Recebe um objeto datetime ou timestamp e retorna a idade da conta em anos e meses."""

    # Verifica se for timestamp (int ou float), converte para datetime
    if isinstance(creation_date, (int, float)):
        creation_date = datetime.fromtimestamp(creation_date)

    # Se ainda assim não for datetime, retorna erro
    if not isinstance(creation_date, datetime):
        return "Data inválida"

    hoje = datetime.now()
    diff = hoje - creation_date

    anos = diff.days // 365
    meses = (diff.days % 365) // 30
    dias = (diff.days % 365) % 30
    horas = diff.seconds // 3600
    minutos = (diff.seconds % 3600) // 60
    segundos = (diff.seconds % 3600) % 60

    if inputconfig is None:
        return f"{anos}y {meses}m {dias}d, {horas}h {minutos}m {segundos}s"
    if inputconfig == "year":
        return int(anos)

    return "Formato inválido"


def acclimit5dol(xp, year, communityban, cvs):
    if cvs != 3 or communityban != 0:
        return 2  ## not enough info to conclude

    if xp // 50 == year:
        return 0  ## no limit

    return 1  ## acc has a limit


def get_player_info(steam_id, api_key):

    # URLs da API Steam
    profile_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={steam_id}"
    ban_url = f"https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={api_key}&steamids={steam_id}"
    lvl_url = f"https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key={api_key}&steamid={steam_id}"
    friends_url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={api_key}&steamid={steam_id}&relationship=friend"

    try:
        profile_response = requests.get(profile_url).json()
        ban_response = requests.get(ban_url).json()
        lvl_response = requests.get(lvl_url).json()
        friends_response = requests.get(friends_url).json()

        profile_data = profile_response.get("response", {}).get("players", [])
        ban_data = ban_response.get("players", [])
        steam_level = lvl_response.get("response", {}).get("player_level", 0)
        steam_friends_raw = friends_response.get("friendslist", {}).get("friends", [])

        # Resumo dos amigos
        steam_ids = [f["steamid"] for f in steam_friends_raw]
        summary_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        summary_response = requests.get(summary_url, params={
            "key": api_key,
            "steamids": ",".join(steam_ids)
        }).json()

        players_data = summary_response.get("response", {}).get("players", [])
        friends_final = []

        def lvl_friend(api, steamidfriend):
            lvl_friendurl = f"https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key={api}&steamid={steamidfriend}"
            lvl_response_friend = requests.get(lvl_friendurl).json()
            return lvl_response_friend.get("response", {}).get("player_level", 0)



        # XP da badge Game Collector
        badge_xp = get_badge_xp(steam_id, 13)

        if not profile_data or not ban_data:
            return None

        player = profile_data[0]
        bans = ban_data[0]
        badge_name, games_count = badge_from_xp(badge_xp)

        player_data = {
            "steam_id": steam_id,
            "name": player.get("personaname", "Desconhecido"),
            "avatar": player.get("avatarfull", ""),
            "profileurl": player.get("profileurl", f"https://steamcommunity.com/profiles/{steam_id}"),
            "vac_bans": bans.get("NumberOfVACBans", 0),
            "game_bans": bans.get("NumberOfGameBans", 0),
            "community_ban": bans.get("CommunityBanned", False),
            "trade_ban": bans.get("EconomyBan", "none"),
            "loccountrycode": player.get("loccountrycode"),
            "locinfos": get_location_dict(f"https://steamcommunity.com/profiles/{steam_id}"),
            "communityvisibilitystate": player.get("communityvisibilitystate"),
            "account_age": player.get("timecreated"),
            "xpyos": get_badge_xp(steam_id, 1),
            "vanity_url": get_custom_url(steam_id),
            "acclimit5dol": acclimit5dol(
                get_badge_xp(steam_id, 1),
                conversor_timestamp(player.get("timecreated"), "year"),
                bans.get("CommunityBanned", False),
                player.get("communityvisibilitystate")
            ),
            "friends": friends_final,
            "lvl": steam_level,
            "badge_xp": badge_xp,
            "badge_name": badge_name,
            "games_count": int(games_count),
            "badge_count": int(badgeschecker(steam_id))
        }

        return player_data

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar API da Steam: {e}")
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("steam_input", "").strip()
        steam_id = process_search_input(user_input)
        if not steam_id:
            return render_template("index.html", error="Steam ID inválido ou perfil não encontrado")

        player = get_player_info(steam_id, STEAM_API_KEY)
        if not player:
            return render_template("index.html", error="Não foi possível obter dados do perfil")

        # Se tudo deu certo, renderize a página de perfil
        return render_template("profile.html", player=player)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
