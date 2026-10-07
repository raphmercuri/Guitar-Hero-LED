# ======================================================
# GUITARRA (TRANSMISSOR) - roda na Pico 2W dentro do braco
# Le os botoes localmente e manda o estado via Wi-Fi (UDP)
# para a Pico 2W da caixa.
# ======================================================

import time
import network
import socket
from machine import Pin

# ===================== CONFIGURACAO =====================
WIFI_SSID = "GuitarHero_Caixa"
WIFI_PASS = "senha1234"
CAIXA_IP = "192.168.4.1"   # IP padrao do Access Point da Pico da caixa
UDP_PORT = 5000

FRET_PINS = [14, 13, 12, 11, 10]   # Pista 1 (Verde) a Pista 5 (Laranja)
STAR_PIN = 7
PLUS_PIN = 6
STRUM_UP_PIN = 3
STRUM_DOWN_PIN = 2
# ==========================================================

frets = [Pin(p, Pin.IN, Pin.PULL_UP) for p in FRET_PINS]
star = Pin(STAR_PIN, Pin.IN, Pin.PULL_UP)
plus = Pin(PLUS_PIN, Pin.IN, Pin.PULL_UP)
strum_up = Pin(STRUM_UP_PIN, Pin.IN, Pin.PULL_UP)
strum_down = Pin(STRUM_DOWN_PIN, Pin.IN, Pin.PULL_UP)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
try:
    wlan.config(pm=network.WLAN.PM_NONE)   # sem economia de energia: pacotes sem atraso
except Exception:
    pass


def conectar_wifi():
    # Sequencia padrao de conexao (sempre igual): desconecta, conecta e ESPERA
    # ate o fim da tentativa, sem chamar connect() de novo no meio dela
    # (chamar varias vezes seguidas aborta a associacao em andamento).
    try:
        wlan.disconnect()
    except Exception:
        pass
    time.sleep_ms(300)
    wlan.connect(WIFI_SSID, WIFI_PASS)

    print("Conectando a rede da Caixa...")
    tentativas = 150  # ~15 segundos (150 x 0.1s)
    while not wlan.isconnected() and tentativas > 0:
        if wlan.status() < 0:
            print("Falha ao conectar. wlan.status() =", wlan.status(),
                  "(-2 = rede nao encontrada, -3 = senha errada)")
            return False
        time.sleep(0.1)
        tentativas -= 1

    if not wlan.isconnected():
        print("Nao conectou dentro do tempo limite (a Caixa esta ligada?)")
        return False

    print("Conectado! IP da guitarra:", wlan.ifconfig()[0])
    return True


# Tenta conectar; se falhar, espera 2 s e tenta de novo, sem limite de tentativas
# (a Caixa pode ainda estar ligando o Access Point quando a guitarra liga)
while not conectar_wifi():
    time.sleep(2)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
destino = (CAIXA_IP, UDP_PORT)

print("Enviando sinais dos botoes para a caixa...")

ultima_checagem = time.ticks_ms()

while True:
    # A cada ~2s, confere se a conexao ainda esta de pe. Se a Caixa
    # reiniciar (outro teste, reset, etc.) e o Access Point cair, a
    # guitarra percebe e reconecta sozinha, sem precisar replugar o cabo.
    if time.ticks_diff(time.ticks_ms(), ultima_checagem) > 2000:
        ultima_checagem = time.ticks_ms()
        if not wlan.isconnected():
            print("Conexao com a Caixa caiu. Reconectando...")
            while not conectar_wifi():
                time.sleep(2)

    f_state = "".join(["1" if f.value() == 0 else "0" for f in frets])
    s_state = "1" if star.value() == 0 else "0"
    p_state = "1" if plus.value() == 0 else "0"
    su_state = "1" if strum_up.value() == 0 else "0"
    sd_state = "1" if strum_down.value() == 0 else "0"

    pacote = f"{f_state},{s_state},{p_state},{su_state},{sd_state}\n"

    try:
        sock.sendto(pacote.encode("utf-8"), destino)
    except OSError:
        pass  # buffer cheio / rede momentaneamente instavel, ignora e segue

    time.sleep_ms(10)  # ~100 pacotes por segundo
