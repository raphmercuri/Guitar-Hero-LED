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



---

*Projeto educacional/protótipo integrado criado para ser experienciado de maneira física, ideal para eventos e fliperamas experimentais.*
