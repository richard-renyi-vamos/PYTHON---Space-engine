import pygame
import math

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Space Engine 🚀")

# Clock for FPS
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Spacecraft class
class Spacecraft:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 0  # Facing upwards
        self.speed = 0
        self.vx = 0
        self.vy = 0
        self.acceleration = 0.1
        self.friction = 0.99
        self.rotation_speed = 3
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, WHITE, [(20, 0), (0, 60), (40, 60)])
        self.original_image = self.image

    def rotate(self, direction):
        self.angle += self.rotation_speed * direction

    def thrust(self):
        rad = math.radians(self.angle)
        self.vx += math.sin(rad) * self.acceleration
        self.vy -= math.cos(rad) * self.acceleration

    def update(self):
        # Apply friction
        self.vx *= self.friction
        self.vy *= self.friction

        self.x += self.vx
        self.y += self.vy

        # Wrap around screen
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.original_image, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect.topleft)

# Create spaceship
ship = Spacecraft()

# Game loop
running = True
while running:
    screen.fill(BLACK)

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        ship.rotate(-1)
    if keys[pygame.K_RIGHT]:
        ship.rotate(1)
    if keys[pygame.K_UP]:
        ship.thrust()

    # Update
    ship.update()
    ship.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
