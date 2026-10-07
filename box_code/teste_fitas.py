import time
import config
from inputs import InputManager
from display import DisplayManager

print("Iniciando teste das 5 fitas...")
print("Aguardando comunicação com a guitarra...")

# Puxa o gerenciador de botões e o gerenciador de LEDs da caixa
inputs = InputManager()
display = DisplayManager()

# Garante que começa tudo apagado
display.clear()

print("Pronto! Aperte os botões na guitarra.")

while True:
    # Atualiza o estado dos botões (lendo os pacotes que chegam da guitarra)
    inputs.update()
    
    # Passa por cada uma das 5 pistas
    for i in range(5):
        # Se o botão da pista atual estiver sendo segurado
        if inputs.state["frets"][i]:
            # Acende a fita inteira com a respectiva cor configurada
            display.strips[i].fill(config.NOTE_COLORS[i])
        else:
            # Apaga a fita
            display.strips[i].fill((0, 0, 0))
            
        # Envia a informação física para os LEDs
        display.strips[i].write()
        
    time.sleep_ms(10)