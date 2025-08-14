# background_jobs.py
import time
import threading
import queue
from api import SMARTAPI
import database
import requests


fila = queue.Queue()

def adicionar_na_fila(steam_id):
    fila.put(steam_id)


def iniciar_loop_background(delay):
    def loop():
        while True:
            if not fila.empty():
                steam_id = fila.get()

                # 🔥 IMPORTA AQUI DENTRO para evitar loop de importação
                from database import _process_single_player_data_and_friends

                _process_single_player_data_and_friends(steam_id, SMARTAPI)
            else:
                time.sleep(1)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
