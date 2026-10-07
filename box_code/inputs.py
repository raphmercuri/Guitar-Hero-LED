import network
import socket
import time
import config

class InputManager:
    def __init__(self):
        self.state = {"frets": [False]*5, "star": False, "plus": False, "strum_up": False, "strum_down": False}
        self.last_state = {"frets": [False]*5, "star": False, "plus": False, "strum_up": False, "strum_down": False}
        
        # 1. Cria a rede Wi-Fi exclusiva (Access Point)
        self.ap = network.WLAN(network.AP_IF)
        self._iniciar_ap()
        
        # 2. Abre a porta UDP para escutar a guitarra
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", config.UDP_PORT))
        self.sock.setblocking(False) # Não trava o jogo esperando dados

    def _iniciar_ap(self):
        # Sequencia padrao de inicializacao do Access Point (sempre igual):
        #  1) desliga o AP (limpa qualquer estado de uma execucao anterior)
        #  2) configura nome, senha, canal fixo, sem economia de energia, limite de aparelhos
        #  3) liga e espera ate o AP estar de fato no ar
        ap = self.ap
        ap.active(False)
        time.sleep_ms(300)
        ap.config(essid=config.WIFI_SSID, password=config.WIFI_PASS)
        # Os ajustes abaixo dependem do firmware da Pico: se algum nao existir, so e ignorado
        for chave, valor in (("channel", getattr(config, "WIFI_CANAL", 6)),
                             ("max_clients", getattr(config, "WIFI_MAX_CLIENTES", 4))):
            try:
                ap.config(**{chave: valor})
            except Exception:
                print("[AP] ajuste '{}' nao aceito por este firmware (ignorado)".format(chave))
        try:
            ap.config(pm=network.WLAN.PM_NONE)   # sem economia de energia: menos atraso/perda
        except Exception:
            pass
        ap.active(True)
        for _ in range(50):                      # ate ~5 s
            if ap.active():
                break
            time.sleep_ms(100)
        print("[AP] rede '{}' no ar em {} (canal {})".format(
            config.WIFI_SSID, ap.ifconfig()[0], getattr(config, "WIFI_CANAL", "?")))

    def update(self):
        self.last_state["frets"] = list(self.state["frets"])
        self.last_state["star"] = self.state["star"]
        self.last_state["plus"] = self.state["plus"]
        self.last_state["strum_up"] = self.state["strum_up"]
        self.last_state["strum_down"] = self.state["strum_down"]

        ultimo_pacote = None
        
        # Lê todos os pacotes que chegaram no ar até esvaziar o buffer
        try:
            while True:
                data, addr = self.sock.recvfrom(64)
                ultimo_pacote = data.decode('utf-8')
        except OSError:
            pass # Buffer vazio, sai do loop

        if ultimo_pacote:
            self._parse_packet(ultimo_pacote)

    def _parse_packet(self, pacote):
        try:
            partes = pacote.strip().split(',')
            if len(partes) == 5:
                self.state["frets"] = [True if c == '1' else False for c in partes[0]]
                self.state["star"] = partes[1] == '1'
                self.state["plus"] = partes[2] == '1'
                self.state["strum_up"] = partes[3] == '1'
                self.state["strum_down"] = partes[4] == '1'
        except Exception:
            pass

    def just_pressed(self, lane):
        return self.state["frets"][lane] and not self.last_state["frets"][lane]

    def just_pressed_star(self):
        return self.state["star"] and not self.last_state["star"]
        
    def just_pressed_plus(self):
        return self.state["plus"] and not self.last_state["plus"]

    def just_pressed_strum_up(self):
        return self.state["strum_up"] and not self.last_state["strum_up"]

    def just_pressed_strum_down(self):
        return self.state["strum_down"] and not self.last_state["strum_down"]