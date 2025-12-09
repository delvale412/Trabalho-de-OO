import sqlite3
import os
from config import DATABASE_FILE 

def carregar_placares():
    """
    Carrega os 10 maiores placares do banco de dados SQLite.
    """
    # Verifica se o banco de dados existe antes de tentar conectar
    if not os.path.exists(DATABASE_FILE):
        print(f"Aviso: Banco de dados '{DATABASE_FILE}' não encontrado.")
        print("Execute 'python database_setup.py' para criar o banco.")
        return []

    try:
        # Conecta ao banco de dados em modo somente leitura
        conn = sqlite3.connect(f"file:{DATABASE_FILE}?mode=ro&immutable=1", uri=True)
        cursor = conn.cursor()
        
        # Executa o comando SQL para selecionar e ordenar os placares
        cursor.execute("""
        SELECT nome, score 
        FROM placares 
        ORDER BY score DESC 
        LIMIT 10;
        """)
        
        entries = cursor.fetchall()
        return entries
        
    except sqlite3.OperationalError as e:
        print(f"Erro operacional ao carregar placares: {e}")
        print("Certifique-se de que o banco de dados e a tabela 'placares' existem.")
        return []
    except sqlite3.Error as e:
        print(f"Erro ao carregar placares do SQLite: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def salvar_placar(nome, score):
    """
    Salva um novo placar no banco de dados.
    - Se o nome não existir, cria um novo registro.
    - Se o nome existir e o novo score for MAIOR, atualiza o score.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Tenta inserir o novo placar
        # Se houver um CONFLITO (nome já existe), ele tenta o "DO UPDATE"
        # A condição "WHERE excluded.score > placares.score" garante
        # que a atualização só ocorra se o novo score for maior.
        
        cursor.execute("""
        INSERT INTO placares (nome, score, data_registro) 
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(nome) DO UPDATE SET
            score = excluded.score,
            data_registro = CURRENT_TIMESTAMP
        WHERE excluded.score > placares.score;
        """, (nome, score))
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Erro ao salvar/atualizar placar no SQLite: {e}")
    finally:
        if conn:
            conn.close()