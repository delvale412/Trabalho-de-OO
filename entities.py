# Salve este arquivo como: entities.py
import pygame
import math
import random
import collections
from config import *
from pathfinding import bfs_next_step, find_nearest_walkable_global

class GameObject:
    """Superclasse para todos os objetos móveis (HERANÇA)."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.anim_phase = random.uniform(0, 2 * math.pi)

    def draw(self, screen, frame):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError
    
    def get_pixel_pos(self):
        return (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2)

class Player(GameObject):
    """Classe que representa o jogador."""
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
        """Método update (POLIMORFISMO)."""
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
        """Método draw (POLIMORFISMO)."""
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
    """Classe que representa um fantasma."""
    def __init__(self, x, y, color, gtype):
        super().__init__(x, y)
        self.spawn_x, self.spawn_y = x, y
        self.color = color
        self.type = gtype
        self.state = "house"
        self.vul_timer = 0

    def update(self, maze, player, ghosts, blinky_ref):
        """Update do fantasma (ASSOCIAÇÃO com player)."""
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

