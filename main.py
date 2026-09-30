import json
import js
from pyodide.ffi import create_proxy

# Estado global da Shell
CURRENT_DIR = ["FefehOS"]
VFS = {}
CURRENT_NODE = {}

def load_vfs():
    global VFS, CURRENT_NODE
    try:
        # Lê o JSON gerado pelo build.py
        with open("build.json", "r", encoding="utf-8") as f:
            VFS = json.load(f)
        CURRENT_NODE = VFS
    except Exception as e:
        print_to_output(f"[-] Erro fatal ao carregar VFS: {e}\n")

def print_to_output(text):
    output_div = js.document.getElementById("output")
    output_div.innerHTML += text + "<br>"
    output_div.scrollTop = output_div.scrollHeight

def update_prompt():
    path_str = "/" + "/".join(CURRENT_DIR)
    js.document.getElementById("prompt-label").innerText = f"fefeh@fefehOS:{path_str}$"

def resolve_path(path_parts):
    global VFS
    node = VFS
    for part in path_parts:
        if part == "" or part == "FefehOS":
            continue
        if part == "..":
            # Tratar subida de diretório se necessário
            pass
        elif part in node.get("children", {}):
            node = node["children"][part]
        else:
            return None
    return node

def execute_command(event):
    if event.key == "Enter":
        input_el = js.document.getElementById("terminal-input")
        cmd_line = input_el.value.strip()
        input_el.value = ""
        
        path_str = "/" + "/".join(CURRENT_DIR)
        print_to_output(f"<span style='color:#ff0055;'>fefeh@fefehOS:{path_str}$</span> {cmd_line}")
        
        if not cmd_line:
            return
            
        parts = cmd_line.split(" ")
        cmd = parts[0]
        args = parts[1:]
        
        # Lógica dos comandos
        if cmd == "clear":
            js.document.getElementById("output").innerHTML = ""
        elif cmd == "help":
            print_to_output("Comandos disponíveis: ls, cd, cat, pwd, clear, uname, help")
        elif cmd == "uname":
            print_to_output("FefehOS Linux-WASM 2026.9 x86_64 TTY")
        elif cmd == "pwd":
            print_to_output("/" + "/".join(CURRENT_DIR))
        elif cmd == "ls":
            # Navega até ao nó atual
            node = VFS
            for d in CURRENT_DIR:
                if d in node.get("children", {}):
                    node = node["children"][d]
            
            children = node.get("children", {})
            listing = "  ".join(children.keys())
            print_to_output(listing)
        elif cmd == "cat":
            if not args:
                print_to_output("cat: falta argumento")
            else:
                filename = args[0]
                node = VFS
                for d in CURRENT_DIR:
                    if d in node.get("children", {}):
                        node = node["children"][d]
                
                file_node = node.get("children", {}).get(filename)
                if file_node and file_node.get("type") == "file":
                    print_to_output(file_node.get("content", ""))
                else:
                    print_to_output(f"cat: {filename}: Ficheiro não encontrado ou é um diretório")
        else:
            print_to_output(f"zsh: comando não encontrado: {cmd}")
            
        update_prompt()

# Inicialização
load_vfs()
update_prompt()
print_to_output("Bem-vindo ao FefehOS TTY (Python Powered). Digite 'help' para começar.\n")

# Associar o evento de tecla Enter ao input
input_element = js.document.getElementById("terminal-input")
input_element.addEventListener("keydown", create_proxy(execute_command))