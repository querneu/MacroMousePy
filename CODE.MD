# Documentação Detalhada do Código: Gravador de Macro

Este documento fornece uma análise técnica detalhada do script `main.py`, explicando a função de cada parte do código.

## 1. Visão Geral

O script cria uma aplicação de interface gráfica (GUI) para gravar e reproduzir macros de mouse. Ele utiliza a biblioteca `tkinter` para a interface e `pynput` para monitorar e controlar o mouse e o teclado. O uso de `threading` é fundamental para garantir que a interface do usuário permaneça responsiva enquanto tarefas demoradas (como gravar ou reproduzir) são executadas em segundo plano.

---

## 2. Importações e Variáveis Globais

```python
from pynput import mouse, keyboard
import time
import json
import threading
import os
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

# --- Variáveis Globais de Controle ---
actions = []
recording = False
playing = False
stop_thread = threading.Event()
```

*   **Importações**:
    *   `pynput`: Biblioteca principal para criar "listeners" (monitores) e "controllers" (controladores) de mouse e teclado.
    *   `time`: Usado para registrar o timestamp de cada ação e para criar os delays durante a reprodução.
    *   `json`: Para serializar (salvar) e desserializar (carregar) a lista de ações da macro em um formato de texto legível.
    *   `threading`: Essencial para executar os listeners e a reprodução em threads separadas, evitando que a interface gráfica congele.
    *   `os`, `sys`: Usados para manipulação de caminhos de arquivos, garantindo que o programa encontre o diretório `macros/` corretamente, seja executado como script ou como um executável (`.exe`).
    *   `tkinter`: A biblioteca padrão do Python para criar a interface gráfica (janelas, botões, diálogos).
*   **Variáveis Globais**:
    *   `actions = []`: Uma lista que armazena cada ação do usuário (movimento, clique, etc.) como um dicionário. É limpa antes de cada nova gravação.
    *   `recording = False`: Uma flag booleana que atua como um interruptor global para iniciar e parar a captura de eventos.
    *   `playing = False`: Flag similar à `recording`, mas para controlar o estado da reprodução.
    *   `stop_thread = threading.Event()`: Um objeto de evento seguro para comunicação entre threads. É usado para sinalizar que a thread de reprodução deve ser interrompida (quando o usuário pressiona F9). É mais seguro do que usar uma flag booleana simples em cenários de concorrência.

---

## 3. Funções Utilitárias

```python
def data_path(filename):
    """Retorna caminho absoluto, mesmo quando empacotado com PyInstaller"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    macros_dir = os.path.join(base, "macros")
    os.makedirs(macros_dir, exist_ok=True)
    return os.path.join(macros_dir, filename)
```

*   **`data_path(filename)`**: Esta função resolve um problema comum ao empacotar scripts com PyInstaller.
    *   `getattr(sys, "frozen", False)` verifica se o script está rodando como um executável "congelado".
    *   Se for um `.exe`, o caminho base (`base`) é o diretório do próprio executável.
    *   Se for um script `.py`, o caminho base é o diretório onde o script está localizado.
    *   `os.makedirs(macros_dir, exist_ok=True)` garante que o subdiretório `macros` exista, criando-o se necessário, sem gerar erro se ele já existir.
    *   Retorna o caminho completo para o arquivo de macro dentro do diretório `macros`.

---

## 4. Lógica de Gravação e Atalhos

```python
def on_move(x, y):
    if recording:
        actions.append({"type": "move", "pos": (x, y), "time": time.time()})

# ... on_click, on_scroll são similares ...

def stop_recording_or_playing():
    global recording, playing
    recording = False
    playing = False
    stop_thread.set()

def on_key_press(key):
    if key == keyboard.Key.f8 and recording:
        stop_recording_or_playing()
        return False
    if key == keyboard.Key.f9 and playing:
        stop_recording_or_playing()
        return False

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_key_press) as listener:
        listener.join()
```

*   **`on_move`, `on_click`, `on_scroll`**: São as funções de "callback" que o `pynput.mouse.Listener` executa sempre que um evento correspondente do mouse é detectado.
    *   Elas verificam a flag global `recording`. Se for `True`, um dicionário contendo os detalhes da ação (tipo, posição, botão, timestamp) é adicionado à lista `actions`.
*   **`stop_recording_or_playing()`**: Função centralizada para parar qualquer operação. Define as flags `recording` e `playing` como `False` e ativa o evento `stop_thread.set()`, que sinaliza para a thread de reprodução que ela deve parar.
*   **`on_key_press(key)`**: O callback para o listener de teclado. Ele verifica se a tecla **F8** foi pressionada durante a gravação ou se a **F9** foi pressionada durante a reprodução.
    *   Se a condição for atendida, ele chama `stop_recording_or_playing()` e retorna `False` para parar o listener de teclado e a thread associada.
*   **`start_keyboard_listener()`**: Inicia o `pynput.keyboard.Listener` que fica "ouvindo" as teclas pressionadas em segundo plano. O `with` garante que o listener seja finalizado corretamente.

---

## 5. Lógica de Reprodução

```python
def play_macro_thread(file_path, loop_count):
    # ...
    m = Controller()
    playing = True
    stop_thread.clear()
    # ...
    while playing and (is_infinite or loops_done < loop_count):
        prev_time = recorded[0]["time"]
        for action in recorded:
            if not playing: break
            delay = action["time"] - prev_time
            time.sleep(delay)
            prev_time = action["time"]
            # ... (executa a ação) ...
    # ...
```

*   **`play_macro_thread(...)`**: Esta função é projetada para ser executada em uma `threading.Thread` separada.
    *   Ela lê o arquivo JSON e carrega as ações.
    *   `m = Controller()`: Cria um objeto para controlar o mouse programaticamente.
    *   `playing = True` e `stop_thread.clear()`: Prepara o estado para o início da reprodução.
    *   O loop `while` continua enquanto a flag `playing` for `True` e o contador de loops (`loops_done`) for menor que o solicitado (`loop_count`). A condição `is_infinite` (quando `loop_count == 0`) permite que o loop rode para sempre.
    *   **Cálculo do Delay**: A genialidade da reprodução está em `delay = action["time"] - prev_time`. Isso calcula o tempo exato que se passou entre uma ação e a próxima durante a gravação, e `time.sleep(delay)` pausa a execução por esse período, replicando o ritmo original.
    *   **Interrupção**: Dentro do loop, `if not playing: break` verifica a cada ação se a flag foi alterada (pela tecla F9). Isso garante uma interrupção quase imediata da macro.

---

## 6. Classe da Aplicação Principal (`MacroApp`)

Esta classe encapsula toda a lógica da interface gráfica e o gerenciamento de estado.

*   **`__init__(self, root)`**: O construtor da classe.
    *   Recebe a janela principal do Tkinter (`root`).
    *   Configura propriedades da janela como título, tamanho e centralização na tela.
    *   Chama `create_main_widgets()` para construir a interface.

*   **`create_main_widgets(self)`**: Cria e organiza os componentes visuais (widgets) na janela principal: um `Label` para instruções e os botões "Gravar Macro", "Reproduzir Macro" e "Sair", cada um associado a um método (`command=...`).

*   **`show_recording_indicator(self)`**: Cria a pequena janela "marca d'água" que informa o status de gravação.
    *   `Toplevel`: Cria uma nova janela.
    *   `overrideredirect(True)`: Remove as bordas e a barra de título.
    *   `attributes('-topmost', True)`: Mantém a janela sempre visível, acima de todas as outras.
    *   A janela é posicionada no canto inferior direito da tela.

*   **`start_recording(self)`**: Método chamado pelo botão "Gravar Macro".
    1.  Define a flag global `recording` como `True` e limpa a lista `actions`.
    2.  Esconde a janela principal com `self.root.withdraw()`.
    3.  Mostra o indicador de gravação.
    4.  Inicia os listeners de mouse e teclado em threads separadas para não bloquear a UI.
    5.  **`self.root.after(100, self.check_recording_status, ...)`**: Agenda a função `check_recording_status` para ser executada após 100ms. Esta é a técnica usada para criar um "loop de verificação" no Tkinter sem travar o `mainloop`.

*   **`check_recording_status(self, mouse_listener)`**:
    *   Verifica continuamente se a flag `recording` ainda é `True`.
    *   Se for, agenda a si mesma para rodar novamente em 100ms.
    *   Quando o usuário pressiona F8, a flag se torna `False`. Neste ponto, o método para o `mouse_listener`, destrói a janela indicadora e chama `save_macro()`.

*   **`save_macro(self)`**:
    *   Abre um diálogo padrão do sistema (`filedialog.asksaveasfilename`) para o usuário escolher onde salvar o arquivo.
    *   Sugere um nome de arquivo padrão com data e hora para evitar sobrescrever macros acidentalmente.
    *   Usa `json.dump()` para escrever a lista `actions` no arquivo.
    *   Reexibe a janela principal com `self.root.deiconify()` e a traz para o primeiro plano com `self.root.lift()`.

*   **`start_playback(self)`**: Método chamado pelo botão "Reproduzir Macro".
    1.  Abre diálogos para o usuário selecionar o arquivo (`.json`) e o número de repetições.
    2.  Esconde a janela principal.
    3.  Inicia a função `play_macro_thread` em uma nova thread, passando o caminho do arquivo e o número de loops como argumentos.
    4.  Usa `self.root.after()` para agendar `check_playback_status`, que irá monitorar o fim da reprodução.

*   **`check_playback_status(self, thread)`**:
    *   Verifica se a thread de reprodução (`thread.is_alive()`) ainda está em execução.
    *   Se estiver, agenda a si mesma para uma nova verificação.
    *   Quando a thread termina (seja por conclusão ou por ter sido abortada com F9), a janela principal é reexibida.

---

## 7. Ponto de Entrada

```python
if __name__ == "__main__":
    main_root = tk.Tk()
    app = MacroApp(main_root)
    main_root.mainloop()
```

*   Este é o bloco padrão que executa o código quando o script é chamado diretamente.
*   `main_root = tk.Tk()`: Cria a janela raiz da aplicação.
*   `app = MacroApp(main_root)`: Cria uma instância da nossa classe de aplicação, que constrói e gerencia toda a UI e lógica.
*   `main_root.mainloop()`: Inicia o loop de eventos do `tkinter`. Este loop é o coração de qualquer aplicação GUI, pois ele desenha a janela na tela e a mantém aberta, ouvindo e respondendo a eventos como cliques de botão e interações do usuário.