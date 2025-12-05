import sqlite3

def criar_banco():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Tabela de Usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL,
                 password TEXT NOT NULL)''')

    # Tabela de Hardware
    c.execute('''CREATE TABLE IF NOT EXISTS hardware (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nome TEXT NOT NULL,
                 tipo TEXT NOT NULL,
                 quantidade INTEGER NOT NULL)''')
    # Inserir usuário padrão
    c.execute("INSERT OR IGNORE INTO usuarios (id, username, password) VALUES (1, 'admin', '123')")
    
    c.execute("INSERT OR IGNORE INTO hardware (id, nome, tipo, quantidade) VALUES (1, 'RTX 4090', 'GPU', 3)")

    conn.commit()
    conn.close()
    print("Banco de dados criado com sucesso!")

if __name__ == '__main__':
    criar_banco()