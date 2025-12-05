from bottle import Bottle, run, template, request, redirect, response, static_file
from models import HardwareModel
import sqlite3
import os

app = Bottle()
model = HardwareModel()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rotas Estáticas (CSS/JS)
@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=os.path.join(BASE_DIR, 'static'))

# Middleware de Segurança
def check_login():
    if not request.get_cookie("username", secret='chave-vmc-n3'):
        redirect('/login')

# Login
@app.route('/login')
def login():
    return template('views/login', erro=None)

@app.route('/login', method='POST')
def do_login():
    username = request.forms.get('username')
    password = request.forms.get('password')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        response.set_cookie("username", username, secret='chave-vmc-n3')
        redirect('/')
    else:
        return template('views/login', erro="Dados incorretos.")

@app.route('/logout')
def logout():
    response.delete_cookie("username")
    redirect('/login')

# CRUD
@app.route('/')
def index():
    check_login()
    lista = model.listar_todos()
    user = request.get_cookie("username", secret='chave-vmc-n3')
    return template('views/dashboard', itens=lista, user=user)

@app.route('/novo')
def novo():
    check_login()
    return template('views/editar', acao="Cadastrar", item=None)

@app.route('/novo', method='POST')
def novo_post():
    check_login()
    nome = request.forms.get('nome')
    tipo = request.forms.get('tipo')
    qtd = request.forms.get('quantidade')
    model.inserir(nome, tipo, qtd)
    redirect('/')

@app.route('/editar/<id:int>')
def editar(id):
    check_login()
    item = model.buscar_por_id(id)
    return template('views/editar', acao="Editar", item=item)

@app.route('/editar/<id:int>', method='POST')
def editar_post(id):
    check_login()
    nome = request.forms.get('nome')
    tipo = request.forms.get('tipo')
    qtd = request.forms.get('quantidade')
    model.atualizar(id, nome, tipo, qtd)
    redirect('/')

@app.route('/deletar/<id:int>')
def deletar(id):
    check_login()
    model.deletar(id)
    redirect('/')

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8080, debug=True)