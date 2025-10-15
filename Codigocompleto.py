# Pac-Man Completo (Ficheiro Único)
# Este script combina todos os módulos do jogo num único ficheiro executável.

import sys
import os
import random
import math
import collections
import pygame
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QMessageBox, QDialog, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# -----------------------------------------------------------------------------
# Módulo: config.py
# -----------------------------------------------------------------------------
# Armazena todas as constantes e configurações do jogo.

# Configurações Gerais
CELL_SIZE = 20
ROWS, COLS = 31, 28
HUD_HEIGHT = 60
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE + HUD_HEIGHT
SCORES_FILE = "scores.txt"
FPS = 30
INITIAL_LIVES = 3

# Ajustes de Gameplay
SUPER_MODE_DURATION = 450   # Duração do super modo em frames
PLAYER_MOVE_DELAY = 4       # Delay para o movimento do jogador (frames)
GHOST_MOVE_DELAY = 6        # Delay para o movimento dos fantasmas (frames)

# Cores (RGB)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_WALL = (0, 0, 180)
COLOR_SPECIAL_DOT = (200, 0, 255)
COLOR_SPECIAL_DOT_BLINK = (120, 0, 120)
COLOR_GHOST_HOUSE = (80, 80, 80)
COLOR_VULNERABLE = (0, 0, 255)
COLOR_VULNERABLE_GHOST_BLINK = (200, 200, 255)
COLOR_EATEN_GHOST = (40, 40, 40)
COLOR_BLOOD = (150, 0, 0)
COLOR_JASON_MASK = (220, 220, 220)
COLOR_JASON_DETAILS = (100, 100, 100)
COLOR_JASON_MARKS = (180, 0, 0)
COLOR_MACHETE_HANDLE = (101, 67, 33)
COLOR_MACHETE_BLADE = (120, 120, 120)
COLOR_MACHETE_SHINE = (200, 200, 200)

# Cores dos Fantasmas
COLOR_BLINKY = (255, 0, 0)
COLOR_PINKY = (255, 184, 222)
COLOR_INKY = (0, 255, 255)
COLOR_CLYDE = (255, 165, 0)


# -----------------------------------------------------------------------------
# Módulo: utils.py
# -----------------------------------------------------------------------------
# Funções de suporte, como manipulação de ficheiros.

def carregar_placares():
    """Carrega os placares do ficheiro de texto."""
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        entries = []
        for ln in lines:
            if ";" in ln:
                n, s = ln.split(";", 1)
                try:
                    entries.append((n, int(s)))
                except ValueError:
                    pass
        return entries
    except IOError as e:
        print(f"Erro ao carregar placares: {e}")
        return []

def salvar_placar(nome, score):
    """Salva um novo placar no ficheiro de texto."""
    try:
        with open(SCORES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{nome};{score}\n")
    except IOError as e:
        print(f"Erro ao salvar placar: {e}")


# -----------------------------------------------------------------------------
# Módulo: maze_generator.py
# -----------------------------------------------------------------------------
# Contém a lógica para a geração procedural do labirinto.

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

    # Abre passagens extras para eliminar becos sem saída
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

    # Converte caminhos para tipos (ponto comum, ponto especial)
    for y in range(linhas):
        for x in range(colunas):
            if maze[y][x] == 0:
                if random.random() < 0.02:
                    maze[y][x] = 3  # Ponto especial
                else:
                    maze[y][x] = 2  # Ponto comum

    # Área central livre para os fantasmas
    mid_y, mid_x = linhas // 2, colunas // 2
    for i in range(-2, 3):
        for j in range(-2, 3):
            if 0 <= mid_y + i < linhas and 0 <= mid_x + j < colunas:
                maze[mid_y + i][mid_x + j] = 0
    maze[mid_y][mid_x] = 4 # Marca o centro da "casa dos fantasmas"

    return maze


# -----------------------------------------------------------------------------
# Módulo: pathfinding.py
# -----------------------------------------------------------------------------
# Algoritmos de busca para a IA dos fantasmas.

def bfs_next_step(start, target, maze):
    """
    Encontra o próximo passo do caminho mais curto de start a target usando BFS.
    Retorna a direção (dx, dy) a ser tomada.
    """
    sx, sy = start
    if start == target:
        return (0, 0)
    
    rows, cols = len(maze), len(maze[0])
    q = collections.deque([(sx, sy)])
    prev = {(sx, sy): None}

    while q:
        x, y = q.popleft()
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] != 1 and (nx, ny) not in prev:
                prev[(nx, ny)] = (x, y)
                if (nx, ny) == target:
                    cur = (nx, ny)
                    while prev[cur] is not None and prev[cur] != (sx, sy):
                        cur = prev[cur]
                    return (cur[0] - sx, cur[1] - sy)
                q.append((nx, ny))
    return (0, 0)

def find_nearest_walkable_global(maze, x, y):
    """
    Encontra a célula caminhável mais próxima de (x, y), caso a original não seja.
    Esta função precisa ser global no ficheiro único para ser acedida pela classe Game.
    """
    rows, cols = len(maze), len(maze[0])
    # Garante que as coordenadas sejam inteiros antes de usar como índices
    ix, iy = int(x), int(y)
    if 0 <= ix < cols and 0 <= iy < rows and maze[iy][ix] != 1:
        return ix, iy
    q = collections.deque([(ix, iy)])
    visited = {(ix, iy)}
    while q:
        cx, cy = q.popleft()
        for dx, dy in [(1,0),(-1,0),(0,1),(-1,0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in visited:
                if maze[ny][nx] != 1: return (nx, ny)
                visited.add((nx, ny))
                q.append((nx, ny))
    return (cols//2, rows//2)

# -----------------------------------------------------------------------------
# Módulo: entities.py
# -----------------------------------------------------------------------------
# Classes para as entidades do jogo, agora com Herança e Polimorfismo.

class GameObject:
    """
    Superclasse para todos os objetos móveis do jogo.
    Este é o pilar para a APLICAÇÃO DE HERANÇA.
    """
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.anim_phase = random.uniform(0, 2 * math.pi)

    def draw(self, screen, frame):
        raise NotImplementedError("A subclasse deve implementar o método draw.")

    def update(self, *args, **kwargs):
        raise NotImplementedError("A subclasse deve implementar o método update.")
    
    def get_pixel_pos(self):
        return (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2)

class Player(GameObject):
    """Classe que representa o jogador (Pac-Man). HERDA de GameObject."""
    def __init__(self, x, y):
        super().__init__(x, y) 
        self.dx, self.dy = 0, 0
        self.score = 0
        self.super_timer = 0
        self.is_dying = False
        self.death_animation_timer = 0
        self.blood_particles = []
        self.blood_trail = collections.deque(maxlen=100)

    def try_set_direction(self, ndx, ndy, maze):
        nx, ny = self.x + ndx, self.y + ndy
        if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] != 1:
            self.dx, self.dy = ndx, ndy

    def move(self, maze):
        nx, ny = self.x + self.dx, self.y + self.dy
        if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] != 1:
            self.x, self.y = nx, ny
            cell_type = maze[ny][nx]
            if cell_type == 2:
                maze[ny][nx] = 0
                self.score += 10
            elif cell_type == 3:
                maze[ny][nx] = 0
                self.score += 50
                return self.activate_super_mode()
        return None
    
    def activate_super_mode(self):
        self.super_timer = SUPER_MODE_DURATION
        return "SUPER_MODE_START"

    def update(self, frame):
        if self.is_dying:
            self.update_death_animation()
        else:
            self.anim_phase = (self.anim_phase + 0.3) % (2 * math.pi)
            if self.super_timer > 0:
                self.super_timer -= 1
                if self.super_timer == 0:
                    self.blood_trail.clear()
                if frame % 3 == 0:
                    x_pix, y_pix = self.get_pixel_pos()
                    self.blood_trail.appendleft({'pos': (x_pix + random.randint(-2, 2), y_pix + random.randint(-2, 2)), 'age': 0})
                for drop in self.blood_trail:
                    drop['age'] += 1

    def start_dying(self):
        self.is_dying = True
        self.death_animation_timer = 60
        self.blood_particles = []
        px, py = self.get_pixel_pos()
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            self.blood_particles.append({'x': px, 'y': py, 'dx': math.cos(angle) * speed, 'dy': math.sin(angle) * speed, 'life': random.randint(15, 30)})

    def update_death_animation(self):
        if not self.is_dying: return
        self.death_animation_timer -= 1
        for p in self.blood_particles:
            p['x'] += p['dx']; p['y'] += p['dy']; p['life'] -= 1
        self.blood_particles = [p for p in self.blood_particles if p['life'] > 0]
        if self.death_animation_timer <= 0:
            self.is_dying = False

    def draw(self, screen, frame):
        x_pix, y_pix = self.get_pixel_pos()
        for drop in self.blood_trail:
            alpha = max(0, 255 - drop['age'] * 5)
            radius = max(1, 5 - drop['age'] // 8)
            if alpha > 0 and radius > 0:
                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*COLOR_BLOOD, alpha), (radius, radius), radius)
                screen.blit(s, (int(drop['pos'][0] - radius), int(drop['pos'][1] - radius)))
        if self.is_dying:
            self._draw_death_effect(screen, x_pix, y_pix)
        elif self.super_timer > 0:
            self._draw_jason_mode(screen, x_pix, y_pix, frame)
        else:
            self._draw_normal_mode(screen, x_pix, y_pix)

    def _draw_death_effect(self, screen, x_pix, y_pix):
        pygame.draw.circle(screen, COLOR_RED, (x_pix, y_pix), CELL_SIZE // 2 - 2)
        for p in self.blood_particles:
            pygame.draw.circle(screen, COLOR_RED, (int(p['x']), int(p['y'])), random.randint(2, 4))
    
    def _draw_normal_mode(self, screen, x_pix, y_pix):
        angle_ampl = 30 * (0.5 + 0.5 * math.sin(self.anim_phase))
        if self.dx == 1: base = 0
        elif self.dx == -1: base = 180
        elif self.dy == -1: base = 90
        else: base = 270
        pygame.draw.circle(screen, COLOR_YELLOW, (x_pix, y_pix), CELL_SIZE // 2 - 2)
        a1 = math.radians(base - angle_ampl); a2 = math.radians(base + angle_ampl)
        p1 = (x_pix + math.cos(a1) * CELL_SIZE, y_pix - math.sin(a1) * CELL_SIZE)
        p2 = (x_pix + math.cos(a2) * CELL_SIZE, y_pix - math.sin(a2) * CELL_SIZE)
        pygame.draw.polygon(screen, COLOR_BLACK, [(x_pix, y_pix), p1, p2])

    def _draw_jason_mode(self, screen, x_pix, y_pix, frame):
        pygame.draw.circle(screen, COLOR_YELLOW, (x_pix, y_pix), CELL_SIZE // 2)
        mask_rect = (x_pix - 9, y_pix - 9, 18, 18)
        pygame.draw.ellipse(screen, COLOR_JASON_MASK, mask_rect)
        pygame.draw.ellipse(screen, (50, 50, 50), mask_rect, 1)
        pygame.draw.ellipse(screen, COLOR_BLACK, (x_pix - 6, y_pix - 5, 4, 6))
        pygame.draw.ellipse(screen, COLOR_BLACK, (x_pix + 2, y_pix - 5, 4, 6))
        pygame.draw.polygon(screen, COLOR_JASON_MARKS, [(x_pix, y_pix - 7), (x_pix - 2, y_pix - 3), (x_pix + 2, y_pix - 3)])
        pygame.draw.line(screen, COLOR_JASON_MARKS, (x_pix - 7, y_pix + 1), (x_pix - 3, y_pix + 5), 2)
        pygame.draw.line(screen, COLOR_JASON_MARKS, (x_pix + 7, y_pix + 1), (x_pix + 3, y_pix + 5), 2)
        angle_swing = math.sin(frame * 0.2) * 20
        weapon_angle_rad = math.radians(135 + angle_swing)
        handle_start = (x_pix + 6, y_pix - 6)
        handle_end = (handle_start[0] + 25 * math.cos(weapon_angle_rad), handle_start[1] - 25 * math.sin(weapon_angle_rad))
        pygame.draw.line(screen, COLOR_MACHETE_HANDLE, handle_start, handle_end, 5)
        blade_model = [(0, -3), (20, -6), (28, -2), (25, 5), (10, 3)]
        transformed_blade = []
        for mx, my in blade_model:
            rx = mx * math.cos(weapon_angle_rad) - my * math.sin(weapon_angle_rad)
            ry = mx * math.sin(weapon_angle_rad) + my * math.cos(weapon_angle_rad)
            transformed_blade.append((handle_end[0] + rx, handle_end[1] + ry))
        pygame.draw.polygon(screen, COLOR_MACHETE_BLADE, transformed_blade)
        pygame.draw.polygon(screen, COLOR_JASON_DETAILS, transformed_blade, 1)
        if len(transformed_blade) >= 3:
            pygame.draw.line(screen, COLOR_MACHETE_SHINE, transformed_blade[1], transformed_blade[2], 2)
        pygame.draw.circle(screen, COLOR_YELLOW, handle_start, 5)
        pygame.draw.circle(screen, COLOR_BLACK, handle_start, 5, 1)

class Ghost(GameObject):
    """Classe que representa um fantasma. HERDA de GameObject."""
    def __init__(self, x, y, color, gtype):
        super().__init__(x, y)
        self.spawn_x, self.spawn_y = x, y
        self.color = color
        self.type = gtype
        self.state = "house"
        self.vul_timer = 0

    def update(self, maze, player, ghosts, blinky_ref):
        if self.state == "house": return
        if self.state == "vulnerable":
            self.vul_timer -= 1
            if self.vul_timer <= 0: self.state = "chase"
        target = self._get_target_tile(player, blinky_ref, maze)
        ideal_dx, ideal_dy = bfs_next_step((self.x, self.y), target, maze)
        next_x, next_y = self.x + ideal_dx, self.y + ideal_dy
        is_stuck = (ideal_dx, ideal_dy) == (0,0)
        is_cong = any(g is not self and g.state != "eaten" and (g.x, g.y) == (next_x, next_y) for g in ghosts)
        if is_stuck or is_cong:
            moves = []
            for rdx, rdy in random.sample([(0,1),(0,-1),(1,0),(-1,0)], 4):
                nx, ny = self.x + rdx, self.y + rdy
                if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] != 1 and not any(g is not self and g.state!="eaten" and (g.x,g.y) == (nx,ny) for g in ghosts):
                    moves.append((rdx, rdy))
            final_dx, final_dy = moves[0] if moves else (0, 0)
        else:
            final_dx, final_dy = ideal_dx, ideal_dy
        self.x += final_dx; self.y += final_dy
        if self.state == "eaten" and (self.x, self.y) == (self.spawn_x, self.spawn_y):
            self.state = "chase"

    def _get_target_tile(self, player, blinky_ref, maze):
        if self.state == "eaten": return self.spawn_x, self.spawn_y
        if self.state == "vulnerable":
            corners = [(1, 1), (COLS - 2, 1), (1, ROWS - 2), (COLS - 2, ROWS - 2)]
            return max(corners, key=lambda c: abs(c[0] - player.x) + abs(c[1] - player.y))
        if self.type == "blinky": return find_nearest_walkable_global(maze, player.x, player.y)
        if self.type == "pinky":
            tx, ty = player.x + 4 * player.dx, player.y + 4 * player.dy
            return find_nearest_walkable_global(maze, tx, ty)
        if self.type == "inky":
            if blinky_ref:
                vx = player.x + (player.x - blinky_ref.x)
                vy = player.y + (player.y - blinky_ref.y)
                return find_nearest_walkable_global(maze, vx, vy)
            return find_nearest_walkable_global(maze, player.x, player.y)
        if self.type == "clyde":
            dist = abs(self.x - player.x) + abs(self.y - player.y)
            return find_nearest_walkable_global(maze, player.x, player.y) if dist > 8 else (1, ROWS - 2)
        return player.x, player.y

    def draw(self, screen, frame):
        offset = int(math.sin((frame + self.anim_phase) * 0.25) * 2)
        cx, cy = self.get_pixel_pos(); cy += offset
        if self.state == "vulnerable":
            color = COLOR_VULNERABLE if (self.vul_timer > 90 or (frame // 5) % 2 == 0) else COLOR_VULNERABLE_GHOST_BLINK
        elif self.state == "eaten":
            color = COLOR_EATEN_GHOST
        else:
            color = self.color
        pygame.draw.circle(screen, color, (cx, cy - 4), CELL_SIZE // 2 - 3)
        pygame.draw.rect(screen, color, (cx - CELL_SIZE // 2 + 3, cy - 4, CELL_SIZE - 6, CELL_SIZE // 2))
        if self.state != "eaten":
            for i in [-1, 1]:
                pygame.draw.circle(screen, COLOR_WHITE, (cx + i * 4, cy - 6), 4)
                pygame.draw.circle(screen, COLOR_BLACK, (cx + i * 4, cy - 6), 2)


# -----------------------------------------------------------------------------
# Módulo: game.py
# -----------------------------------------------------------------------------
# O coração do jogo. A classe Game encapsula todo o loop principal e o estado do jogo.

class Game:
    """Controla o fluxo principal, o estado e a renderização do jogo."""
    def __init__(self, player_name):
        pygame.init()
        self.player_name = player_name
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.game_surface = pygame.Surface((COLS * CELL_SIZE, ROWS * CELL_SIZE))
        pygame.display.set_caption(f"Pac-Man Jason - {player_name}")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.frame = 0
        self._load_assets()
        self._new_game()

    def _load_assets(self):
        self.font_hud = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_selascou = pygame.font.SysFont("Impact", 80)
        self.font_power = pygame.font.SysFont("Courier New", 28, bold=True, italic=True)
        self.font_game_over = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_esc = pygame.font.SysFont("Arial", 16)

    def _new_game(self):
        self.maze = gerar_labirinto()
        self._create_entities()
        self.lives = INITIAL_LIVES
        self.game_over = False; self.win = False; self.started = False
        self.is_paused_for_death = False; self.death_countdown = 0
        self.super_intro_countdown = 0; self.player_move_timer = 0; self.ghost_move_timer = 0

    def _create_entities(self):
        px, py = find_nearest_walkable_global(self.maze, COLS // 2, ROWS - 5)
        self.player = Player(px, py)
        cx, cy = next(((x, y) for y, r in enumerate(self.maze) for x, c in enumerate(r) if c == 4), (COLS//2, ROWS//2))
        self.ghosts = [
            Ghost(cx, cy, COLOR_BLINKY, "blinky"),
            Ghost(cx - 1, cy, COLOR_PINKY, "pinky"),
            Ghost(cx + 1, cy, COLOR_INKY, "inky"),
            Ghost(cx, cy - 1, COLOR_CLYDE, "clyde")
        ]
    
    def run(self):
        while self.is_running:
            self._handle_events(); self._update(); self._draw()
            self.clock.tick(FPS)
        pygame.quit()
        return self.player.score

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.is_running = False
            if event.type == pygame.KEYDOWN and not self.game_over and not self.is_paused_for_death:
                self.started = True
                if event.key == pygame.K_UP: self.player.try_set_direction(0, -1, self.maze)
                elif event.key == pygame.K_DOWN: self.player.try_set_direction(0, 1, self.maze)
                elif event.key == pygame.K_LEFT: self.player.try_set_direction(-1, 0, self.maze)
                elif event.key == pygame.K_RIGHT: self.player.try_set_direction(1, 0, self.maze)

    def _update(self):
        if self.game_over: return
        if self.super_intro_countdown > 0: self.super_intro_countdown -= 1; return
        if self.is_paused_for_death:
            self.player.update(self.frame)
            if not self.player.is_dying: self._handle_player_death_end()
            return
        if not self.started: return
        self._update_player(); self._update_ghosts(); self._check_collisions(); self._check_win_condition()
        self.frame += 1

    def _update_player(self):
        self.player_move_timer += 1
        if self.player_move_timer >= PLAYER_MOVE_DELAY:
            self.player_move_timer = 0
            event = self.player.move(self.maze)
            if event == "SUPER_MODE_START":
                self.super_intro_countdown = int(FPS * 1.5)
                for g in self.ghosts:
                    if g.state != "eaten": g.state = "vulnerable"; g.vul_timer = SUPER_MODE_DURATION
        self.player.update(self.frame)

    def _update_ghosts(self):
        for i, g in enumerate(self.ghosts):
            if g.state == "house" and self.frame > (i * 90 + 60): g.state = "chase"
        self.ghost_move_timer += 1
        if self.ghost_move_timer >= GHOST_MOVE_DELAY:
            self.ghost_move_timer = 0
            blinky_ref = next((g for g in self.ghosts if g.type == "blinky"), None)
            for g in self.ghosts: g.update(self.maze, self.player, self.ghosts, blinky_ref)

    def _check_collisions(self):
        for g in self.ghosts:
            if g.x == self.player.x and g.y == self.player.y:
                if g.state == "vulnerable": g.state = "eaten"; self.player.score += 200
                elif g.state != "eaten": self._handle_player_death(); break

    def _handle_player_death(self):
        self.lives -= 1
        self.player.start_dying()
        self.is_paused_for_death = True

    def _handle_player_death_end(self):
        self.is_paused_for_death = False
        if self.lives > 0: self._reset_positions()
        else: self.game_over = True; self.win = False; salvar_placar(self.player_name, self.player.score)

    def _reset_positions(self):
        self.started = False
        px, py = find_nearest_walkable_global(self.maze, COLS // 2, ROWS - 5)
        self.player.x, self.player.y = px, py; self.player.dx, self.player.dy = 0, 0
        self.player.super_timer = 0; self.player.blood_trail.clear()
        cx, cy = next(((x, y) for y, r in enumerate(self.maze) for x, c in enumerate(r) if c == 4), (COLS//2, ROWS//2))
        self.ghosts[0].x, self.ghosts[0].y = cx, cy
        self.ghosts[1].x, self.ghosts[1].y = cx-1, cy
        self.ghosts[2].x, self.ghosts[2].y = cx+1, cy
        self.ghosts[3].x, self.ghosts[3].y = cx, cy-1
        for g in self.ghosts: g.state = "house"

    def _check_win_condition(self):
        if not any(2 in row or 3 in row for row in self.maze):
            self.game_over = True; self.win = True; salvar_placar(self.player_name, self.player.score)

    def _draw(self):
        self.screen.fill((10, 10, 25)); self.game_surface.fill(COLOR_BLACK)
        self._draw_maze()
        if self.player.super_timer > 0 and not self.is_paused_for_death:
             self._draw_overlay(self.game_surface, (0,0,0,150))
        self.player.draw(self.game_surface, self.frame)
        for g in self.ghosts: g.draw(self.game_surface, self.frame)
        if self.is_paused_for_death: self._draw_death_screen()
        self.screen.blit(self.game_surface, (0, HUD_HEIGHT))
        self._draw_hud()
        if self.super_intro_countdown > 0: self._draw_super_intro()
        if self.game_over: self._draw_game_over_screen()
        pygame.display.flip()

    def _draw_maze(self):
        super_blink_state = (self.frame // 10) % 2 == 0
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                cx, cy = x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
                if cell == 1: pygame.draw.rect(self.game_surface, COLOR_WALL, rect)
                elif cell == 2: pygame.draw.circle(self.game_surface, COLOR_WHITE, (cx, cy), 3)
                elif cell == 3:
                    color = COLOR_SPECIAL_DOT if super_blink_state else COLOR_SPECIAL_DOT_BLINK
                    pygame.draw.circle(self.game_surface, color, (cx, cy), 6)
                elif cell == 4: pygame.draw.rect(self.game_surface, COLOR_GHOST_HOUSE, rect)

    def _draw_hud(self):
        score_text = self.font_hud.render(f"Score: {self.player.score}", True, COLOR_WHITE)
        self.screen.blit(score_text, (10, 15))
        lives_text = self.font_hud.render(f"Vidas: {self.lives}", True, COLOR_YELLOW)
        self.screen.blit(lives_text, (WIDTH // 2 - 40, 15))
        name_text = self.font_hud.render(f"{self.player_name}", True, COLOR_WHITE)
        name_rect = name_text.get_rect(right=WIDTH - 10, centery=HUD_HEIGHT / 2)
        self.screen.blit(name_text, name_rect)

    def _draw_death_screen(self):
        self._draw_overlay(self.game_surface, (0,0,0,180))
        selascou_surf = self.font_selascou.render("SELASCOU", True, (200, 0, 0))
        selascou_rect = selascou_surf.get_rect(center=(self.game_surface.get_width() / 2, self.game_surface.get_height() / 2))
        self.game_surface.blit(selascou_surf, selascou_rect)
        
    def _draw_super_intro(self):
        power_surf = self.font_power.render("ESTRIPAR E DILACERAR", True, (255, 100, 0))
        power_rect = power_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        self._draw_overlay(self.screen, (0,0,0,200))
        self.screen.blit(power_surf, power_rect)
        
    def _draw_game_over_screen(self):
        self._draw_overlay(self.screen, (0,0,0,180))
        msg = "VOCÊ VENCEU!" if self.win else "FIM DE JOGO"
        end_text = self.font_game_over.render(msg, True, COLOR_YELLOW)
        text_rect = end_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 20))
        self.screen.blit(end_text, text_rect)
        esc_text = self.font_esc.render("Pressione ESC para voltar ao menu", True, COLOR_WHITE)
        esc_rect = esc_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 30))
        self.screen.blit(esc_text, esc_rect)

    def _draw_overlay(self, surface, color):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(color)
        surface.blit(overlay, (0, 0))


# -----------------------------------------------------------------------------
# Módulo: ui.py
# -----------------------------------------------------------------------------
# Módulo para a interface gráfica do menu, usando PyQt6.

class PlacaresDialog(QDialog):
    """Janela de diálogo para exibir os placares."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Placares - Top 10")
        self.setFixedSize(360, 420)
        self.setStyleSheet("background-color: #0A0A0A; color: #FFD700;")
        layout = QVBoxLayout()
        title = QLabel("🏆 Placar de Líderes")
        title.setFont(QFont("Impact", 20))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        entries = carregar_placares()
        if not entries:
            txt = QLabel("Nenhum placar registado ainda.")
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(txt)
        else:
            entries_sorted = sorted(entries, key=lambda x: x[1], reverse=True)[:10]
            text_edit = QTextEdit(); text_edit.setReadOnly(True)
            text_edit.setStyleSheet("background-color: #111; color: #FFD700; font-family: 'Courier New', monospace; border: 1px solid #FFD700; padding: 5px;")
            content = "\n".join([f"{i+1:2d}. {n:<12}  {p:6d}" for i, (n, p) in enumerate(entries_sorted)])
            text_edit.setText(content); layout.addWidget(text_edit)
        btn_close = QPushButton("Fechar")
        btn_close.setStyleSheet("background-color:#222; color: yellow; border:1px solid yellow; padding:8px;")
        btn_close.clicked.connect(self.accept); layout.addWidget(btn_close)
        self.setLayout(layout)

class MenuPrincipal(QWidget):
    """A janela principal do menu do jogo."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pac-Man Jason"); self.setFixedSize(420, 380)
        self.layout = QVBoxLayout(); self.setStyleSheet("background-color: #0A0A0A; color: white;")
        self._setup_ui()
        self.btn_jogar.clicked.connect(self.on_jogar)
        self.btn_placares.clicked.connect(self.on_placares)
        self.btn_sair.clicked.connect(self.close)

    def _setup_ui(self):
        titulo = QLabel("PAC-MAN"); titulo.setFont(QFont("Impact", 48, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter); titulo.setStyleSheet("color: #FFD700;")
        self.layout.addWidget(titulo)
        subtitle = QLabel("A Vingança de Jason"); subtitle.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter); subtitle.setStyleSheet("color: #FF4444; margin-bottom: 15px;")
        self.layout.addWidget(subtitle)
        self.nome_input = QLineEdit(); self.nome_input.setPlaceholderText("Digite o seu nome")
        self.nome_input.setMaxLength(12); self.nome_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nome_input.setStyleSheet("padding:10px; font-size:16px; background:#111; color:#FFD700; border:1px solid #444; border-radius: 5px;")
        self.layout.addWidget(self.nome_input)
        btn_container = QHBoxLayout()
        self.btn_jogar = QPushButton("🎮 Jogar"); self.btn_placares = QPushButton("🏆 Placares"); self.btn_sair = QPushButton("❌ Sair")
        button_style = "QPushButton { background-color: #FFD700; color: black; border: none; padding: 12px; font-size: 16px; font-weight: bold; border-radius: 5px; } QPushButton:hover { background-color: #FFFF44; }"
        for btn in (self.btn_jogar, self.btn_placares, self.btn_sair):
            btn.setStyleSheet(button_style); btn.setFixedHeight(50); btn_container.addWidget(btn)
        self.layout.addLayout(btn_container); self.setLayout(self.layout)

    def on_jogar(self):
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "Digite o seu nome antes de jogar!")
            return
        self.hide()
        game_instance = Game(nome)
        score = game_instance.run()
        QMessageBox.information(self, "Fim de jogo", f"{nome}, a sua pontuação final foi: {score}")
        self.show()

    def on_placares(self):
        dlg = PlacaresDialog(self); dlg.exec()


# -----------------------------------------------------------------------------
# Ponto de Entrada Principal (main.py)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MenuPrincipal()
    menu.show()
    sys.exit(app.exec())
