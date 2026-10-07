# ======================================================
# LIGACAO COM O ESP32 - roda na Pico da CAIXA
# O ESP32 (audio + display) entra na rede da caixa. Aqui a Pico manda
# para ele, por UDP:
#   - o que deve aparecer no display (clear / move_to / putstr)
#   - o comando de tocar / parar a musica
#
# Protocolo (texto simples, uma mensagem por pacote UDP):
#   "C"            limpa o display
#   "M,x,y"        move o cursor
#   "T,texto"      escreve o texto na posicao do cursor
#   "P,seq,faixa"  toca a musica (0001.mp3 = faixa 1)
#   "S,seq"        para a musica
# Os comandos P e S sao enviados 3 vezes seguidas (mesmo "seq") para nao
# se perderem no ar; o ESP32 ignora as copias.
# ======================================================

import socket
import time
import config


class Esp32Link:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.destino = (config.ESP32_IP, config.ESP32_PORT)
        # Comeca num numero diferente a cada vez que a Pico liga
        self.seq = time.ticks_ms() % 100000
        self.ok = 0
        self.falhas = 0
        self.ultimo_erro = None
        self._ult_rel = 0

    def enviar(self, texto):
        try:
            self.sock.sendto(texto.encode("utf-8"), self.destino)
            self.ok += 1
        except OSError as e:
            # ESP32 fora da rede / rede ocupada: o jogo segue sem ele
            self.falhas += 1
            self.ultimo_erro = e
        self._relatorio()

    def _relatorio(self):
        # Diagnostico: so escreve no Shell quando algum envio falhou (no maximo 1x a cada 2 s)
        agora = time.ticks_ms()
        if self.falhas and time.ticks_diff(agora, self._ult_rel) >= 2000:
            self._ult_rel = agora
            print("[ESP32] envios ok={} FALHARAM={} (ultimo erro: {})".format(
                self.ok, self.falhas, self.ultimo_erro))

    def enviar_confiavel(self, tipo, extra=None):
        self.seq = (self.seq + 1) % 100000
        if extra is None:
            msg = "{},{}".format(tipo, self.seq)
        else:
            msg = "{},{},{}".format(tipo, self.seq, extra)
        for _ in range(3):
            self.enviar(msg)


class RemoteLCD:
    """Tem os mesmos metodos do LCD (clear, move_to, putstr), mas manda
    tudo para o display que esta ligado no ESP32. Tambem escreve no Shell
    (so quando o texto de uma linha muda, para nao encher o Shell)."""

    def __init__(self, link, imprimir=True):
        self.link = link
        self.imprimir = imprimir
        self.y = 0
        self._ultimo = {}   # ultimo texto mostrado no Shell em cada linha

    def clear(self):
        self.link.enviar("C")
        self._ultimo = {}

    def move_to(self, x, y):
        self.y = y
        self.link.enviar("M,{},{}".format(x, y))

    def putstr(self, texto):
        self.link.enviar("T," + texto)
        if self.imprimir and self._ultimo.get(self.y) != texto:
            self._ultimo[self.y] = texto
            print("[LCD]: " + texto.strip().replace("\n", " | "))


class RemoteAudio:
    """Manda o ESP32 tocar / parar a musica (DFPlayer)."""

    def __init__(self, link):
        self.link = link

    def tocar(self, faixa):
        self.link.enviar_confiavel("P", faixa)

    def parar(self):
        self.link.enviar_confiavel("S")
