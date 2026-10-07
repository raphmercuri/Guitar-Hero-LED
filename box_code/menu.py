import os
import time
import config

# O menu e redesenhado de tempos em tempos (e nao so quando voce aperta algo):
# se o ESP32 (display) entrar na rede depois da caixa, o nome das musicas
# aparece sozinho em ate REDESENHAR_MS.
REDESENHAR_MS = 1500

# Nome de musica maior que a tela: o nome da musica selecionada rola da direita
# para a esquerda (as outras linhas mostram o comeco do nome).
ROLAGEM_PAUSA_MS = 1500   # espera antes de comecar a rolar
ROLAGEM_PASSO_MS = 350    # tempo de cada passo (1 letra)
ROLAGEM_ESPACO = 4        # espacos entre o fim do nome e a repeticao

class MenuMusicas:
    def __init__(self, lcd, inputs):
        self.lcd = lcd
        self.inputs = inputs
        self.musicas = []
        self.carregar_lista_musicas()

    def carregar_lista_musicas(self):
        self.musicas = []
        for entrada in os.ilistdir():
            nome_dir = entrada[0]
            tipo = entrada[1]
            
            if tipo == 16384:
                arquivos_pasta = os.listdir(nome_dir)
                if "notes.chart" in arquivos_pasta:
                    nome_exibicao = nome_dir
                    if "song.ini" in arquivos_pasta:
                        try:
                            with open(f"{nome_dir}/song.ini", "r") as f:
                                for linha in f:
                                    if linha.lower().startswith("name"):
                                        nome_exibicao = linha.split("=")[1].strip()
                                        break
                        except Exception:
                            pass
                            
                    musica = {
                        "titulo": nome_exibicao,
                        "artista": "",
                        "faixa": config.FAIXA_PADRAO,
                        "listada": False,
                        "pasta": nome_dir,
                        "chart_path": f"{nome_dir}/notes.chart"
                    }
                    # Procura a musica na lista MUSICAS do config.py (nome certo + numero da faixa)
                    procurado = (nome_dir + " " + nome_exibicao).lower()
                    for item in getattr(config, "MUSICAS", []):
                        if item["busca"].lower() in procurado:
                            musica["titulo"] = item["titulo"]
                            musica["artista"] = item.get("artista", "")
                            musica["faixa"] = item["faixa"]
                            musica["listada"] = True
                            break
                    self.musicas.append(musica)

        # Mostra na ordem das faixas (1, 2, 3...); as que nao estao na lista ficam no fim
        self.musicas.sort(key=lambda m: (m["faixa"] if m["listada"] else 999, m["titulo"]))
        for m in self.musicas:
            print("[MENU] faixa {} -> {} ({})".format(m["faixa"], m["titulo"], m["pasta"]))

    def _nome_na_lista(self, musica):
        # Texto mostrado na lista do display
        if getattr(config, "MOSTRAR_ARTISTA", False) and musica.get("artista"):
            return musica["titulo"] + " - " + musica["artista"]
        return musica["titulo"]

    def _linha(self, texto):
        # Corta no tamanho da tela e completa com espacos (apaga sobras da escrita anterior)
        cols = config.LCD_COLS
        texto = texto[:cols]
        return texto + " " * (cols - len(texto))

    def _deslocamento(self, titulo, decorrido):
        # Quantas letras o nome ja rolou (0 se cabe na tela ou ainda esta na pausa)
        largura = config.LCD_COLS - 1
        if len(titulo) <= largura or decorrido < ROLAGEM_PAUSA_MS:
            return 0
        passo = (decorrido - ROLAGEM_PAUSA_MS) // ROLAGEM_PASSO_MS
        return passo % (len(titulo) + ROLAGEM_ESPACO)

    def _desenhar(self, indice, deslocamento):
        # A musica selecionada fica na 1a linha (com ">") e as proximas abaixo.
        # Funciona em tela de 2 linhas (16x2) ou de 4 linhas (20x4).
        # Cada linha e escrita inteira (com espacos no fim), sem limpar a tela,
        # para nao piscar.
        largura = config.LCD_COLS - 1
        for i in range(config.LCD_ROWS):
            idx = indice + i
            if idx < len(self.musicas):
                titulo = self._nome_na_lista(self.musicas[idx])
                if i == 0 and len(titulo) > largura:
                    ciclo = titulo + " " * ROLAGEM_ESPACO
                    titulo = (ciclo + ciclo)[deslocamento:deslocamento + largura]
                else:
                    titulo = titulo[:largura]
                texto = (">" if i == 0 else " ") + titulo
            else:
                texto = ""
            self.lcd.move_to(0, i)
            self.lcd.putstr(self._linha(texto))

    def selecionar_musica(self):
        if not self.musicas:
            self.lcd.clear()
            self.lcd.putstr("Nenhuma musica\nencontrada.")
            time.sleep(2)
            return None

        indice_atual = 0
        inicio_item = time.ticks_ms()   # quando a musica atual foi selecionada (para a rolagem)
        ultimo_desenho = None
        indice_desenhado = -1
        desloc_desenhado = -1

        while True:
            self.inputs.update()
            agora = time.ticks_ms()

            # Aguarda ação do jogador baseada na palheta e botões do corpo
            if self.inputs.just_pressed_strum_down():
                indice_atual = (indice_atual + 1) % len(self.musicas)
                inicio_item = agora
            elif self.inputs.just_pressed_strum_up():
                indice_atual = (indice_atual - 1) % len(self.musicas)
                inicio_item = agora
            elif self.inputs.just_pressed_star():
                self.lcd.clear()
                self.lcd.putstr("Carregando...\n" + self.musicas[indice_atual]["titulo"][:config.LCD_COLS])
                time.sleep(1)
                return self.musicas[indice_atual]
            # O botão PLUS pode ser mapeado aqui futuramente se o menu tiver camadas (voltar pasta)

            # Desenha quando mudou a selecao, quando a rolagem andou, ou de tempos em tempos
            desloc = self._deslocamento(self._nome_na_lista(self.musicas[indice_atual]),
                                        time.ticks_diff(agora, inicio_item))
            if (ultimo_desenho is None
                    or indice_atual != indice_desenhado
                    or desloc != desloc_desenhado
                    or time.ticks_diff(agora, ultimo_desenho) >= REDESENHAR_MS):
                self._desenhar(indice_atual, desloc)
                indice_desenhado = indice_atual
                desloc_desenhado = desloc
                ultimo_desenho = agora

            time.sleep_ms(20)
