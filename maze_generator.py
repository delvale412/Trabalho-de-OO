# Salve este arquivo como: maze_generator.py
import random
from config import ROWS, COLS

def gerar_labirinto(linhas=ROWS, colunas=COLS):
    """Gera um labirinto aleatório usando DFS e remove becos sem saída."""
    if linhas % 2 == 0: linhas -= 1
    if colunas % 2 == 0: colunas -= 1
    maze = [[1 for _ in range(colunas)] for _ in range(linhas)]

    def vizinhos_validos(x, y):
        v = []
        if x > 1: v.append((x - 2, y))
        if x < colunas - 2: v.append((x + 2, y))
        if y > 1: v.append((x, y - 2))
        if y < linhas - 2: v.append((x, y + 2))
        random.shuffle(v)
        return v

    def dfs(x, y):
        maze[y][x] = 0
        for nx, ny in vizinhos_validos(x, y):
            if maze[ny][nx] == 1:
                maze[(y + ny) // 2][(x + nx) // 2] = 0
                dfs(nx, ny)

    start_x = random.randrange(1, colunas, 2)
    start_y = random.randrange(1, linhas, 2)
    dfs(start_x, start_y)

    alterado = True
    while alterado:
        alterado = False
        for y in range(1, linhas - 1):
            for x in range(1, colunas - 1):
                if maze[y][x] == 0:
                    vizinhos = sum(
                        maze[yy][xx] == 0
                        for yy, xx in [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
                    )
                    if vizinhos <= 1:
                        direcoes = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                        random.shuffle(direcoes)
                        for dx, dy in direcoes:
                            nx, ny = x + dx, y + dy
                            if 0 < nx < colunas - 1 and 0 < ny < linhas - 1 and maze[ny][nx] == 1:
                                maze[ny][nx] = 0
                                alterado = True
                                break

    for y in range(linhas):
        for x in range(colunas):
            if maze[y][x] == 0:
                if random.random() < 0.02:
                    maze[y][x] = 3
                else:
                    maze[y][x] = 2

    mid_y, mid_x = linhas // 2, colunas // 2
    for i in range(-2, 3):
        for j in range(-2, 3):
            if 0 <= mid_y + i < linhas and 0 <= mid_x + j < colunas:
                maze[mid_y + i][mid_x + j] = 0
    maze[mid_y][mid_x] = 4

    return maze
