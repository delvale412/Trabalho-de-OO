import os
import sqlite3
from bottle import Bottle, run, template, request, redirect, response, static_file, abort
# Importações necessárias para o WebSocket
from bottle.ext.websocket import GeventWebSocketServer
from gevent import monkey; monkey.patch_all()
from models import HardwareModel

app = Bottle()

# Configuração de caminhos para achar os arquivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(BASE_DIR, 'static')

# ---------------------------------------------------------
# LÓGICA DO WEBSOCKET (O CORAÇÃO DO NÍVEL 4)
# ---------------------------------------------------------
conexoes_ativas = set()

@app.route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    conexoes_ativas.add(wsock)
    print(f"Nova conexão WebSocket! Total: {len(conexoes_ativas)}")
    
    try:
        # Mantém a conexão aberta esperando mensagens (loop infinito)
        while True:
            message = wsock.receive()
            if message is None: break
    except:
        pass
    finally:
        conexoes_ativas.remove(wsock)
        print("Conexão fechada.")

def notificar_mudanca():
    """Envia 'atualizar' para todos os navegadores conectados"""
    to_remove = set()
    for ws in conexoes_ativas:
        try:
            ws.send("atualizar")
        except:
            to_remove.add(ws)
    for ws in to_remove:
        conexoes_ativas.remove(ws)

# ---------------------------------------------------------
# AUTENTICAÇÃO E ARQUIVOS ESTÁTICOS
# ---------------------------------------------------------
def check_login():
    username = request.get_cookie("username", secret='chave-vmc-n3')
    if not username:
        redirect('/login')
    return username

@app.route('/static/<filename:path>')
def server_static(filename):
    return static_file(filename, root=static_path)

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

# ---------------------------------------------------------
# ROTAS DO CRUD (AGORA COM NOTIFICAÇÃO)
# ---------------------------------------------------------

@app.route('/')
def index():
    user = check_login()
    model = HardwareModel()
    itens = model.listar_todos()
    return template('views/dashboard', user=user, itens=itens)

# --- CREATE (NOVO) ---
@app.route('/novo')
def novo_get():
    check_login()
    # Formulário simples com CSS injetado para ficar bonito
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Novo Item</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <header>
            <h1>Novo Hardware</h1>
            <div class="user-info"><a href="/">Voltar</a></div>
        </header>
        <main>
            <div class="form-box">
                <form action="/novo" method="POST">
                    <label>Nome:</label> <input type="text" name="nome" required>
                    <label>Tipo:</label> <input type="text" name="tipo" required>
                    <label>Qtd:</label>  <input type="number" name="quantidade" required>
                    <button type="submit" class="btn-novo">Cadastrar</button>
                </form>
            </div>
        </main>
    </body>
    </html>
    '''

@app.route('/novo', method='POST')
def novo_post():
    check_login()
    nome = request.forms.get('nome')
    tipo = request.forms.get('tipo')
    qtd = request.forms.get('quantidade')
    
    model = HardwareModel()
    model.inserir(nome, tipo, qtd)
    
    # AQUI ESTÁ O SEGREDO DO NÍVEL 4:
    notificar_mudanca() 
    
    redirect('/')

# --- UPDATE (EDITAR) ---
@app.route('/editar/<id>')
def editar_get(id):
    check_login()
    model = HardwareModel()
    item = model.buscar_por_id(id)
    # Chama o arquivo views/editar.tpl que criamos com CSS
    return template('views/editar', item=item)

@app.route('/editar/<id>', method='POST')
def editar_post(id):
    check_login()
    nome = request.forms.get('nome')
    tipo = request.forms.get('tipo')
    qtd = request.forms.get('quantidade')
    
    model = HardwareModel()
    model.atualizar(id, nome, tipo, qtd)
    
    notificar_mudanca() # Avisa todos os navegadores
    redirect('/')

# --- DELETE ---
@app.route('/deletar/<id>')
def deletar(id):
    check_login()
    model = HardwareModel()
    model.deletar(id)
    
    notificar_mudanca() # Avisa todos os navegadores
    redirect('/')

# ---------------------------------------------------------
# INICIALIZAÇÃO DO SERVIDOR ASSÍNCRONO
# ---------------------------------------------------------
if __name__ == '__main__':
    print("Servidor rodando na porta 8080 com suporte a WebSocket...")
    # Usamos GeventWebSocketServer em vez do servidor padrão
    run(app, host='0.0.0.0', port=8080, server=GeventWebSocketServer)