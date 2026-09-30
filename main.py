import json
import js
from pyodide.ffi import create_proxy

# Estado global da Shell
CURRENT_DIR = []  # Raiz do sistema virtual "/"
VFS = {}
COMMAND_HISTORY = []
HISTORY_INDEX = -1

def load_vfs():
    global VFS
    try:
        with open("build.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Normaliza para garantir que a raiz é o topo do FHS
            if "FefehOS" in data.get("children", {}):
                VFS = data["children"]["FefehOS"]
            else:
                VFS = data
    except Exception as e:
        print_to_output(f"[-] Erro crítico ao carregar VFS: {e}\n", "error")

def print_to_output(text, style="normal"):
    output_div = js.document.getElementById("output")
    color_map = {
        "normal": "#00ff66",
        "error": "#ff0055",
        "info": "#00ccff",
        "command": "#ff0055"
    }
    color = color_map.get(style, "#00ff66")
    output_div.innerHTML += f"<span style='color:{color};'>{text}</span><br>"
    output_div.scrollTop = output_div.scrollHeight

def update_prompt():
    path_str = "/" + "/".join(CURRENT_DIR)
    js.document.getElementById("prompt-label").innerText = f"fefeh@fefehOS:{path_str}$"

def get_node_at_path(path_parts):
    node = VFS
    for part in path_parts:
        if not part:
            continue
        children = node.get("children", {})
        if part in children:
            node = children[part]
        else:
            return None
    return node

def resolve_target_path(target):
    if not target or target == "~" or target == "/":
        return []
    
    parts = target.split("/")
    new_path = CURRENT_DIR.copy() if not target.startswith("/") else []
    
    if target.startswith("/"):
        parts = parts[1:]
        
    for part in parts:
        if not part or part == ".":
            continue
        elif part == "..":
            if new_path:
                new_path.pop()
        else:
            test_node = get_node_at_path(new_path)
            if test_node and part in test_node.get("children", {}):
                if test_node["children"][part].get("type") == "directory":
                    new_path.append(part)
                else:
                    return None  # Não é diretório
            else:
                return None  # Não existe
    return new_path

def execute_command(cmd_line):
    global CURRENT_DIR
    parts = cmd_line.split()
    if not parts:
        return
        
    cmd = parts[0]
    args = parts[1:]
    
    path_str = "/" + "/".join(CURRENT_DIR)
    print_to_output(f"fefeh@fefehOS:{path_str}$ {cmd_line}", "command")
    
    if cmd == "clear":
        js.document.getElementById("output").innerHTML = ""
        
    elif cmd == "help":
        print_to_output("FefehOS TTY - Comandos suportados:", "info")
        print_to_output("  ls [-la] [path]  - Lista ficheiros e diretórios")
        print_to_output("  cd [path]        - Altera o diretório atual")
        print_to_output("  pwd              - Mostra o caminho absoluto atual")
        print_to_output("  cat <file>       - Exibe o conteúdo de um ficheiro")
        print_to_output("  uname [-a]       - Informações do sistema")
        print_to_output("  whoami           - Utilizador atual ativo")
        print_to_output("  history          - Histórico de comandos da sessão")
        print_to_output("  clear            - Limpa o ecrã do terminal")
        
    elif cmd == "whoami":
        print_to_output("fefeh")
        
    elif cmd == "uname":
        if args and "-a" in args:
            print_to_output("Linux fefehOS-tty 2026.9-arch #1 SMP PREWASM x86_64 GNU/Linux")
        else:
            print_to_output("FefehOS")
            
    elif cmd == "pwd":
        print_to_output("/" + "/".join(CURRENT_DIR))
        
    elif cmd == "history":
        for idx, hist_cmd in enumerate(COMMAND_HISTORY):
            print_to_output(f"  {idx+1}  {hist_cmd}")
            
    elif cmd == "ls":
        target_path = CURRENT_DIR
        show_all = False
        long_format = False
        
        for arg in args:
            if arg.startswith("-"):
                if "a" in arg: show_all = True
                if "l" in arg: long_format = True
            else:
                resolved = resolve_target_path(arg)
                if resolved is not None:
                    target_path = resolved
                else:
                    print_to_output(f"ls: aceder a '{arg}': Ficheiro ou diretório não encontrado", "error")
                    return
                    
        node = get_node_at_path(target_path)
        if node and node.get("type") == "directory":
            children = node.get("children", {})
            items = []
            for name, details in children.items():
                if not show_all and name.startswith('.'):
                    continue
                if long_format:
                    ftype = "d" if details.get("type") == "directory" else "-"
                    size = details.get("size", 4096)
                    items.append(f"{ftype}r-xr-x  1 fefeh fefeh {size:5d} 30 Sep 01:00 {name}")
                else:
                    items.append(name)
            
            if long_format:
                print_to_output(f"total {len(items)}")
                for item in items:
                    print_to_output(item)
            else:
                print_to_output("  ".join(items))
        else:
            print_to_output("ls: erro ao inspecionar diretório", "error")
            
    elif cmd == "cd":
        target = args[0] if args else "/"
        new_path = resolve_target_path(target)
        if new_path is not None:
            CURRENT_DIR = new_path
        else:
            print_to_output(f"cd: {target}: Diretório não encontrado ou inválido", "error")
            
    elif cmd == "cat":
        if not args:
            print_to_output("cat: falta argumento de ficheiro", "error")
        else:
            filename = args[0]
            node = get_node_at_path(CURRENT_DIR)
            if node and node.get("type") == "directory":
                file_node = node.get("children", {}).get(filename)
                if file_node and file_node.get("type") == "file":
                    content = file_node.get("content", "")
                    for line in content.split("\n"):
                        print_to_output(line)
                else:
                    print_to_output(f"cat: {filename}: É um diretório ou não existe", "error")
            else:
                print_to_output("cat: erro no contexto do diretório", "error")
    else:
        print_to_output(f"zsh: comando não encontrado: {cmd}", "error")

def handle_keydown(event):
    global HISTORY_INDEX, COMMAND_HISTORY
    input_el = js.document.getElementById("terminal-input")
    
    if event.key == "Enter":
        cmd_line = input_el.value.strip()
        if cmd_line:
            COMMAND_HISTORY.append(cmd_line)
            HISTORY_INDEX = len(COMMAND_HISTORY)
        input_el.value = ""
        execute_command(cmd_line)
        update_prompt()
        
    elif event.key == "ArrowUp":
        if COMMAND_HISTORY and HISTORY_INDEX > 0:
            HISTORY_INDEX -= 1
            input_el.value = COMMAND_HISTORY[HISTORY_INDEX]
        event.preventDefault()
        
    elif event.key == "ArrowDown":
        if COMMAND_HISTORY:
            if HISTORY_INDEX < len(COMMAND_HISTORY) - 1:
                HISTORY_INDEX += 1
                input_el.value = COMMAND_HISTORY[HISTORY_INDEX]
            else:
                HISTORY_INDEX = len(COMMAND_HISTORY)
                input_el.value = ""
        event.preventDefault()

# Inicialização do ambiente
load_vfs()
update_prompt()
print_to_output("FefehOS TTY [Versão 2026.9-WASM]", "info")
print_to_output("Digite 'help' para listar os comandos disponíveis.\n", "info")

input_element = js.document.getElementById("terminal-input")
input_element.addEventListener("keydown", create_proxy(handle_keydown))