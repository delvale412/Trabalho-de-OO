<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - BMVC IV</title>
    <link rel="stylesheet" href="/static/css/style.css">
    
    <script>
        function connect() {
            var ws = new WebSocket("ws://" + window.location.host + "/websocket");
            ws.onmessage = function(evt) {
                if (evt.data === "atualizar") {
                    window.location.reload(); 
                }
            };
            ws.onclose = function() { setTimeout(connect, 5000); };
        }
        window.onload = connect;

        function confirmarDelecao() {
            return confirm("Tem certeza que deseja excluir este item?");
        }
    </script>
</head>
<body>
    <header>
        <h1>Gestão de Hardware</h1>
        <div class="user-info">Usuário: <b>{{user}}</b> | <a href="/logout">Sair</a></div>
    </header>

    <main>
        <h3>Itens em Estoque</h3>
        <a href="/novo" class="btn-novo">+ Novo Item</a>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Nome</th><th>Tipo</th><th>Qtd</th><th>Ações</th>
                </tr>
            </thead>
            <tbody>
                % for item in itens:
                <tr>
                    <td>{{item.id}}</td>
                    <td>{{item.nome}}</td>
                    <td>{{item.tipo}}</td>
                    <td style="font-weight:bold;">{{item.quantidade}}</td>
                    <td>
                        <a href="/editar/{{item.id}}" class="btn-edit">Editar</a>
                        <a href="/deletar/{{item.id}}" class="btn-delete" onclick="return confirmarDelecao()">Excluir</a>
                    </td>
                </tr>
                % end
            </tbody>
        </table>
    </main>
</body>
</html>