from flask import Flask, render_template, request, redirect
import steam_api

from badge_utils import badge_number
from steam_api import conversor_timestamp
from background_jobs import iniciar_loop_background
from api import DELAY, SMARTAPI

app = Flask(__name__)
iniciar_loop_background(DELAY)



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("steam_id")

        # Processar entrada corretamente
        steam_id64 = steam_api.process_search_input(user_input)

        if steam_id64:  # Apenas redireciona se houver um Steam ID64 válido
            return redirect(f"/id/{steam_id64}")
        else:
            print("⚠️ Entrada inválida ou não encontrada.")
            return render_template("index.html", error="Perfil não encontrado!")

    return render_template("index.html")

@app.route("/id/<steam_id>")
def perfil(steam_id):
    player_data = steam_api.get_player_info(steam_id, SMARTAPI)  # Passa a API key corretamente
    if player_data:
        return render_template("profile.html", player=player_data,
                               badge_number=badge_number if badge_number is not None else "",
                               conversor_timestamp=conversor_timestamp if conversor_timestamp is not None else "",)
    else:
        return render_template("error.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
