<!DOCTYPE html>
<html>
<head>
    <title>Login - Projeto BMVC N3</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="login-body">
    <div class="login-box">
        <h2>Projeto BMVC N3</h2>
        <p>Acesso Restrito</p>
        % if erro:
            <p class="erro">{{erro}}</p>
        % end
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="Usuário" required>
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit">Entrar no Sistema</button>
        </form>
    </div>
</body>
</html>