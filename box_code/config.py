# Módulos de Hardware
HAS_SPECIAL_STRIP = False  

# Comunicação Serial (Recebendo da Guitarra)
UART_TX_PIN = 0
UART_RX_PIN = 1

# Pinos das Fitas de LED (Soldados na Caixa)
# Ordem = Pista 1 (Verde), 2 (Vermelho), 3 (Amarelo), 4 (Azul), 5 (Laranja)
# Conferido na pratica com o identificar_fitas.py (a fiacao fisica nao e sequencial)
# Ordem das fitas: 1a (verde), 2a (vermelho), 3a (amarelo), 4a (azul), 5a (laranja)
LED_PINS = [17, 19, 16, 18, 15]
SPECIAL_LED_PIN = 20
SPECIAL_NUM_LEDS = 7

# Tela LCD: agora fica ligada no ESP32 (a Pico manda o texto por Wi-Fi).
# Tamanho do display: 16 colunas x 2 linhas (se for um 20x4, troque aqui).
LCD_COLS = 16
LCD_ROWS = 2
# (Pinos I2C abaixo so serviriam se o LCD fosse ligado direto na Pico - nao usados)
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_ADDR = 0x27

# ESP32 (audio com DFPlayer + display)
USA_ESP32 = True              # False = joga sem o ESP32 (display so no Shell, sem musica)
ESP32_IP = "192.168.4.50"     # IP fixo do ESP32 na rede da caixa (igual no codigo do ESP32)
ESP32_PORT = 5001
FAIXA_PADRAO = 1              # musica tocada (1 = 0001.mp3 no cartao SD do DFPlayer)
# Sincronia: o DFPlayer demora um pouco para comecar a tocar depois do comando.
# Se a musica sair ATRASADA em relacao as notas, aumente este valor (de 50 em 50).
# O jogo espera esse tempo depois de mandar tocar e so entao comeca a descer as notas.
ATRASO_LEDS_MS = 0

# Pista e Mecânica
NUM_LEDS = 100       # Tamanho total da fita
HIT_POS = 90         # Posição da zona de acerto
# Quantos LEDs a nota percorre ate chegar na zona de acerto (a nota "nasce" no LED
# HIT_POS - TRAJETO_LEDS). Velocidade = TRAJETO_LEDS / TEMPO_ROLAGEM_MS (no main.py).
#   90 -> as notas nascem no LED 0 (comeco da fita) e descem ate a zona de acerto
#   40 -> as notas so aparecem a partir do LED 50 (meio da fita)
# Para as notas sempre nascerem no comeco da fita, mantenha igual ao HIT_POS.
TRAJETO_LEDS = 90
HIT_WINDOW_MS = 250  # Janela de tolerância de erro em milissegundos
# Brilho branco quando acerta uma nota: a hitbox (LED HIT_POS e HIT_POS+1) mais estes LEDs extras.
#   FLASH_DEPOIS = LEDs acesos DEPOIS da hitbox (lado de tras, por onde a nota ja passou)
#   FLASH_ANTES  = LEDs acesos ANTES da hitbox (lado de onde as notas chegam; confunde com as notas)
# Se acender do lado errado, troque: FLASH_ANTES = 2 e FLASH_DEPOIS = 0
# Inverte o sentido da fita: True = zona de acerto no COMECO da fita (LEDs 8 e 9) e as
# notas descem do final para o comeco. False = como era antes (acerto no final).
INVERTER_FITA = True

# Ao errar uma nota, a musica passa para a versao DESAFINADA (arquivo estereo: esquerdo =
# original, direito = desafinada) ate o proximo acerto. False = nunca desafina (desligado por enquanto;
# para ativar, tambem troque DESAFINACAO_ATIVA para true no sketch do ESP32).
DESAFINAR_AO_ERRAR = False

FLASH_ANTES = 0
FLASH_DEPOIS = 2
# ======================================================
# MUSICAS DO MENU: nome mostrado no display e numero da faixa no cartao SD (0001.mp3...)
# "busca" = pedaco do nome da PASTA da musica no Pico (ou do "name" do song.ini), sem
# diferenciar maiusculas de minusculas. O menu mostra as musicas na ordem da faixa.
# Musica que nao estiver nesta lista aparece com o nome do song.ini e toca FAIXA_PADRAO.
# ======================================================
MUSICAS = [
    {"busca": "slow ride",            "titulo": "Slow Ride",              "artista": "Foghat",           "faixa": 1},
    {"busca": "i was made",           "titulo": "I Was Made for Lovin' You", "artista": "KISS",          "faixa": 2},
    {"busca": "new faces",            "titulo": "New Faces in the Dark",  "artista": "Loathe",           "faixa": 3},
    {"busca": "iron man",             "titulo": "Iron Man",               "artista": "Black Sabbath",    "faixa": 4},
    {"busca": "everlong",             "titulo": "Everlong",               "artista": "Foo Fighters",     "faixa": 5},
    {"busca": "highway to hell",      "titulo": "Highway to Hell",        "artista": "AC/DC",            "faixa": 6},
    {"busca": "somewhere i belong",   "titulo": "Somewhere I Belong",     "artista": "Linkin Park",      "faixa": 7},
    {"busca": "is it really you",     "titulo": "Is It Really You?",      "artista": "Loathe",           "faixa": 8},
    {"busca": "no stranger",          "titulo": "No Stranger to You...",  "artista": "Loathe",           "faixa": 9},
    {"busca": "death of an executioner", "titulo": "Death of an Executioner", "artista": "Pierce the Veil", "faixa": 10},
]
# True = o menu mostra "Titulo - Artista" (nomes longos rolam na linha selecionada)
# False = mostra so o titulo
MOSTRAR_ARTISTA = True

# Cores dos LEDs (RGB)
NOTE_COLORS = [
    (0, 255, 0),    
    (255, 0, 0),    
    (255, 255, 0),  
    (0, 0, 255),    
    (255, 128, 0)   
]
COLOR_SPECIAL_MODE = (0, 255, 239)
COLOR_SPECIAL_DIM = (0, 40, 38)
COLOR_HIT_ZONE = (30, 30, 30)
COLOR_EMPTY = (0, 0, 0)
# Configuracoes de Rede Sem Fio
WIFI_SSID = "GuitarHero_Caixa"
WIFI_PASS = "senha1234"
UDP_PORT = 5000
# Ajustes do Access Point da caixa (a Pico cria a rede; guitarra e ESP32 entram nela)
WIFI_CANAL = 6            # canal fixo: guitarra e ESP32 acham a rede mais rapido (1, 6 ou 11)
WIFI_MAX_CLIENTES = 4     # guitarra + ESP32 + folga (so vale se o firmware da Pico aceitar)

