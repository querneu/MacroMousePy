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

# --- Funções Utilitárias ---

def data_path(filename):
    """Retorna caminho absoluto, mesmo quando empacotado com PyInstaller"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    # Garante que o diretório de macros exista
    macros_dir = os.path.join(base, "macros")
    os.makedirs(macros_dir, exist_ok=True)
    return os.path.join(macros_dir, filename)

def key_to_str(key):
    """Converte um objeto de tecla do pynput para uma string serializável."""
    if isinstance(key, keyboard.Key):
        return key.name
    elif isinstance(key, keyboard.KeyCode):
        return key.char
    return str(key)

def str_to_key(key_str):
    """Converte uma string de volta para um objeto de tecla do pynput."""
    if len(key_str) == 1:
        return keyboard.KeyCode.from_char(key_str)
    try:
        return keyboard.Key[key_str]
    except KeyError:
        # Caso a tecla não seja encontrada, retorna a string para ser usada com type
        return key_str

# --- Lógica de Gravação ---

def on_move(x, y):
    if recording:
        actions.append({"type": "move", "pos": (x, y), "time": time.time()})

def on_click(x, y, button, pressed):
    if recording:
        actions.append({"type": "click", "pos": (x, y), "button": str(button), "pressed": pressed, "time": time.time()})

def on_scroll(x, y, dx, dy):
    if recording:
        actions.append({"type": "scroll", "pos": (x, y), "dx": dx, "dy": dy, "time": time.time()})

def on_record_press(key):
    """Callback para pressionar tecla durante a gravação."""
    if key == keyboard.Key.f8:
        stop_recording_or_playing()
        return False # Para o listener
    if recording:
        actions.append({"type": "key_press", "key": key_to_str(key), "time": time.time()})

def on_record_release(key):
    """Callback para soltar tecla durante a gravação."""
    if key != keyboard.Key.f8 and key != keyboard.Key.f9 and recording:
        actions.append({"type": "key_release", "key": key_to_str(key), "time": time.time()})

def stop_recording_or_playing():
    global recording
    global playing
    recording = False
    playing = False
    stop_thread.set() # Sinaliza para a thread de reprodução parar

def on_playback_hotkey(key):
    """Listener de teclado para F8 (parar) e F9 (abortar)"""
    if key == keyboard.Key.f9 and playing:
        stop_recording_or_playing()
        return False # Para o listener de reprodução

# --- Lógica de Reprodução ---

def play_macro_thread(file_path, loop_count):
    """Função que executa a reprodução em uma thread separada."""
    global playing
    from pynput.mouse import Controller, Button
    from pynput.keyboard import Controller as KeyboardController

    with open(file_path, "r", encoding="utf-8") as f:
        recorded = json.load(f)

    if not recorded:
        messagebox.showerror("Erro", "O arquivo de macro está vazio.")
        return

    m = Controller()
    k = KeyboardController()
    playing = True
    stop_thread.clear()

    # Inicia listener para F9 em uma thread separada
    def start_hotkey_listener():
        with keyboard.Listener(on_press=on_playback_hotkey) as listener:
            listener.join()
    hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
    hotkey_thread.start()

    loops_done = 0
    is_infinite = loop_count == 0

    while playing and (is_infinite or loops_done < loop_count):
        prev_time = recorded[0]["time"]
        for action in recorded:
            if not playing:
                break

            delay = action["time"] - prev_time
            if delay > 0:
                time.sleep(delay)
            prev_time = action["time"]

            if action["type"] == "move":
                m.position = tuple(action["pos"])
            elif action["type"] == "click":
                btn = Button.left if "left" in action["button"].lower() else (
                      Button.right if "right" in action["button"].lower() else Button.middle)
                if action["pressed"]:
                    m.press(btn)
                else:
                    m.release(btn)
            elif action["type"] == "scroll":
                m.scroll(action.get("dx", 0), action.get("dy", 0))
            elif action["type"] == "key_press":
                key = str_to_key(action["key"])
                k.press(key)
            elif action["type"] == "key_release":
                key = str_to_key(action["key"])
                k.release(key)

        loops_done += 1

    playing = False
    if stop_thread.is_set():
        messagebox.showinfo("Reprodução", "Reprodução abortada pelo usuário (F9).")
    else:
        messagebox.showinfo("Reprodução", "Reprodução da macro finalizada.")

# --- Classe da Aplicação Principal ---

class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gravador de Macro")
        self.root.geometry("380x120")
        self.root.resizable(False, False)
        self.center_window(self.root)

        self.recording_window = None
        self.create_main_widgets()

    def center_window(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')

    def create_main_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(expand=True, fill=tk.BOTH)

        label = tk.Label(frame, text="O que você deseja fazer?", font=("Segoe UI", 12))
        label.pack(pady=(0, 10))

        btn_frame = tk.Frame(frame)
        btn_frame.pack()

        tk.Button(btn_frame, text="Gravar Macro", command=self.start_recording, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reproduzir Macro", command=self.start_playback, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Sair", command=self.root.quit, width=15).pack(pady=(10, 0))

    def show_recording_indicator(self):
        """Cria uma janela 'marca d'água' para indicar a gravação."""
        self.recording_window = tk.Toplevel(self.root)
        self.recording_window.overrideredirect(True) # Sem bordas
        self.recording_window.attributes('-topmost', True)
        self.recording_window.attributes('-alpha', 0.6)

        label = tk.Label(self.recording_window, text="🔴 Gravando... (Pressione F8 para parar)",
                         bg="black", fg="white", font=("Segoe UI", 10))
        label.pack(padx=10, pady=5)

        # Posiciona no canto inferior direito
        self.recording_window.update_idletasks()
        width = self.recording_window.winfo_width()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.recording_window.geometry(f"+{screen_width - width - 10}+{screen_height - 50}")

    def start_recording(self):
        global recording, actions
        recording = True
        actions.clear()

        self.root.withdraw() # Esconde a janela principal
        self.show_recording_indicator()

        # Inicia listeners em threads para não bloquear a UI
        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        keyboard_listener = keyboard.Listener(on_press=on_record_press, on_release=on_record_release)

        mouse_listener.start()
        keyboard_listener.start()

        # Espera a gravação terminar
        self.root.after(100, self.check_recording_status, mouse_listener, keyboard_listener)

    def check_recording_status(self, mouse_listener, keyboard_listener):
        if recording:
            self.root.after(100, self.check_recording_status, mouse_listener, keyboard_listener)
        else:
            mouse_listener.stop()
            # O listener de teclado já para sozinho ao retornar False

            if self.recording_window:
                self.recording_window.destroy()
                self.recording_window = None
            self.save_macro()

    def save_macro(self):
        if not actions:
            messagebox.showwarning("Gravação", "Nenhuma ação foi gravada.")
            self.root.deiconify() # Mostra a janela principal novamente
            return

        default_filename = f"macro_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
        file_path = filedialog.asksaveasfilename(
            title="Salvar Macro",
            initialdir=data_path(""),
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(actions, f, indent=4)
            messagebox.showinfo("Sucesso", f"Macro salva em:\n{file_path}")

        self.root.deiconify() # Mostra a janela principal novamente
        self.root.lift()

    def start_playback(self):
        file_path = filedialog.askopenfilename(
            title="Selecione um arquivo de macro para reproduzir",
            initialdir=data_path(""),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return

        if not os.path.exists(file_path):
            messagebox.showerror("Erro", "Arquivo não encontrado.")
            return

        loops_str = simpledialog.askstring(
            "Repetir Gravação",
            "Quantas vezes repetir a gravação?\n(Digite 0 para repetir infinitamente até F9 ser pressionado)",
            parent=self.root
        )

        if loops_str is None: # Usuário cancelou
            return

        try:
            loops = int(loops_str)
        except (ValueError, TypeError):
            messagebox.showerror("Erro", "Por favor, insira um número válido.")
            return

        self.root.withdraw() # Esconde a janela principal durante a reprodução

        # Inicia a reprodução em uma thread para não travar a UI
        playback_thread = threading.Thread(
            target=play_macro_thread,
            args=(file_path, loops),
            daemon=True
        )
        playback_thread.start()

        # Agenda a verificação do fim da reprodução
        self.root.after(100, self.check_playback_status, playback_thread)

    def check_playback_status(self, thread):
        if thread.is_alive():
            self.root.after(100, self.check_playback_status, thread)
        else:
            self.root.deiconify() # Mostra a janela principal novamente
            self.root.lift()

if __name__ == "__main__":
    main_root = tk.Tk()
    app = MacroApp(main_root)
    main_root.mainloop()
