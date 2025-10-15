# Salve este arquivo como: utils.py
import os
from config import SCORES_FILE

def carregar_placares():
    """Carrega os placares do ficheiro de texto."""
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        entries = []
        for ln in lines:
            if ";" in ln:
                n, s = ln.split(";", 1)
                try:
                    entries.append((n, int(s)))
                except ValueError:
                    pass
        return entries
    except IOError as e:
        print(f"Erro ao carregar placares: {e}")
        return []

def salvar_placar(nome, score):
    """Salva um novo placar no ficheiro de texto."""
    try:
        with open(SCORES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{nome};{score}\n")
    except IOError as e:
        print(f"Erro ao salvar placar: {e}")

