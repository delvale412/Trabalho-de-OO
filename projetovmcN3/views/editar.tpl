<!DOCTYPE html>
<html>
<head>
    <title>Editar Item</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header>
        <h1>Editar Hardware</h1>
        <div class="user-info"><a href="/">Voltar para Home</a></div>
    </header>

    <main>
        <div class="form-box">
            <form action="/editar/{{item.id}}" method="POST">
                <label>Nome do Componente:</label>
                <input type="text" name="nome" value="{{item.nome}}" required>
                
                <label>Tipo:</label>
                <input type="text" name="tipo" value="{{item.tipo}}" required>
                
                <label>Quantidade:</label>
                <input type="number" name="quantidade" value="{{item.quantidade}}" required>
                
                <button type="submit" class="btn-novo">Salvar Alterações</button>
            </form>
        </div>
    </main>
</body>
</html>