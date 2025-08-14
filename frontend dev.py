import steam_api
import api

steamid = input("STEAMIDPLEASE!!!!!!!!!!")
steam_api.get_player_info(steamid, next(api.SMARTAPI))
