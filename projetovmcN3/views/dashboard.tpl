<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - BMVC N3</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="/static/js/script.js"></script>
</head>
<body>
    <header>
        <h1>Gestão de Hardware (Nível 3)</h1>
        <div class="user-info">
            Usuário: <b>{{user}}</b> | <a href="/logout" class="btn-logout">Sair</a>
        </div>
    </header>

    <main>
        <div class="top-bar">
            <h3>Itens Cadastrados</h3>
            <a href="/novo" class="btn-novo">+ Novo Hardware</a>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Componente</th>
                    <th>Tipo</th>
                    <th>Estoque</th>
                    <th>Gerenciar</th>
                </tr>
            </thead>
            <tbody>
                % for item in itens:
                <tr>
                    <td>{{item.id}}</td>
                    <td>{{item.nome}}</td>
                    <td>{{item.tipo}}</td>
                    <td>{{item.quantidade}} un.</td>
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
</html>print("Usuário Operador Criado!")