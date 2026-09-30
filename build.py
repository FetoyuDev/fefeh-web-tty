import os
import json
from pathlib import Path

# Diretórios base
ROOT_DIR = Path("fs_root")
OUTPUT_JSON = Path("fs.json")

def build_virtual_filesystem(current_path: Path) -> dict:
    fs_node = {}
    
    for item in current_path.iterdir():
        if item.name.startswith('.'):
            continue  # Ignora ficheiros ocultos indesejados (.git, etc.)
            
        relative_path = item.relative_to(ROOT_DIR)
        
        if item.is_dir():
            fs_node[item.name] = {
                "type": "directory",
                "children": build_virtual_filesystem(item)
            }
        elif item.is_file():
            # Lê o conteúdo do ficheiro para ficar acessível no VFS (ótimo para comandos tipo 'cat')
            try:
                content = item.read_text(encoding="utf-8")
            except Exception:
                content = "[Binary or unreadable content]"
                
            fs_node[item.name] = {
                "type": "file",
                "size": item.stat().st_size,
                "content": content
            }
            
    return fs_node

def main():
    if not ROOT_DIR.exists():
        print(f"[-] Erro: Diretório '{ROOT_DIR}' não encontrado. Cria a pasta com os assets primeiro.")
        return

    print("[*] A construir o Sistema de Ficheiros Virtual (VFS)...")
    vfs_data = {
        "type": "directory",
        "children": build_virtual_filesystem(ROOT_DIR)
    }

    # Grava o JSON final compactado ou formatado
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(vfs_data, f, ensure_ascii=False, indent=2)

    print(f"[+] VFS gerado com sucesso em '{OUTPUT_JSON}'!")

if __name__ == "__main__":
    main()