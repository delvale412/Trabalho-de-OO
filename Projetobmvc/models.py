import sqlite3

class Hardware:
    def __init__(self, id, nome, tipo, quantidade):
        self.id = id
        self.nome = nome
        self.tipo = tipo
        self.quantidade = quantidade

class HardwareModel:
    def __init__(self):
        self.db_name = 'database.db'

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def listar_todos(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hardware")
        rows = cursor.fetchall()
        conn.close()
        return [Hardware(row[0], row[1], row[2], row[3]) for row in rows]

    def buscar_por_id(self, id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hardware WHERE id=?", (id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Hardware(row[0], row[1], row[2], row[3])
        return None

    def inserir(self, nome, tipo, quantidade):
        conn = self.get_connection()
        conn.execute("INSERT INTO hardware (nome, tipo, quantidade) VALUES (?, ?, ?)", 
                     (nome, tipo, quantidade))
        conn.commit()
        conn.close()

    def atualizar(self, id, nome, tipo, quantidade):
        conn = self.get_connection()
        conn.execute("UPDATE hardware SET nome=?, tipo=?, quantidade=? WHERE id=?", 
                     (nome, tipo, quantidade, id))
        conn.commit()
        conn.close()

    def deletar(self, id):
        conn = self.get_connection()
        conn.execute("DELETE FROM hardware WHERE id=?", (id,))
        conn.commit()
        conn.close()