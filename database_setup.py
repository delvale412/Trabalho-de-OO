import sqlite3
import os
from config import DATABASE_FILE

def criar_banco():
    """
    Cria o arquivo do banco de dados SQLite e a tabela 'placares' 
    se ela ainda não existir.
    """
    
    # Apaga o banco de dados antigo, se existir, para garantir a nova estrutura
    if os.path.exists(DATABASE_FILE):
        print(f"Encontrado '{DATABASE_FILE}' antigo. Removendo para recriar...")
        os.remove(DATABASE_FILE)
        
    print(f"Iniciando configuração do banco de dados: {DATABASE_FILE}")
    conn = None
    try:
        # Conecta ao banco (cria o arquivo)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS placares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(12) NOT NULL UNIQUE, 
            score INTEGER NOT NULL,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        print("Tabela 'placares' (com nomes únicos) criada com sucesso.")
        
    except sqlite3.Error as e:
        print(f"Erro ao configurar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    criar_banco()