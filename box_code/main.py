import time
from machine import Pin
import machine
import config
from inputs import InputManager
from display import DisplayManager
from menu import MenuMusicas
from game import GameEngine

# Quanto tempo (em ms) uma nota leva para descer da ponta da fita ate a zona de
# acerto. E tambem a quantidade de musica visivel na fita ao mesmo tempo:
# Velocidade da nota (LEDs por segundo) = TRAJETO_LEDS (config.py) / TEMPO_ROLAGEM_MS * 1000.
#   Valor atual: 90 LEDs em 9 s = 10 LEDs/s (6000 dava 15 LEDs/s)
# Para ficar mais LENTO: aumente o TEMPO_ROLAGEM_MS (ex.: 11000 = 8 LEDs/s).
# Para ficar mais RAPIDO: diminua (ex.: 7000 = 13 LEDs/s).
# Atencao: quanto maior o tempo, mais notas ficam na fita ao mesmo tempo.
TEMPO_ROLAGEM_MS = 9000

# ATALHO "VOLTAR AO INICIO": segurar o botao PLUS da guitarra por este tempo (ms)
# para a musica, apaga as fitas e volta ao MENU DE MUSICAS, sem desligar nada:
# o Wi-Fi da caixa continua no ar (a guitarra e o ESP32 nao perdem a conexao).
TEMPO_REINICIO_MS = 5000

# Se preferir que o atalho REINICIE a Pico de verdade (machine.reset), troque para True.
# Atencao: o reset derruba o Wi-Fi da caixa e, rodando pelo Thonny, a Pico fica parada.
REINICIAR_PICO = False


class VoltarAoInicio(Exception):
    """Levantada quando o PLUS e segurado por TEMPO_REINICIO_MS."""
    pass


class InputManagerComReinicio(InputManager):
    """Igual ao InputManager, mas detecta o PLUS segurado por TEMPO_REINICIO_MS.
    Como o update() roda em todas as telas (menu, contagem, jogo, tela final),
    o atalho funciona em qualquer uma delas."""

    def __init__(self):
        InputManager.__init__(self)
        self.plus_desde = None
        self.avisou = False
        self.esperar_soltar = False   # depois de disparar, so rearma quando o PLUS for solto

    def update(self):
        InputManager.update(self)
        if not self.state["plus"]:
            self.plus_desde = None
            self.esperar_soltar = False
            return
        if self.esperar_soltar:
            return
        agora = time.ticks_ms()
        if self.plus_desde is None:
            self.plus_desde = agora
            self.avisou = False
            return
        tempo = time.ticks_diff(agora, self.plus_desde)
        if tempo >= 1000 and not self.avisou:
            self.avisou = True
            print("[REINICIAR] segurando PLUS... continue por {} s para voltar ao inicio".format(
                TEMPO_REINICIO_MS // 1000))
        if tempo >= TEMPO_REINICIO_MS:
            self.plus_desde = None
            self.esperar_soltar = True
            raise VoltarAoInicio()


# Simula o LCD no terminal do Thonny (usado quando config.USA_ESP32 = False)
class DummyLCD:
    def __init__(self):
        self.y = 0
        self._ultimo = {}
    def clear(self):
        self._ultimo = {}
    def move_to(self, x, y):
        self.y = y
    def putstr(self, text):
        # So mostra no Shell quando o texto de uma linha muda
        if self._ultimo.get(self.y) != text:
            self._ultimo[self.y] = text
            print(f"[LCD]: {text.strip().replace(chr(10), ' | ')}")

def main():
    # Display e musica ficam no ESP32 (ligado na rede da caixa)
    if config.USA_ESP32:
        from esp32_link import Esp32Link, RemoteLCD, RemoteAudio
        link = Esp32Link()
        lcd = RemoteLCD(link)
        audio = RemoteAudio(link)
    else:
        lcd = DummyLCD()
        audio = None

    # Inicializa Controles e LEDs
    input_mgr = InputManagerComReinicio()
    display_mgr = DisplayManager()

    display_mgr.clear()

    menu = MenuMusicas(lcd, input_mgr)

    print("=== JOGO INICIADO ===")
    if config.USA_ESP32:
        print("ESP32 esperado em", config.ESP32_IP, "porta", config.ESP32_PORT)
    print("Use a palheta (strum) para navegar no menu e Star para escolher a música.")

    try:
        while True:
            try:
                musica_selecionada = menu.selecionar_musica()

                if musica_selecionada:
                    print(f"\nCarregando: {musica_selecionada['titulo']}")
                    engine = GameEngine(
                        song_info=musica_selecionada,
                        input_mgr=input_mgr,
                        display_mgr=display_mgr,
                        lcd=lcd,
                        scroll_time_ms=TEMPO_ROLAGEM_MS,
                        audio=audio
                    )

                    engine.start(difficulty="ExpertSingle")
                    display_mgr.clear()
            except VoltarAoInicio:
                print("\nPLUS segurado: voltando ao inicio...")
                if REINICIAR_PICO:
                    raise
                # Para tudo e recomeca pelo menu (o Wi-Fi nao e mexido)
                if audio is not None:
                    audio.parar()
                display_mgr.clear()
                lcd.clear()
                lcd.putstr("Voltando ao\ninicio...")
                time.sleep_ms(1200)
    except VoltarAoInicio:
        # REINICIAR_PICO = True
        if audio is not None:
            audio.parar()
        display_mgr.clear()
        lcd.clear()
        lcd.putstr("Reiniciando...")
        time.sleep_ms(1500)
        machine.reset()
    except KeyboardInterrupt:
        print("\nPrograma interrompido (Ctrl+C).")
        # Roda quando o programa para por Ctrl+C: para a musica no ESP32,
        # apaga as fitas e avisa no display.
        if audio is not None:
            audio.parar()
        try:
            display_mgr.clear()
        except Exception:
            pass
        try:
            lcd.clear()
            lcd.putstr("Programa parado")
        except Exception:
            pass

if __name__ == "__main__":
    main()
