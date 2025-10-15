# Salve este arquivo como: game.py
import pygame
from config import *
from utils import salvar_placar
from maze_generator import gerar_labirinto
from pathfinding import find_nearest_walkable_global
from entities import Player, Ghost

class Game:
    """Controla o fluxo principal e o estado do jogo (COMPOSIÇÃO)."""
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


