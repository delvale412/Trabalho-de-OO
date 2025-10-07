import pygame
import sys
import math

# Inicialização
pygame.init()
pygame.mixer.init()

# Configurações Gerais
CELL_SIZE = 20
ROWS, COLS = 31, 28
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man Caveiras")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24, bold=True)

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AMARELO = (255, 255, 0)
VERMELHO = (255, 0, 0)
ROSA = (255, 184, 222)
CIANO = (0, 255, 255)
LARANJA = (255, 165, 0)
FANTASMA_AZUL = (33, 33, 255)
MAZE_AZUL = (0, 0, 255)
COR_PORTA_FANTASMA = (255, 184, 222)

# Layout do Labirinto
maze_layout = [
    "1111111111111011111111111111",
    "1222222222221122222222222221",
    "1211112111111111111121111121",
    "1311112111111111111121111131",
    "1211112111111111111121111121",
    "1222222222222222222222222221",
    "1211112111211111112111211111",
    "1222222111222112221112222221",
    "1111112111111111111121111111",
    "0000112111000110001112110000",
    "1111112111110110111121111111",
    "1111112111110110111121111111",
    "1111112111000220001112111111",
    "1111112111011441101112111111",
    "0000002000010001000002000000",
    "1111112111011111101112111111",
    "1111112111000000001112111111",
    "0000112111011111101112110000",
    "1111112111000000001112111111",
    "1222222222221122222222222221",
    "1211112111111111111121111121",
    "132211222222002222222112231",
    "1112112111211111112111211211",
    "1222222111222112221112222221",
    "1211111111111111111111111121",
    "1222222222222222222222222221",
    "1111111111111111111111111111",
    "1111111111111111111111111111",
    "1111111111111011111111111111",
    "1111111111111111111111111111",
    "1111111111111111111111111111",
]

maze = [[int(c) for c in row] for row in maze_layout]
SCATTER_TARGETS = {"VERMELHO": (COLS - 2, 1), "ROSA": (1, 1), "CIANO": (COLS - 2, ROWS - 3)}

# Classes
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.dx, self.dy = 0, 0
        self.score = 0
        self.lives = 3

    def move(self):
        new_x, new_y = self.x + self.dx, self.y + self.dy
        # Teletransporte lateral
        if new_x < 0: new_x = COLS - 1
        if new_x >= COLS: new_x = 0
        if new_y < 0: new_y = ROWS - 1
        if new_y >= ROWS: new_y = 0

        if maze[new_y][new_x] in [0, 2, 3, 4]:
            self.x, self.y = new_x, new_y
            if maze[self.y][self.x] == 2:
                self.score += 10
                maze[self.y][self.x] = 0
            elif maze[self.y][self.x] == 3:
                self.score += 50
                maze[self.y][self.x] = 0
                for ghost in ghosts: ghost.become_vulnerable()

    def draw(self):
        center = (int(self.x*CELL_SIZE + CELL_SIZE/2), int(self.y*CELL_SIZE + CELL_SIZE/2))
        radius = int(CELL_SIZE/2) - 2
        mouth = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2 * math.pi / 2
        if self.dx > 0: start, end = mouth, 2*math.pi - mouth
        elif self.dx < 0: start, end = math.pi + mouth, math.pi - mouth
        elif self.dy < 0: start, end = 1.5*math.pi + mouth, 1.5*math.pi - mouth
        else: start, end = 0.5*math.pi + mouth, 0.5*math.pi - mouth
        pygame.draw.arc(screen, AMARELO, (center[0]-radius, center[1]-radius, radius*2, radius*2), start, end, radius)

class Ghost:
    def __init__(self, x, y, color, name):
        self.x, self.y, self.name = x, y, name
        self.dx, self.dy = 0, -1
        self.start_x, self.start_y = x, y
        self.color = color
        self.mode = 'scatter'
        self.vulnerable_timer = 0

    def become_vulnerable(self):
        if self.mode != 'eaten':
            self.mode = 'vulnerable'
            self.vulnerable_timer = 500
            self.dx, self.dy = -self.dx, -self.dy

    def update(self, player_x, player_y, game_mode):
        if self.mode == 'vulnerable':
            self.vulnerable_timer -= 1
            if self.vulnerable_timer <= 0: self.mode = game_mode
        elif self.mode not in ['eaten', 'exiting']:
            self.mode = game_mode

        target_x, target_y = self.get_target(player_x, player_y)
        self.move_towards_target(target_x, target_y)

    def get_target(self, player_x, player_y):
        if self.mode == 'chase': return player_x, player_y
        if self.mode == 'scatter': return SCATTER_TARGETS[self.name]
        if self.mode == 'vulnerable': return player_x, player_y
        if self.mode == 'eaten': return 13, 14
        if self.mode == 'exiting': return 13, 11
        return self.x, self.y

    def move_towards_target(self, target_x, target_y):
        possible_moves = []
        all_directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dx, dy in all_directions:
            if (dx, dy) == (-self.dx, -self.dy): continue
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                if maze[ny][nx] in [0, 2, 3, 4]: possible_moves.append((dx, dy))

        if possible_moves:
            best_move = min(possible_moves, key=lambda m: math.hypot(self.x+m[0]-target_x, self.y+m[1]-target_y)) if self.mode != 'vulnerable' else max(possible_moves, key=lambda m: math.hypot(self.x+m[0]-target_x, self.y+m[1]-target_y))
            self.dx, self.dy = best_move
        else:
            self.dx, self.dy = -self.dx, -self.dy

        self.x += self.dx
        self.y += self.dy

        # Teletransporte lateral
        if self.x < 0: self.x = COLS-1
        if self.x >= COLS: self.x = 0
        if self.y < 0: self.y = ROWS-1
        if self.y >= ROWS: self.y = 0

        if self.mode == 'exiting' and (self.x, self.y) == (13, 11): self.mode = 'scatter'
        if self.mode == 'eaten' and (self.x, self.y) == (13, 14): self.mode = 'exiting'

    def draw(self):
        if self.mode == 'eaten': return
        center = (int(self.x*CELL_SIZE + CELL_SIZE/2), int(self.y*CELL_SIZE + CELL_SIZE/2))
        radius = int(CELL_SIZE/2) - 2
        if self.mode == 'vulnerable':
            color = FANTASMA_AZUL if (pygame.time.get_ticks() // 200) % 2 == 0 else BRANCO
        else:
            color = self.color

        # Desenho de caveira simples
        pygame.draw.circle(screen, color, center, radius)
        eye_offset = radius // 2
        pygame.draw.circle(screen, PRETO, (center[0]-eye_offset//2, center[1]-eye_offset//2), 2)
        pygame.draw.circle(screen, PRETO, (center[0]+eye_offset//2, center[1]-eye_offset//2), 2)
        pygame.draw.line(screen, PRETO, (center[0]-eye_offset//2, center[1]+eye_offset//2),
                         (center[0]+eye_offset//2, center[1]+eye_offset//2), 2)

# Funções
def draw_maze():
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            pos = (x*CELL_SIZE, y*CELL_SIZE)
            center = (pos[0]+CELL_SIZE//2, pos[1]+CELL_SIZE//2)
            if cell == 1: pygame.draw.rect(screen, MAZE_AZUL, (*pos, CELL_SIZE, CELL_SIZE))
            elif cell == 2: pygame.draw.circle(screen, BRANCO, center, 3)
            elif cell == 3: pygame.draw.circle(screen, LARANJA, center, 6)
            elif cell == 4: pygame.draw.rect(screen, COR_PORTA_FANTASMA, (pos[0], pos[1]+8, CELL_SIZE, 4))

def check_win(): return not any(2 in row or 3 in row for row in maze)

def check_collisions():
    global game_over
    for ghost in ghosts:
        if (player.x, player.y) == (ghost.x, ghost.y):
            if ghost.mode == 'vulnerable':
                player.score += 200
                ghost.mode = 'eaten'
            elif ghost.mode != 'eaten':
                player.lives -= 1
                if player.lives <= 0:
                    game_over = True
                else:
                    restart_game()
                return

def restart_game():
    global player, ghosts, maze
    player.x, player.y = 13, 22
    player.dx, player.dy = 0, 0
    for g in ghosts:
        g.x, g.y = g.start_x, g.start_y
        g.mode = 'scatter' if g.name == 'VERMELHO' else 'exiting'
    maze[:] = [[int(c) for c in row] for row in maze_layout]

def show_message(text):
    screen.fill(PRETO)
    message_surf = font.render(text, True, AMARELO)
    screen.blit(message_surf, message_surf.get_rect(center=(WIDTH/2, HEIGHT/2)))
    pygame.display.flip()
    pygame.time.wait(3000)

# Instâncias
player = Player(13, 22)
ghosts = [
    Ghost(13, 11, VERMELHO, 'VERMELHO'),
    Ghost(13, 14, ROSA, 'ROSA'),
    Ghost(11, 14, CIANO, 'CIANO')
]

game_mode = 'scatter'
mode_timer = 0
SCATTER_TIME, CHASE_TIME = 420, 1200
move_timer = 0
running, game_over, win = True, False, False

# Loop Principal
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: player.dx, player.dy = -1, 0
            elif event.key == pygame.K_RIGHT: player.dx, player.dy = 1, 0
            elif event.key == pygame.K_UP: player.dx, player.dy = 0, -1
            elif event.key == pygame.K_DOWN: player.dx, player.dy = 0, 1

    if not game_over and not win:
        mode_timer += 1
        if game_mode == 'scatter' and mode_timer > SCATTER_TIME: game_mode, mode_timer = 'chase', 0
        elif game_mode == 'chase' and mode_timer > CHASE_TIME: game_mode, mode_timer = 'scatter', 0

        move_timer += 1
        if move_timer >= 6:
            move_timer = 0
            player.move()
            check_collisions()
            for ghost in ghosts:
                ghost.update(player.x, player.y, game_mode)
            check_collisions()

        if check_win(): win = True

        screen.fill(PRETO)
        draw_maze()
        player.draw()
        for ghost in ghosts: ghost.draw()

        score_text = font.render(f"Score: {player.score}", True, BRANCO)
        lives_text = font.render(f"Vidas: {player.lives}", True, BRANCO)
        screen.blit(score_text, (10, HEIGHT-30))
        screen.blit(lives_text, (WIDTH-120, HEIGHT-30))

    if game_over: show_message(f"Game Over! Pontuação: {player.score}"); running = False
    if win: show_message(f"Você Venceu! Pontuação: {player.score}"); running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
