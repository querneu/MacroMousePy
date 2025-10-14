# Gravador de Macro de Mouse

Este projeto é uma aplicação de interface gráfica (GUI) desenvolvida em Python para gravar e reproduzir macros de mouse. A ferramenta é ideal para automatizar tarefas repetitivas no computador.

## 1. Funcionalidades

*   **Interface Gráfica Intuitiva**: Uma janela principal com acesso rápido a todas as funções.
*   **Gravação de Ações**: Captura movimentos, cliques (botões esquerdo, direito e do meio) e rolagens do mouse.
*   **Salvamento de Macros**: Salva as gravações em arquivos `.json` em um diretório `macros/`, com nomes que incluem data e hora para fácil identificação.
*   **Reprodução Flexível**:
    *   Permite selecionar qualquer macro `.json` salva para reprodução.
    *   Oferece a opção de definir um número específico de repetições.
    *   Inclui um modo de **repetição infinita** (loop até ser interrompido).
*   **Controle por Atalhos**:
    *   **`F8`**: Para a gravação a qualquer momento.
    *   **`F9`**: Aborta a reprodução da macro, mesmo em loop infinito.
*   **Feedback Visual**:
    *   Uma pequena janela "marca d'água" indica que a gravação está ativa.
    *   Caixas de diálogo informam sobre o status das operações (gravação salva, reprodução finalizada, etc.).

## 2. Como Usar

1.  Execute o arquivo `main.py` ou o executável `MacroMouse.exe`.
2.  A janela principal será exibida com as opções.

### Gravação

1.  Clique no botão **"Gravar Macro"**.
2.  A janela principal desaparecerá e um indicador "🔴 Gravando..." aparecerá no canto inferior direito da tela.
3.  Realize as ações de mouse que deseja gravar.
4.  Pressione a tecla **`F8`** para parar a gravação.
5.  Uma janela para salvar o arquivo será exibida. Escolha um nome e salve a macro.
6.  A janela principal retornará.

### Reprodução

1.  Clique no botão **"Reproduzir Macro"**.
2.  Selecione o arquivo `.json` da macro que deseja executar.
3.  Uma caixa de diálogo perguntará quantas vezes a macro deve ser repetida.
   *   Digite um número (ex: `5`) para um número fixo de repetições.
   *   Digite `0` para repetir infinitamente.
4.  A janela principal desaparecerá durante a reprodução.
5.  Para interromper a reprodução a qualquer momento, pressione a tecla **`F9`**.
6.  Ao final, a janela principal retornará.

## 3. Estrutura do Código

O código é organizado nas seguintes seções:

1.  **Importações e Variáveis Globais**: Módulos e variáveis de controle de estado.
2.  **Funções Utilitárias**: Funções de ajuda, como a que define o caminho para salvar arquivos.
3.  **Lógica de Gravação**: Funções que capturam os eventos do mouse e teclado.
4.  **Lógica de Reprodução**: Função que executa as ações da macro.
5.  **Classe da Aplicação (`MacroApp`)**: Onde a GUI e a lógica de interação são construídas.
6.  **Ponto de Entrada**: Bloco que inicia a aplicação.

## 4. Análise Detalhada do Código

Esta seção detalha o funcionamento de cada parte do script.

### 4.1. Importações e Variáveis Globais

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

*   **`pynput`**: Biblioteca principal para monitorar e controlar o mouse e o teclado.
*   **`threading`**: Essencial para executar a gravação e a reprodução em threads separadas, evitando que a interface gráfica (Tkinter) congele.
*   **`tkinter`**: Biblioteca padrão do Python para a criação da GUI.
*   **Variáveis Globais**: `recording` e `playing` são flags que controlam o estado da aplicação. `stop_thread` é um `threading.Event` usado para sinalizar de forma segura a interrupção da thread de reprodução.

### 4.2. Funções Utilitárias

```python
def data_path(filename):
    """Retorna caminho absoluto, mesmo quando empacotado com PyInstaller"""
    # ...
    macros_dir = os.path.join(base, "macros")
    os.makedirs(macros_dir, exist_ok=True)
    return os.path.join(macros_dir, filename)
```

*   Esta função cria um caminho seguro para os arquivos de macro, garantindo que funcione tanto ao rodar o script `.py` quanto o executável `.exe`. Ela cria um subdiretório `macros/` para manter os arquivos organizados.

### 4.3. Lógica de Gravação e Atalhos

```python
def on_move(x, y):
    if recording:
        actions.append({"type": "move", "pos": (x, y), "time": time.time()})

# ... (on_click, on_scroll) ...

def on_key_press(key):
    """Listener de teclado para F8 (parar) e F9 (abortar)"""
    if key == keyboard.Key.f8 and recording:
        stop_recording_or_playing()
        return False # Para o listener de gravação
    if key == keyboard.Key.f9 and playing:
        stop_recording_or_playing()
        return False # Para o listener de reprodução
```

*   As funções `on_move`, `on_click` e `on_scroll` são "callbacks" que o `pynput` chama. Elas registram cada ação do mouse em uma lista (`actions`) com detalhes como tipo, posição e o tempo exato do evento.
*   A função `on_key_press` escuta as teclas `F8` (para parar a gravação) e `F9` (para abortar a reprodução). Retornar `False` interrompe o listener do teclado.

### 4.4. Lógica de Reprodução

```python
def play_macro_thread(file_path, loop_count):
    # ...
    while playing and (is_infinite or loops_done < loop_count):
        prev_time = recorded[0]["time"]
        for action in recorded:
            if not playing:
                break

            delay = action["time"] - prev_time
            time.sleep(delay)
            prev_time = action["time"]
            # ... (executa a ação: move, click, scroll) ...
```

*   A reprodução é executada em uma thread (`play_macro_thread`) para não travar a interface.
*   O `delay` entre as ações é calculado pela diferença de tempo registrada na gravação. Isso garante que a macro seja reproduzida na mesma velocidade original.
*   O loop principal verifica a flag `playing` a cada ação, permitindo que a tecla `F9` interrompa a execução a qualquer momento.

### 4.5. Classe da Aplicação Principal (`MacroApp`)

Esta classe encapsula toda a lógica da interface gráfica e a interação com o usuário.

*   **`__init__(self, root)`**: Configura a janela principal, seu título, tamanho e chama a criação dos widgets.
*   **`create_main_widgets(self)`**: Cria os botões "Gravar Macro", "Reproduzir Macro" e "Sair", associando cada um à sua função correspondente.
*   **`start_recording(self)`**:
    1.  Esconde a janela principal (`self.root.withdraw()`).
    2.  Mostra o indicador de gravação.
    3.  Inicia os listeners de mouse e teclado em threads.
    4.  Usa `self.root.after()` para verificar periodicamente o fim da gravação sem bloquear a UI.
*   **`check_recording_status(self, ...)`**: Quando a gravação é parada (pelo F8), esta função para os listeners, fecha o indicador e chama `save_macro()`.
*   **`save_macro(self)`**:
    1.  Abre um diálogo para o usuário nomear e salvar o arquivo `.json`.
    2.  Salva a lista de ações no arquivo.
    3.  Reexibe a janela principal (`self.root.deiconify()`).
*   **`start_playback(self)`**:
    1.  Abre diálogos para o usuário selecionar o arquivo e o número de repetições.
    2.  Esconde a janela principal.
    3.  Inicia `play_macro_thread` em uma nova thread.
    4.  Usa `self.root.after()` para verificar o fim da reprodução.
*   **`check_playback_status(self, ...)`**: Quando a thread de reprodução termina, reexibe a janela principal.

### 4.6. Ponto de Entrada

```python
if __name__ == "__main__":
    main_root = tk.Tk()
    app = MacroApp(main_root)
    main_root.mainloop()
```

*   Este bloco padrão inicia a aplicação. Ele cria a janela raiz do Tkinter, instancia a nossa classe `MacroApp` e inicia o loop de eventos da GUI com `main_root.mainloop()`.

## 5. Dependências

Para executar este projeto, você precisa da seguinte biblioteca:

*   **pynput**: Para controle de mouse e teclado.

Você pode instalá-la usando pip:

```bash
pip install pynput
```

## 6. Como Empacotar (PyInstaller)

Para criar um arquivo executável (`.exe`) que pode ser distribuído e executado sem a necessidade de ter o Python instalado, você pode usar o PyInstaller.

1.  **Instale o PyInstaller**:
    ```bash
    pip install pyinstaller
    ```

2.  **Execute o comando**: Navegue até o diretório do projeto no terminal e execute o seguinte comando. A opção `--noconsole` (ou `--windowed`) é importante para que a aplicação GUI não abra um terminal preto em segundo plano.

    ```bash
    pyinstaller --onefile --windowed --name MacroMouse main.py
    ```

3.  **Encontre o executável**: O arquivo `MacroMouse.exe` estará dentro da pasta `dist/` que será criada.

---

