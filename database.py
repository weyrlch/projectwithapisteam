import sqlite3
import time  # novo import aqui
import json
import threading
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import steam_api
from api import SMARTAPI
from background_jobs import fila

def criar_tabela_historico():
    conn = sqlite3.connect("steam_users.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios_steam_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        steam_id TEXT,
        name TEXT,
        realname TEXT,
        avatar TEXT,
        profileurl TEXT,
        vac_bans INTEGER,
        game_bans INTEGER,
        community_ban BOOLEAN,
        trade_ban TEXT,
        loccountrycode TEXT,
        stateinfos INTEGER,
        cityinfos INTEGER,
        communityvisibilitystate INTEGER,
        account_age INTEGER,
        xpyos INTEGER,
        vanity_url TEXT,
        acclimit5dol TEXT,
        friends TEXT,
        lvl INTEGER,
        badge_xp INTEGER,
        badge_name TEXT,
        games_count INTEGER,
        badge_count INTEGER,
        xp INTEGER,
        data_registro INTEGER
        ) ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS ban_detected (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                steam_id TEXT UNIQUE,
                vac_bans INTEGER,
                game_bans INTEGER,
                community_ban BOOLEAN,
                trade_ban TEXT,
                first_ban_type INTEGER,
                shadow_ban INTEGER,
                data_register_ban TEXT,
                data_register_unban TEXT,
                datasave TEXT
            )
        ''')

    #first ban_type 1 = vac 2 = gameban
    conn.commit()
    conn.close()


def get_next_expired_profile(steam_id, api_key_for_background):
    conn = sqlite3.connect("steam_users.db")
    cursor = conn.cursor()

    # Pega o último registro de cada usuário que passou de 24h
    now = int(time.time())
    twenty_four_hours_ago = now - 24 * 60 * 60

    cursor.execute('''
        SELECT steam_id, MAX(data_registro) as last_time
        FROM usuarios_steam_historico
        GROUP BY steam_id
        HAVING last_time < ?
        ORDER BY last_time ASC
        LIMIT 1
    ''', (twenty_four_hours_ago,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        _process_single_player_data_and_friends(steam_id, api_key_for_background)  # SteamID do próximo usuário expirado
    return None

def pode_atualizar(steam_id, delayperuser=3600):
    conn = sqlite3.connect("steam_users.db")
    cursor = conn.cursor()

    cursor.execute('''
       SELECT data_registro FROM usuarios_steam_historico
       WHERE steam_id = ?
       ORDER BY data_registro DESC
       LIMIT 1
       ''', (steam_id,))

    resultado = cursor.fetchone()
    conn.close()

    if resultado is None:
        return False  # ou o que fizer sentido no seu caso

    timestamp_nowanddelay = int(time.time() - delayperuser)
    finalnumber = resultado[0]

    if finalnumber is not None and finalnumber >= timestamp_nowanddelay:
        return True



def salvar_versao(dados):
    conn = sqlite3.connect("steam_users.db")
    cursor = conn.cursor()

    timestamp = int(time.time())

    # --- CORREÇÃO AQUI ---
    # Serializa locinfos e friends para strings JSON
    friends_json = json.dumps(dados["friends"]) if dados["friends"] is not None else None
    # --- FIM DA CORREÇÃO ---
    cursor.execute('''
    INSERT INTO usuarios_steam_historico (
        steam_id, name, realname, avatar, profileurl, vac_bans, game_bans,
        community_ban, trade_ban, loccountrycode, stateinfos, cityinfos,
        communityvisibilitystate, account_age, xpyos, vanity_url,
        acclimit5dol, friends, lvl, badge_xp, badge_name,
        games_count, xp, badge_count, data_registro
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados["steam_id"],
        dados["name"],
        dados["realname"],
        dados["avatar"],
        dados["profileurl"],
        dados["vac_bans"],
        dados["game_bans"],
        dados["community_ban"],
        dados["trade_ban"],
        dados["loccountrycode"],
        dados["stateinfos"],
        dados["cityinfos"],
        dados["communityvisibilitystate"],
        dados["account_age"],
        dados["xpyos"],
        dados["vanity_url"],
        dados["acclimit5dol"],
        friends_json,  # <-- Usar a string JSON aqui
        dados["lvl"],
        dados["badge_xp"],
        dados["badge_name"],
        dados["games_count"],
        dados["xp"],
        dados["badge_count"],
        timestamp
    ))

    conn.commit()
    conn.close()


def _process_single_player_data_and_friends(steam_id, api_key_for_background):
    """
    Função a ser executada em segundo plano para buscar e salvar
    dados de um player e seus amigos.
    Esta função NÃO deve chamar get_player_info() de api.py para evitar circular import.
    Ela deve conter sua própria lógica para buscar dados da API.
    """
    print(f"[BACKGROUND] Iniciando processamento para SteamID: {steam_id}")
    try:
        # AQUI, REPLIQUE A LÓGICA NECESSÁRIA PARA OBTER OS DADOS DO JOGADOR
        # (similar ao que get_player_info faz para um único jogador, mas sem recursão)

        # URLs da API Steam (replicadas para evitar dependência cíclica com steam_api.py)
        profile_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key_for_background}&steamids={steam_id}"
        ban_url = f"https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={api_key_for_background}&steamids={steam_id}"
        lvl_url = f"https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key={api_key_for_background}&steamid={steam_id}"
        friends_url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={api_key_for_background}&steamid={steam_id}&relationship=friend"
        badges_url = f"https://api.steampowered.com/IPlayerService/GetBadges/v1/?key={api_key_for_background}&steamid={steam_id}"

        profile_response = requests.get(profile_url).json()
        ban_response = requests.get(ban_url).json()
        lvl_response = requests.get(lvl_url).json()
        friends_response = requests.get(friends_url).json()
        badges_response = requests.get(badges_url).json()

        profile_data = profile_response.get("response", {}).get("players", [])
        ban_data = ban_response.get("players", [])
        steam_level = lvl_response.get("response", {}).get("player_level", 0)
        steam_friends_raw = friends_response.get("friendslist", {}).get("friends", [])

        if not profile_data or not ban_data:
            print(f"[BACKGROUND] Sem dados completos para {steam_id}. Ignorando.")
            return

        player_xp = badges_response.get("response", {}).get("player_xp", 0)
        player = profile_data[0]
        bans = ban_data[0]

        # Funções auxiliares (você precisará importá-las ou copiá-las se elas não estiverem em database.py)
        # Ex: get_location_dict, get_badge_xp, conversor_timestamp, acclimit5dol, badgeschecker, get_custom_url, badge_from_xp
        # Para evitar circular imports, estas funções deveriam estar em um arquivo de 'utilitários' separado
        # que tanto api.py quanto database.py possam importar, OU serem copiadas para aqui se forem pequenas.
        # Por simplicidade e demonstração, vou assumir que você as terá disponíveis ou importará.

        # ATENÇÃO: As funções abaixo (get_location_dict, get_badge_xp, etc.) PRECISAM ESTAR DISPONÍVEIS AQUI.
        # A forma mais limpa é movê-las para um novo arquivo 'utils.py' e importar 'utils' aqui e em 'api.py'.
        # Por enquanto, estou chamando-as, assumindo que elas existam no escopo ou que você as importará.
        # Se elas estiverem apenas em steam_api.py, você terá um problema de importação circular.
        from steam_api import get_location_dict, get_badge_xp, conversor_timestamp, acclimit5dol, badgeschecker, \
            get_custom_url
        from badge_utils import badge_from_xp  # Certifique-se que badge_utils existe e está importável

        badge_xp = get_badge_xp(steam_id, 13)
        badge_name, games_count = badge_from_xp(badge_xp)

        player_data = {
            "steam_id": steam_id,
            "name": player.get("personaname", "Desconhecido"),
            "realname": player.get("realname", ""),
            "avatar": player.get("avatarfull", ""),
            "profileurl": player.get("profileurl", f"https://steamcommunity.com/profiles/{steam_id}"),
            "vac_bans": bans.get("NumberOfVACBans", 0),
            "game_bans": bans.get("NumberOfGameBans", 0),
            "community_ban": bans.get("CommunityBanned", False),
            "trade_ban": bans.get("EconomyBan", "none"),
            "loccountrycode": player.get("loccountrycode"),
            "stateinfos": player.get("locstatecode"),
            "cityinfos": player.get("loccityid"),
            "communityvisibilitystate": player.get("communityvisibilitystate"),
            "account_age": player.get("timecreated"),
            "xpyos": get_badge_xp(steam_id, 1),
            "vanity_url": get_custom_url(steam_id),  # Pode ser None
            "acclimit5dol": acclimit5dol(
                get_badge_xp(steam_id, 1),
                conversor_timestamp(player.get("timecreated"), "year"),
                bans.get("CommunityBanned", False),
                player.get("communityvisibilitystate"),
                steam_level
            ),
            "friends": steam_friends_raw,  # Lista de amigos diretos (raw)
            "lvl": steam_level,
            "badge_xp": badge_xp,
            "badge_name": badge_name,
            "games_count": games_count,
            "xp": player_xp,
            "badge_count": badgeschecker(steam_id)  # Pode ser None
        }


        salvar_versao(player_data)  # Usa a função local salvar_versao
        print(f"[BACKGROUND] Dados de {steam_id} salvos/atualizados no DB.")

            # Agora, para os amigos dos amigos (NÍVEL 2, 3, etc.):
            # Para cada amigo, iniciamos UMA NOVA TAREFA de background.
            # Isso cria uma "cascata" de processamento.
        for friend in steam_friends_raw:
            print(steam_friends_raw)
            if len(steam_friends_raw) > 1:
                friend_steamid = friend["steamid"]
                # CUIDADO: Isso pode gerar muitas threads! Para profundidade limitada,
                # você pode querer passar um 'depth' (profundidade) para a função
                # e parar de criar novas threads após uma certa profundidade.
                # Ex: if current_depth < max_depth: threading.Thread(target=..., args=(friend_steamid, api_key_for_background, current_depth + 1)).start()
                # Por simplicidade, este exemplo vai uma única camada profunda (amigos do player principal).
                # Se quiser mais, adicione o controle de profundidade.

                # NOVO: Inicia uma thread para processar cada amigo também.
                # Não é recursivo na mesma thread, mas cria novas threads.
                # Cada thread vai processar um amigo e seus *próprios* amigos.
                # Isso pode levar a um grande número de threads rapidamente se houver muitos amigos.
                if not pode_atualizar(friend_steamid):
                    fila.put(friend_steamid)
                else:
                    print(f"o {friend_steamid} não pode ser mais atualizado")






    except requests.exceptions.RequestException as e:
        print(f"[BACKGROUND ERROR] Erro ao acessar API da Steam para {steam_id}: {e}")
        print(f"Tentando novamente com {steam_id} ")
        _process_single_player_data_and_friends(steam_id, api_key_for_background)

    except Exception as e:
        print(f"[BACKGROUND ERROR] Erro inesperado no processamento de {steam_id}: {e}")

    # ----------------------------------------------------------------------------------
    # Funções existentes (criar_tabela_historico, pode_atualizar, salvar_versao)
    # ...
    # Certifique-se que o SELECT em buscar_ultima_versao corresponde à ordem do INSERT
    # -------------------------------------------------------



def buscar_ultima_versao(steam_id):
    conn = sqlite3.connect("steam_users.db")
    cursor = conn.cursor()
    # Ajustado o SELECT para corresponder à ordem do INSERT, facilitando a leitura
    cursor.execute('''
        SELECT steam_id, name, realname, avatar, profileurl, vac_bans, game_bans,
               community_ban, trade_ban, loccountrycode, stateinfos, cityinfos,
               communityvisibilitystate, account_age, xpyos, vanity_url,
               acclimit5dol, friends, lvl, badge_xp, badge_name,
               games_count, xp, badge_count, data_registro
        FROM usuarios_steam_historico
        WHERE steam_id = ?
        ORDER BY data_registro DESC
        LIMIT 1
    ''', (steam_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    # Mapeando a tupla 'row' para o dicionário 'dados'
    # Os índices aqui dependem da ordem das colunas no SELECT acima.
    # Certifique-se que eles batem!
    try:
        return {
            "steam_id": row[0],
            "name": row[1],
            "realname": row[2], # Índice 2
            "avatar": row[3],
            "profileurl": row[4],
            "vac_bans": row[5],
            "game_bans": row[6],
            "community_ban": bool(row[7]),
            "trade_ban": row[8],
            "loccountrycode": row[9],
            "stateinfos": row[10],
            "cityinfos": row[11],
            "communityvisibilitystate": row[12],
            "account_age": row[13],
            "xpyos": row[14],
            "vanity_url": row[15],
            "acclimit5dol": row[16],
            "friends": json.loads(row[17]) if row[17] else [], # Desserializa
            "lvl": row[18],
            "badge_xp": row[19],
            "badge_name": row[20],
            "games_count": row[21],
            "xp": row[22],
            "badge_count": row[23],
            "data_registro": row[24] # Último campo
        }
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Erro ao carregar dados do DB para {steam_id}: {e}")
        print(f"Linha de dados: {row}")
        return None


DB_FILE = 'steam_users.db'