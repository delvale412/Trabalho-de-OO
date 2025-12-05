<!DOCTYPE html>
<html>
<head>
    <title>{{acao}} - BMVC N3</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="form-container">
        <h2>{{acao}} Item</h2>
        
        % url = '/editar/' + str(item.id) if item else '/novo'
        
        <form action="{{url}}" method="POST">
            <label>Nome do Hardware:</label>
            <input type="text" name="nome" value="{{item.nome if item else ''}}" required>
            
            <label>Tipo (Ex: GPU, CPU):</label>
            <input type="text" name="tipo" value="{{item.tipo if item else ''}}" required>
            
            <label>Quantidade:</label>
            <input type="number" name="quantidade" value="{{item.quantidade if item else ''}}" required>
            
            <button type="submit">Salvar Alterações</button>
            <a href="/" class="btn-voltar">Cancelar</a>
        </form>
    </div>
</body>
</html>