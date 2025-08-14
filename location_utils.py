import json
import os

# Carrega o JSON do repositório Holek
_here = os.path.dirname(__file__)
with open(os.path.join(_here, "data/steam_countries.min.json"), encoding="utf-8") as f:
    LOCATION_DATA = json.load(f)

def find_location(country_code, state_code=None, city_id=None):
    """
    Retorna dict com cidade, estado, país, string de busca e coordenadas.
    Baseado em Holek/steam-friends-countries.
    """
    result = {}
    try:
        country = LOCATION_DATA.get(country_code, {})
        if country:
            result["loccountry"] = country.get("name")
            result["coordinates"] = country.get("coordinates")
            result["coordinates_accuracy_level"] = country.get("coordinates_accuracy_level")
        if state_code and country:
            state = country.get("states", {}).get(str(state_code), {})
            if state:
                result["locstate"] = state.get("name")
                if state.get("coordinates"):
                    result["coordinates"] = state["coordinates"]
                    result["coordinates_accuracy_level"] = state.get("coordinates_accuracy_level")
            if city_id and state:
                city = state.get("cities", {}).get(str(city_id), {})
                if city:
                    result["loccity"] = city.get("name")
                    if city.get("coordinates"):
                        result["coordinates"] = city["coordinates"]
                        result["coordinates_accuracy_level"] = city.get("coordinates_accuracy_level")
        # Monta string legível "cidade, estado, país"
        parts = []
        if result.get("loccity"): parts.append(result["loccity"])
        if result.get("locstate"): parts.append(result["locstate"])
        if result.get("loccountry"): parts.append(result["loccountry"])
        result["map_search_string"] = ", ".join(parts)
    except Exception:
        pass
    return result
