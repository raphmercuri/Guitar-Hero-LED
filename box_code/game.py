import time
import config
from song import SongLoader

# Notas longas (sustain): True = o rastro so continua descendo enquanto o
# botao da pista estiver SEGURADO (igual ao jogo). False = o rastro continua
# ate o fim da nota mesmo se soltar o botao.
SUSTAIN_EXIGE_SEGURAR = True

# True = mostra no Shell quando uma nota longa e acertada / encerrada
# (ajuda a diagnosticar). Depois de testar pode colocar False.
DEBUG_SUSTAIN = True

class GameEngine:
    def __init__(self, song_info, input_mgr, display_mgr, lcd, scroll_time_ms=1800, audio=None):
        self.song_info = song_info
        self.inputs = input_mgr
        self.display = display_mgr
        self.lcd = lcd
        self.scroll_time_ms = scroll_time_ms
        # audio: objeto com tocar(faixa) e parar() (ESP32 + DFPlayer). None = sem musica.
        self.audio = audio

        self.score = 0
        self.streak = 0
        self.base_multiplier = 1
        self.total_notes = 0
        self.hits = 0

        self.special_charge = 0.0
        self.is_special_active = False
        self.drain_rate_per_sec = 12.5

        # Notas longas ja acertadas que continuam sendo desenhadas (so visual)
        self.sustains = []
        # Notas NAO acertadas que continuam descendo ate sair da fita
        self.passando = []
        self._lengths = None

    def start(self, difficulty="EasySingle"):
        loader = SongLoader(self.song_info["chart_path"])
        track = loader.load_chart(difficulty=difficulty)

        if not track or len(track) == 0:
            self.lcd.clear()
            self.lcd.putstr("Sem notas na\ndificuldade!")
            time.sleep(2)
            return

        self.total_notes = len(track)

        times = track.times
        lanes = track.lanes
        specials = track.specials
        lengths = track.lengths
        self._lengths = lengths
        self.sustains = []
        self.passando = []

        # Trajeto: quantos LEDs a nota percorre ate a zona de acerto.
        # Velocidade da nota = trajeto / scroll_time_ms. Trajeto menor = nota
        # mais lenta e fita menos "cheia", sem mexer na zona de acerto.
        self.trajeto = getattr(config, "TRAJETO_LEDS", config.HIT_POS)
        if self.trajeto > config.HIT_POS:
            self.trajeto = config.HIT_POS
        self.pos_inicial = config.HIT_POS - self.trajeto

        hit = bytearray(self.total_notes)
        missed = bytearray(self.total_notes)

        self._countdown()

        # Musica e notas comecam JUNTAS: manda o ESP32 tocar e, no mesmo instante,
        # zera o relogio do jogo (as notas comecam a descer a partir daqui).
        if self.audio is not None:
            self.audio.tocar(self.song_info.get("faixa", config.FAIXA_PADRAO))
            if config.ATRASO_LEDS_MS > 0:
                time.sleep_ms(config.ATRASO_LEDS_MS)  # compensa o atraso do DFPlayer

        start_time = time.ticks_ms()
        last_time = start_time
        last_lcd_update = 0

        while True:
            self.inputs.update()
            
            now = time.ticks_diff(time.ticks_ms(), start_time)
            dt = time.ticks_diff(time.ticks_ms(), last_time) / 1000.0
            last_time = time.ticks_ms()

            if self.inputs.just_pressed_star() and not self.is_special_active and self.special_charge >= 50.0:
                self.is_special_active = True

            if self.is_special_active:
                self.special_charge -= self.drain_rate_per_sec * dt
                if self.special_charge <= 0:
                    self.special_charge = 0.0
                    self.is_special_active = False

            self.display.render_special_bar(self.special_charge)

            active_notes_for_render = []
            notes_remaining = False

            for i in range(self.total_notes):
                if hit[i] or missed[i]:
                    continue

                notes_remaining = True
                target = times[i]
                spawn_time = target - self.scroll_time_ms

                if now >= spawn_time:
                    if now > (target + config.HIT_WINDOW_MS):
                        missed[i] = 1
                        self._register_miss()
                        # Nao acertou: a nota passa reto pela zona de acerto e
                        # segue ate o fim da fita (desenhada em _atualizar_passando)
                        self.passando.append(i)
                    else:
                        progress = (now - spawn_time) / self.scroll_time_ms
                        pos = self.pos_inicial + int(progress * self.trajeto)

                        # Converte a duração da nota (ms) em quantidade de LEDs (com base na velocidade atual)
                        tail_leds = int((lengths[i] / self.scroll_time_ms) * self.trajeto)
                        # O rastro nao pode aparecer antes do ponto onde a nota nasce
                        if tail_leds > pos - self.pos_inicial:
                            tail_leds = pos - self.pos_inicial

                        if 0 <= pos <= config.NUM_LEDS or tail_leds > 0:
                            active_notes_for_render.append({
                                'lane': lanes[i],
                                'pos': pos,
                                'is_special': bool(specials[i]),
                                'tail_leds': tail_leds
                            })

            for lane in range(5):
                if self.inputs.just_pressed(lane):
                    self._check_player_hit(lane, now, times, lanes, specials, hit, missed)

            # Notas longas ja acertadas: continuam na tela (cabeca fixa na zona
            # de acerto, rastro encolhendo) em vez de sumir no momento do acerto
            if self.sustains:
                self._atualizar_sustains(now, times, lanes, specials, lengths, active_notes_for_render)

            # Notas nao acertadas: continuam descendo ate sair da fita
            if self.passando:
                self._atualizar_passando(now, times, lanes, specials, lengths, active_notes_for_render)

            self.display.render(
                active_notes_for_render,
                is_special_active=self.is_special_active,
                special_charge=self.special_charge
            )

            if time.ticks_diff(time.ticks_ms(), last_lcd_update) > 200:
                self._update_lcd_status()
                last_lcd_update = time.ticks_ms()

            if not notes_remaining and not self.sustains and not self.passando:
                break

            time.sleep_ms(10)

        self.display.clear()
        self._show_final_score()

        # Saiu da tela final: para a musica (se ainda estiver tocando)
        if self.audio is not None:
            self.audio.parar()

    def _atualizar_passando(self, now, times, lanes, specials, lengths, render_list):
        # Mesma conta de posicao das notas normais: depois da zona de acerto o
        # progresso passa de 1 e a nota segue descendo na mesma velocidade.
        restantes = []
        for i in self.passando:
            spawn_time = times[i] - self.scroll_time_ms
            progress = (now - spawn_time) / self.scroll_time_ms
            pos = self.pos_inicial + int(progress * self.trajeto)

            tail_leds = int((lengths[i] / self.scroll_time_ms) * self.trajeto)
            if tail_leds > pos - self.pos_inicial:
                tail_leds = pos - self.pos_inicial

            # Saiu da fita quando ate a ponta do rastro passou do ultimo LED
            if pos - tail_leds >= config.NUM_LEDS:
                continue

            restantes.append(i)
            render_list.append({
                'lane': lanes[i],
                'pos': pos,
                'is_special': bool(specials[i]),
                'tail_leds': tail_leds
            })
        self.passando = restantes

    def _atualizar_sustains(self, now, times, lanes, specials, lengths, render_list):
        frets = self.inputs.state["frets"]
        restantes = []
        for i in self.sustains:
            fim = times[i] + lengths[i]
            if now >= fim:
                if DEBUG_SUSTAIN:
                    print("Sustain pista", lanes[i] + 1, "terminou (segurou ate o fim)")
                continue  # a nota longa acabou
            if SUSTAIN_EXIGE_SEGURAR and not frets[lanes[i]]:
                if DEBUG_SUSTAIN:
                    print("Sustain pista", lanes[i] + 1, "encerrado: soltou o botao")
                continue  # soltou o botao: encerra o rastro
            restantes.append(i)
            tail = int(((fim - now) / self.scroll_time_ms) * self.trajeto)
            if tail > self.trajeto:
                tail = self.trajeto
            render_list.append({
                'lane': lanes[i],
                'pos': config.HIT_POS,
                'is_special': bool(specials[i]),
                'tail_leds': tail
            })
        self.sustains = restantes

    def _check_player_hit(self, lane, current_time, times, lanes, specials, hit, missed):
        hit_found = False
        for i in range(self.total_notes):
            if hit[i] or missed[i] or lanes[i] != lane:
                continue
                
            if times[i] - current_time > config.HIT_WINDOW_MS:
                break
                
            delta = abs(current_time - times[i])
            if delta <= config.HIT_WINDOW_MS:
                hit[i] = 1
                hit_found = True
                if self._lengths is not None and self._lengths[i] > 0:
                    self.sustains.append(i)
                    if DEBUG_SUSTAIN:
                        print("Nota longa acertada na pista", lane + 1, "- dura", self._lengths[i], "ms")
                self.hits += 1
                self.streak += 1

                if specials[i]:
                    self.special_charge = min(100.0, self.special_charge + 5.0)

                if self.streak >= 30:
                    self.base_multiplier = 4
                elif self.streak >= 20:
                    self.base_multiplier = 3
                elif self.streak >= 10:
                    self.base_multiplier = 2
                else:
                    self.base_multiplier = 1

                effective_multiplier = self.base_multiplier * 2 if self.is_special_active else self.base_multiplier

                self.score += 100 * effective_multiplier
                self.display.flash_hit(lane)
                break

        if not hit_found:
            self._register_miss()

    def _register_miss(self):
        self.streak = 0
        self.base_multiplier = 1

    def _countdown(self):
        self.lcd.clear()
        for i in range(3, 0, -1):
            self.lcd.move_to(9, 1)
            self.lcd.putstr(str(i))
            time.sleep(0.8)
        self.lcd.clear()

    def _linha(self, texto):
        # Corta no tamanho da tela e completa com espacos (apaga sobras da escrita anterior)
        cols = config.LCD_COLS
        texto = texto[:cols]
        return texto + " " * (cols - len(texto))

    def _update_lcd_status(self):
        mult_val = self.base_multiplier * 2 if self.is_special_active else self.base_multiplier
        mult_str = f"{mult_val}x"

        if self.is_special_active:
            sp_str = "SP:ATIVO!"
        elif self.special_charge >= 50.0:
            sp_str = "SP:PRONTO"
        else:
            sp_str = f"SP:{int(self.special_charge)}%"

        # Linha 1: "Pts: 1200"        Linha 2: "2x  SP:PRONTO"  (cabe em 16 colunas)
        self.lcd.move_to(0, 0)
        self.lcd.putstr(self._linha(f"Pts: {self.score}"))
        self.lcd.move_to(0, 1)
        self.lcd.putstr(self._linha(f"{mult_str:<3} {sp_str}"))

    def _qualquer_tecla(self):
        # Qualquer botao da guitarra (trastes, palheta, star ou plus), na hora em que e apertado
        inp = self.inputs
        return (any(inp.just_pressed(i) for i in range(5))
                or inp.just_pressed_star()
                or inp.just_pressed_plus()
                or inp.just_pressed_strum_up()
                or inp.just_pressed_strum_down())

    def _show_final_score(self):
        self.lcd.clear()
        accuracy = (self.hits / self.total_notes * 100) if self.total_notes > 0 else 0

        linhas = [
            "FIM DA MUSICA!",
            f"Pontos: {self.score}",
            f"Precisao: {accuracy:.1f}%",
            "Aperte uma tecla",
        ]
        # Na tela de 2 linhas, as linhas "rolam" de 2 em 2 segundos
        # (FIM/Pontos -> Pontos/Precisao -> Precisao/Aperte uma tecla).
        # Numa tela de 4 linhas aparece tudo junto.
        n_paginas = max(1, len(linhas) - config.LCD_ROWS + 1)
        pagina_atual = -1
        inicio_tela = time.ticks_ms()

        while True:
            self.inputs.update()

            decorrido = time.ticks_diff(time.ticks_ms(), inicio_tela)
            pagina = (decorrido // 2000) % n_paginas
            if pagina != pagina_atual:
                pagina_atual = pagina
                for r in range(config.LCD_ROWS):
                    if pagina + r < len(linhas):
                        self.lcd.move_to(0, r)
                        self.lcd.putstr(self._linha(linhas[pagina + r]))

            # So aceita sair depois de 1 s (evita fechar a tela por um aperto sem querer).
            # Qualquer botao da guitarra volta para o menu de musicas.
            if decorrido > 1000 and self._qualquer_tecla():
                break
            time.sleep_ms(50)
