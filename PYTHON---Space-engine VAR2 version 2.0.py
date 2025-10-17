"""
space_engine.py
A simple 2D "Space Engine" style sandbox written in Python + Pygame.

Extended Features 🚀:
- Orbit trails for the ship (visualize motion)
- Fuel system (limited thrust resource)
- Mini-map radar (overview of all objects)
"""

import sys
import math
import random
import pygame
import numpy as np
from dataclasses import dataclass

# ---------- Config ----------
WIDTH, HEIGHT = 1280, 800
FPS = 60
G = 6.67430e-1  # scaled gravitational constant
STAR_COUNT = 300

# ---------- Utility ----------

def clamp(x, a, b):
    return max(a, min(b, x))

def vec2(x=0.0, y=0.0):
    return np.array([x, y], dtype=float)

# ---------- Entities ----------

@dataclass
class Planet:
    pos: np.ndarray
    mass: float
    radius: float
    color: pygame.Color

@dataclass
class Ship:
    pos: np.ndarray
    vel: np.ndarray
    angle: float
    angular_vel: float
    thrust: float
    fuel: float = 100.0  # NEW FEATURE: Ship starts with full fuel (100%)

# ---------- Engine ----------

class SpaceEngine:
    def __init__(self, w=WIDTH, h=HEIGHT):
        pygame.init()
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption("Space Engine - Python Sandbox")
        self.clock = pygame.time.Clock()
        self.w, self.h = w, h

        # Camera
        self.cam_pos = vec2(0, 0)
        self.zoom = 1.0

        # Starfield
        self.stars = [vec2(random.uniform(-4000, 4000), random.uniform(-4000, 4000)) for _ in range(STAR_COUNT)]

        # Entities
        self.planets = []
        self.ship = self.create_default_ship()

        # Input
        self.running = True
        self.paused = False

        # UI
        self.font = pygame.font.SysFont("consolas", 16)

        # NEW FEATURE: Ship orbit trail
        self.trails = []
        self.max_trail_length = 500

        self.reset()

    def create_default_ship(self):
        return Ship(pos=vec2(0, -300), vel=vec2(40, 0), angle=math.radians(90), angular_vel=0.0, thrust=120.0)

    def reset(self):
        self.planets = [
            Planet(pos=vec2(0, 0), mass=20000.0, radius=40, color=pygame.Color(90, 100, 255)),
            Planet(pos=vec2(-600, 200), mass=8000.0, radius=28, color=pygame.Color(200, 120, 80)),
        ]
        self.ship = self.create_default_ship()
        self.cam_pos = vec2(0, 0)
        self.zoom = 1.0
        self.trails.clear()  # NEW FEATURE: clear trails on reset

    # Coordinate conversions
    def world_to_screen(self, world_pos):
        s = (world_pos - self.cam_pos) * self.zoom + vec2(self.w / 2.0, self.h / 2.0)
        return int(s[0]), int(s[1])

    def screen_to_world(self, screen_pos):
        sp = vec2(screen_pos[0], screen_pos[1])
        return (sp - vec2(self.w / 2.0, self.h / 2.0)) / self.zoom + self.cam_pos

    # Gravity physics
    def compute_gravity(self, position):
        total_acc = vec2(0.0, 0.0)
        for p in self.planets:
            r = p.pos - position
            dist2 = max((r[0] ** 2 + r[1] ** 2), (p.radius * 0.5) ** 2)
            dist = math.sqrt(dist2)
            acc_mag = G * p.mass / dist2
            total_acc += (r / dist) * acc_mag
        return total_acc

    # Drawing
    def draw_starfield(self):
        for s in self.stars:
            sx, sy = self.world_to_screen(s * 0.5)
            if 0 <= sx < self.w and 0 <= sy < self.h:
                size = 1 if random.random() > 0.995 else 2
                self.screen.fill((255, 255, 255), (sx, sy, size, size))

    def draw_planets(self):
        for p in self.planets:
            sx, sy = self.world_to_screen(p.pos)
            r = max(2, int(p.radius * self.zoom))
            pygame.draw.circle(self.screen, p.color, (sx, sy), r)
            for i in range(1, 4):
                alpha = max(0, 50 - i * 12)
                surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*p.color[:3], alpha), (r * 2, r * 2), int(r * (1 + i * 0.25)))
                self.screen.blit(surf, (sx - r * 2, sy - r * 2))

    # NEW FEATURE: Draw orbit trails
    def draw_trails(self):
        if len(self.trails) > 2:
            pts = [self.world_to_screen(p) for p in self.trails]
            pygame.draw.lines(self.screen, (100, 200, 255), False, pts, 1)

    def draw_ship(self):
        s = self.ship
        pts = [vec2(0, -10), vec2(-7, 8), vec2(7, 8)]
        rot = np.array([[math.cos(s.angle), -math.sin(s.angle)], [math.sin(s.angle), math.cos(s.angle)]])
        world_pts = [self.world_to_screen(s.pos + rot.dot(p) * 2.5) for p in pts]
        pygame.draw.polygon(self.screen, (255, 220, 120), world_pts)

        # Thrust flame
        if getattr(self, 'applying_thrust', False):
            flame_pts = [vec2(0, 14), vec2(-5, 9), vec2(5, 9)]
            flame_world = [self.world_to_screen(s.pos + rot.dot(p) * 2.5) for p in flame_pts]
            pygame.draw.polygon(self.screen, (255, 120, 30), flame_world)

    def draw_hud(self, dt):
        s = self.ship
        spd = math.sqrt(s.vel[0] ** 2 + s.vel[1] ** 2)
        lines = [
            f"Pos: ({s.pos[0]:.1f}, {s.pos[1]:.1f})",
            f"Vel: {spd:.1f} u/s",
            f"Angle: {math.degrees(s.angle)%360:.1f}°",
            f"Fuel: {s.fuel:.1f}%",  # NEW FEATURE: Fuel display
            f"Planets: {len(self.planets)}",
            f"Zoom: {self.zoom:.2f}",
            f"FPS: {int(self.clock.get_fps())}"
        ]
        y = 8
        for ln in lines:
            surf = self.font.render(ln, True, (220, 220, 220))
            self.screen.blit(surf, (8, y))
            y += 18

    # NEW FEATURE: Mini-map radar
    def draw_minimap(self):
        surf = pygame.Surface((200, 200))
        surf.fill((10, 10, 30))
        cx, cy = 100, 100
        for p in self.planets:
            x = int(cx + (p.pos[0] - self.ship.pos[0]) * 0.05)
            y = int(cy + (p.pos[1] - self.ship.pos[1]) * 0.05)
            if 0 <= x < 200 and 0 <= y < 200:
                pygame.draw.circle(surf, p.color, (x, y), 3)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 4)
        self.screen.blit(surf, (self.w - 210, 10))

    # Input & logic
    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    self.zoom *= 1.1
                elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                    self.zoom /= 1.1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    world = self.screen_to_world((mx, my))
                    mass = random.uniform(2000, 20000)
                    radius = clamp(int(math.sqrt(mass) * 0.8), 6, 80)
                    color = pygame.Color(random.randint(80, 255), random.randint(80, 255), random.randint(80, 255))
                    self.planets.append(Planet(pos=world, mass=mass, radius=radius, color=color))
                elif event.button == 3:
                    world = self.screen_to_world((mx, my))
                    if self.planets:
                        dists = [np.linalg.norm(p.pos - world) for p in self.planets]
                        idx = int(np.argmin(dists))
                        if dists[idx] < 80:
                            del self.planets[idx]

    def update(self, dt):
        if self.paused:
            return

        keys = pygame.key.get_pressed()
        s = self.ship

        # rotation
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            s.angle -= 2.5 * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            s.angle += 2.5 * dt

        # thrust + NEW FEATURE: fuel consumption
        thrusting = False
        if s.fuel > 0:
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                forward = vec2(math.cos(s.angle - math.pi / 2), math.sin(s.angle - math.pi / 2))
                s.vel += forward * (s.thrust * dt)
                s.fuel = max(0, s.fuel - 10 * dt)
                thrusting = True
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                back = vec2(math.cos(s.angle + math.pi / 2), math.sin(s.angle + math.pi / 2))
                s.vel += back * (s.thrust * 0.5 * dt)
                s.fuel = max(0, s.fuel - 5 * dt)
                thrusting = True

        self.applying_thrust = thrusting

        # gravity
        acc = self.compute_gravity(s.pos)
        s.vel += acc * dt
        s.pos += s.vel * dt

        # trail update
        self.trails.append(s.pos.copy())
        if len(self.trails) > self.max_trail_length:
            self.trails.pop(0)

        # camera follow
        self.cam_pos += (s.pos - self.cam_pos) * 0.05

    def render(self):
        self.screen.fill((6, 8, 20))
        self.draw_starfield()
        self.draw_trails()       # NEW FEATURE
        self.draw_planets()
        self.draw_ship()
        self.draw_hud(self.clock.get_time() / 1000.0)
        self.draw_minimap()      # NEW FEATURE
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()

# ---------- Launcher ----------
if __name__ == '__main__':
    engine = SpaceEngine()
    engine.run()
