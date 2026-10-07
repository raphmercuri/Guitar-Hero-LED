# 🎸 Guitar Hero LED (Raspberry Pi Pico 2W + WS2812B)

This project recreates the classic Guitar Hero and Clone Hero experience in a physical (1D) dimension, using addressable LED strips (WS2812B) as the note track. The system operates entirely wirelessly, ensuring ultra-low latency through a local Wi-Fi network and UDP communication.

## 📐 System Architecture

The project is divided into three main hardware modules:

1. **The Guitar (Transmitter):** Runs on a Raspberry Pi Pico 2W embedded in the guitar body. It reads the state of 5 frets, Star and Plus buttons, and the strum bar, sending UDP packets (~100Hz) to the box. The system features an auto-reconnect logic, reconnecting invisibly if the network drops.


2. **The Box (Game Engine):** Another Raspberry Pi Pico 2W that acts as the Wi-Fi *Access Point* (`GuitarHero_Caixa`). It processes `.chart` files directly in memory (RAM), manages scoring, combos, and multipliers, and sends the exact colors and positions of the notes to 5 WS2812B LED strips (100 LEDs each).


3. **Audiovisual Module (ESP32):** Connects to the box's network and receives UDP instructions to display messages on an I2C LCD and command synchronized audio through a DFPlayer module.



## ✨ Main Features

* **Complete Game Engine:** Supports scoring, configurable hit window (`HIT_WINDOW_MS`), multipliers (1x to 4x), and Star Power.


* **Long Notes (Sustains):** Sustained notes have a visual tail dynamically generated on the LED strips. The player must hold the corresponding button until the end of the note to keep it active.


* **Dynamic LED Control:** The `display.py` module manages global brightness via software to prevent blinding the player and creates an impact flash around the hitbox whenever a note is hit.


* **Scalable Speed:** The game's pace can be adjusted via the `TEMPO_ROLAGEM_MS` variable, which changes how many milliseconds a note takes to cross the strip, automatically recalculating tail physics and musical sync.


* **Auto-Restart Shortcut:** Holding the `PLUS` button on the guitar for 5 seconds stops the music and returns the game to the main menu without dropping the Wi-Fi network.



## 📂 File Structure

Below is the breakdown of the source code and the components they belong to:

### Hardware: Guitar

* `main.py`: The sole guitar script. Connects to Wi-Fi, reads physical buttons using `machine.Pin`, and sends the state in plain text (`f_state,s_state,p_state,su_state,sd_state`) via UDP socket to the box.



### Hardware: Box (Pico 2W)

* `main_box.py`: Main orchestrator. Initializes the menu, ESP32 module (optional), and instantiates the `GameEngine`. It houses the shortcut to return to the menu via the `InputManagerComReinicio` class.


* `game_2.py`: The core game engine. Checks the timing (`ticks_ms`) for each note, handles guitar input received by the `InputManager`, and applies hit/miss rules.


* `song_2.py`: The Chart Parser. Reads `.chart` files line by line optimally to avoid memory fragmentation, converting Ticks and BPM from the "ExpertSingle" track directly into milliseconds using `array.array`.


* `display.py`: Rendering engine. Maps the game's logical note positions to the physical pixel space of the WS2812B strip, handling reverse drawing, base brightness (30%), and tail overlapping.


* `inputs.py`: Instantiates the Wi-Fi *Access Point* mode, opens UDP port `5000`, and extracts button states from packets sent by the guitar.


* `config.py`: Hardware and gameplay configuration hub. Contains IP addresses, LED strip pins, track length, hitbox position, hit window (`HIT_WINDOW_MS`), song directory names, and color definitions.


* `esp32_link.py`: Bridge protocol. Sends structured commands (`C` to clear, `T` for text, `P` to play track) over the network to instruct the LCD and MP3 redundantly (sent 3x to ensure delivery).



### Auxiliary Hardware: Generic I2C Communication

* `lcd_api.py` / `pico_i2c_lcd.py`: Base libraries for handling native I2C LCD displays (if not encapsulated within the ESP32).



## ⚙️ How to Setup

1. **Network Setup:** The guitar needs the SSID and password defined in the Box. By default, the network is `GuitarHero_Caixa` with the password `senha1234`.


2. **Songs Folder:** In the Box Pico's root directory, create separate folders for each song containing a valid `.chart` file. Ensure the search variable in the `MUSICAS` dictionary in `config.py` (e.g., `"slow ride"`) matches a part of the `.chart` or directory name.


3. **SD Card (ESP32):** Rename the songs sequentially (e.g., `0001.mp3`, `0002.mp3`) according to the index mapped in `config.py` under the `"faixa"` key.


4. **Visual Calibration:** Adjust the `INVERTER_FITA` variable in `config.py` to `True` if your physical cabinet's strips were soldered bottom-up.



## 🎮 How to Play

1. Turn on the Box hardware first to allow the Access Point to be created.


2. Turn on the guitar. It will endlessly search for the Box until the connection (using a zero-delay protocol) is successful.


3. In the Menu (viewed via LCD and Terminal), use the **strum bar (strum_up / strum_down)** to navigate available songs. Press the **Star** button on the guitar body to start the match.


4. For emergencies or to change the song, hold the **PLUS** button for 5 seconds.



---

*Educational project/integrated prototype built for physical experiences, ideal for events and experimental arcades.*

---

# 🎸 Guitar Hero LED (Raspberry Pi Pico 2W + WS2812B)

Este projeto recria a experiência clássica do Guitar Hero e Clone Hero em uma dimensão física (1D), utilizando fitas de LED endereçáveis (WS2812B) como a pista de notas. O sistema opera de forma totalmente sem fio, garantindo baixíssima latência através de uma rede Wi-Fi local e comunicação UDP.

## 📐 Arquitetura do Sistema

O projeto é dividido em três módulos de hardware principais:

1. **A Guitarra (Transmissor):** Roda em um Raspberry Pi Pico 2W embutido no corpo da guitarra. Ele lê o estado de 5 trastes, botões Star e Plus, e a palheta (strum), enviando pacotes UDP (~100Hz) para a caixa. O sistema possui lógica de auto-reconexão, reconectando-se de forma invisível caso a rede caia.


2. **A Caixa (Motor do Jogo):** Outro Raspberry Pi Pico 2W que atua como o *Access Point* Wi-Fi da rede (`GuitarHero_Caixa`). Ele processa a leitura de arquivos `.chart` na memória (RAM), gerencia a pontuação, combos e multiplicadores, e envia as cores/posições exatas das notas para 5 fitas de LED WS2812B de 100 LEDs cada.


3. **Módulo Audiovisual (ESP32):** Conecta-se à rede da caixa e recebe instruções via UDP para exibir mensagens em um display LCD (I2C) e comandar o áudio das músicas sincronizadas através de um módulo DFPlayer.



## ✨ Funcionalidades Principais

* **Motor de Jogo Completo:** Suporte a pontuação, janela de acerto configurável (`HIT_WINDOW_MS`), multiplicadores (1x a 4x) e Star Power.


* **Notas Longas (Sustains):** As notas sustentadas possuem um rastro visual ("tail") gerado dinamicamente nas fitas de LED. O jogador precisa segurar o botão correspondente até o fim da nota para mantê-la ativa.


* **Controle Dinâmico de LEDs:** O `display.py` gerencia o brilho global via software para não ofuscar o jogador e cria um "flash" de impacto ao redor da hitbox sempre que uma nota é acertada.


* **Velocidade Escalável:** O ritmo do jogo pode ser alterado através da variável `TEMPO_ROLAGEM_MS`, ajustando quantos milissegundos a nota leva para cruzar a fita, recalculando automaticamente a física do rastro e a sincronia musical.


* **Atalho de Reinício Automático:** Segurar o botão `PLUS` da guitarra por 5 segundos interrompe a música e retorna o jogo para o menu inicial sem desligar a rede Wi-Fi.



## 📂 Estrutura de Arquivos

Abaixo está o detalhamento dos códigos-fonte e de qual componente eles pertencem:

### Hardware: Guitarra

* `main.py`: O único script da guitarra. Conecta-se à rede Wi-Fi, lê os botões físicos utilizando `machine.Pin` e envia o estado em texto simples (`f_state,s_state,p_state,su_state,sd_state`) via socket UDP para a caixa.



### Hardware: Caixa (Pico 2W)

* `main_box.py`: Orquestrador principal. Inicia o menu, o módulo ESP32 (opcional) e instancia o `GameEngine`. É nele que reside o atalho para voltar ao menu através da classe `InputManagerComReinicio`.


* `game_2.py`: O coração do motor do jogo. Verifica o momento (ticks_ms) de cada nota, lida com a entrada da guitarra recebida pelo `InputManager` e aplica as regras de "hit" e "miss".


* `song_2.py`: O *Parser* de Charts. Lê arquivos `.chart` linha por linha de forma otimizada para evitar a fragmentação de memória, convertendo *Ticks* e *BPM* da pista "ExpertSingle" diretamente em milissegundos usando `array.array`.


* `display.py`: Motor de renderização. Mapeia a posição lógica das notas do jogo para o espaço físico de pixels da fita WS2812B, lidando com o desenho reverso, brilho base (30%) e sobreposição das caudas/rastros.


* `inputs.py`: Instancia o modo de *Access Point* Wi-Fi, abre a porta `5000` (UDP) e extrai os estados dos botões a partir dos pacotes enviados pela guitarra.


* `config.py`: Central de configurações de hardware e gameplay. Contém o IP, pinos das fitas, tamanho do percurso, posição da hitbox, janela de erro (`HIT_WINDOW_MS`), nomes dos diretórios de músicas e definição das cores.


* `esp32_link.py`: Protocolo de ponte. Envia comandos estruturados (`C` para limpar, `T` para texto, `P` para tocar faixa) pela rede para instruir o LCD e o MP3 de forma redundante (enviado 3x por garantia).



### Hardware Auxiliar: Comunicação I2C Genérica

* `lcd_api.py` / `pico_i2c_lcd.py`: Bibliotecas bases para lidar com displays LCD I2C nativos (se não estiverem encapsulados no ESP32).



## ⚙️ Como Configurar

1. **Configuração da Rede:** A guitarra precisa saber a senha e SSID definidos na Caixa. Por padrão, a rede é `GuitarHero_Caixa` com a senha `senha1234`.


2. **Pasta de Músicas:** Na raiz do Pico da Caixa, crie pastas separadas para cada música contendo um arquivo `.chart` válido. Certifique-se de que a variável de busca no dicionário `MUSICAS` do `config.py` (ex: `"slow ride"`) corresponde a parte do nome do `.chart` ou diretório.


3. **Cartão SD (ESP32):** Renomeie as músicas no formato sequencial (ex: `0001.mp3`, `0002.mp3`) de acordo com o index mapeado em `config.py` sob a chave `"faixa"`.


4. **Calibração Visual:** Ajuste a variável `INVERTER_FITA` no `config.py` caso as fitas do seu gabinete físico tenham sido soldadas de baixo para cima.



## 🎮 Como Jogar

1. Ligue primeiro o hardware da Caixa para permitir que o Access Point seja criado.


2. Ligue a guitarra. Ela procurará a caixa infinitamente até que a conexão (com protocolo de zero atraso) seja bem-sucedida.


3. No Menu (visualizado via LCD e Terminal), utilize a **palheta (strum_up / strum_down)** para navegar entre as músicas disponíveis. Pressione o botão **Star** no corpo da guitarra para iniciar a partida.


4. Para emergências ou para trocar a música, mantenha pressionado o botão **PLUS** por 5 segundos.

*Projeto educacional/protótipo integrado criado para ser experienciado de maneira física, ideal para eventos e fliperamas experimentais.*
