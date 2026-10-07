import neopixel
from machine import Pin
import config

class DisplayManager:
    def __init__(self):
        self.strips = [neopixel.NeoPixel(Pin(p), config.NUM_LEDS) for p in config.LED_PINS]
        
        # Temporizadores para fazer o brilho do acerto durar na tela
        self.flash_timers = [0, 0, 0, 0, 0] 
        
        # CONTROLE GLOBAL DE BRILHO: 
        # 1.0 = 100% (Cega) | 0.3 = 30% (Confortável) | 0.1 = 10% (Fraco)
        self.brilho = 0.3  

    def _idx(self, p):
        # Espelha a posicao quando INVERTER_FITA = True (config.py):
        # a zona de acerto fica no COMECO da fita e as notas descem do final.
        if getattr(config, "INVERTER_FITA", False):
            return config.NUM_LEDS - 1 - p
        return p

    def _aplicar_brilho(self, cor, multiplicador_extra=1.0):
        # Reduz matematicamente o valor RGB antes de enviar para o LED
        fator = self.brilho * multiplicador_extra
        return (int(cor[0] * fator), int(cor[1] * fator), int(cor[2] * fator))

    def clear(self):
        for strip in self.strips:
            strip.fill((0, 0, 0))
            strip.write()

    def render(self, active_notes, is_special_active=False, special_charge=0.0):
        # 1. Limpa o frame e desenha a Hitbox ou a Explosão de Acerto
        for i, strip in enumerate(self.strips):
            strip.fill((0, 0, 0))
            
            if self.flash_timers[i] > 0:
                # EFEITO DE ACERTO: a hitbox (2 LEDs) mais alguns LEDs do lado DE TRAS dela
                # (depois da zona de acerto, por onde a nota ja passou). Nada acende do
                # lado de onde as notas chegam, para nao confundir com elas.
                # FLASH_ANTES / FLASH_DEPOIS (config.py) ajustam quantos LEDs de cada lado.
                cor_flash = self._aplicar_brilho((255, 255, 255))
                antes = getattr(config, "FLASH_ANTES", 0)
                depois = getattr(config, "FLASH_DEPOIS", 2)
                start_flash = max(0, config.HIT_POS - antes)
                end_flash = min(config.NUM_LEDS, config.HIT_POS + 2 + depois)
                for p in range(start_flash, end_flash):
                    strip[self._idx(p)] = cor_flash
                
                # Desconta o tempo do efeito
                self.flash_timers[i] -= 1
            else:
                # HITBOX NORMAL: Linha branca de 2 LEDs esperando a nota
                cor_hitbox = self._aplicar_brilho((255, 255, 255))
                if config.HIT_POS < config.NUM_LEDS:
                    strip[self._idx(config.HIT_POS)] = cor_hitbox
                if config.HIT_POS + 1 < config.NUM_LEDS:
                    strip[self._idx(config.HIT_POS + 1)] = cor_hitbox

        # 2. Desenha as notas que estão "caindo" e seus rastros
        for note in active_notes:
            lane = note['lane']
            pos = note['pos']
            tail_leds = note.get('tail_leds', 0)
            
            if 0 <= lane < 5:
                color = config.NOTE_COLORS[lane]
                if note['is_special']:
                    color = config.COLOR_SPECIAL_MODE
                
                # Desenha o rastro (tail) beeem fraco
                if tail_leds > 0:
                    # Rastro usa apenas 5% da força da cor
                    tail_color = (int(color[0]*0.05), int(color[1]*0.05), int(color[2]*0.05))
                    for t in range(1, tail_leds + 1):
                        tail_pos = pos - t
                        if 0 <= tail_pos < config.NUM_LEDS:
                            self.strips[lane][self._idx(tail_pos)] = tail_color

                # Desenha a nota brilhante por cima
                if 0 <= pos < config.NUM_LEDS:
                    self.strips[lane][self._idx(pos)] = self._aplicar_brilho(color)

        # 3. Envia o quadro pronto para as 5 fitas
        for strip in self.strips:
            strip.write()

    def flash_hit(self, lane):
        # Em vez de piscar e apagar no mesmo instante, avisa o sistema 
        # para manter o LED branco aceso por 10 frames (~100 milissegundos)
        if 0 <= lane < 5:
            self.flash_timers[lane] = 10 

    def render_special_bar(self, charge):
        pass