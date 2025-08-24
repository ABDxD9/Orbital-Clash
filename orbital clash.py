# cosmic_advent_fixed.py
"""
Cosmic Adventure: The Journey of Star (fixed)
- Single-file game
- Put images next to this file (see asset list in comment)
Run:
    python cosmic_advent_fixed.py
"""

import pygame
import random
import math
import sys
import os

# === CONFIG ===
WIDTH, HEIGHT = 600, 600
FPS = 45

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (60, 60, 60)
GREEN = (60, 255, 60)
YELLOW = (255, 255, 80)
BLUE = (80, 180, 255)
ORANGE = (255, 180, 80)
FUEL_BAR_COLOR = (80, 255, 80)
HEART_COLOR = (255, 80, 80)
HALF_HEART_COLOR = (255, 180, 180)
RED = (255, 60, 60)
GRAY = (160, 160, 160)

# HUD positions / moved controls to the right
HUD_SCORE_POS = (24, 18)
HUD_FUEL_POS = (24, 44)
HUD_HEARTS_POS = (24, 72)
HUD_WEAPON_POS = (WIDTH - 220, 18)
HUD_LEVEL_POS = (WIDTH - 60, 18)
HUD_CONTROLS_POS = (WIDTH - 180, HEIGHT - 140)  # shifted right

# Player
PLAYER_START_HEARTS = 5.0
PLAYER_MAX_HEARTS = 5.0
PLAYER_START_FUEL = 100
PLAYER_MAX_FUEL = 100
PLAYER_SHIP_W, PLAYER_SHIP_H = 64, 64
PLAYER_ACCEL = 0.5
PLAYER_MAX_SPEED = 12
PLAYER_BASE_SPEED = 2
PLAYER_FUEL_DRAIN = 0.015
PLAYER_FUEL_DRAIN_BOOST = 0.03
PLAYER_INVINCIBLE_TIME = 60  # frames (we'll subtract dt*FPS)

# Weapons config
WEAPON_CONFIG = {
    "minigun": {"magazine": 50, "rps": 14, "damage": 10, "spread": 7, "reload_time": 2.0},
    "shotgun": {"rps": 0.8, "pellets": 3, "damage": 12, "spread_angle": 18, "reload_time": 0.0},
    "laser": {"charge_time": 0.7, "beam_duration": 4.5, "dps": 30, "charges": 2, "cooldown": 5.0, "width": 24},
    "missile": {"windup": 1.0, "cooldown": 3.0, "capacity": 3, "explosion_radius": 150, "damage": 100},
}

# Asteroid tiers (5)
ASTEROID_TIERS = [
    {"name": "Tiny", "radius": 12, "hp": 2, "speed": (6, 9), "color": (220, 220, 220)},
    {"name": "Small", "radius": 20, "hp": 5, "speed": (4, 7), "color": (180, 180, 180)},
    {"name": "Medium", "radius": 32, "hp": 12, "speed": (2, 5), "color": (120, 120, 120)},
    {"name": "Large", "radius": 48, "hp": 28, "speed": (1, 3), "color": (100, 100, 100)},
    {"name": "Titan", "radius": 64, "hp": 60, "speed": (1, 2), "color": (80, 80, 80)},
]

# Alien types (4)
ALIEN_TYPES = [
    {"name": "Normal", "color": (255, 80, 80), "hp": 8, "speed": 3, "fire_rate": 1.8, "damage": 0.5},
    {"name": "Rapid", "color": (255, 180, 80), "hp": 5, "speed": 4, "fire_rate": 0.8, "damage": 0.5},
    {"name": "Tank", "color": (120, 255, 120), "hp": 20, "speed": 2, "fire_rate": 2.6, "damage": 1.0},
    {"name": "Dart", "color": (80, 180, 255), "hp": 6, "speed": 7, "fire_rate": 1.5, "damage": 0.5},
]

# Powerups
POWERUP_TYPES = [
    {"type": "shield", "color": (0, 200, 255)},
    {"type": "firerate", "color": (255, 200, 0)},
    {"type": "heal", "color": (0, 255, 0)},
    {"type": "heal1.5", "color": (255, 120, 200)},
    {"type": "fuel", "color": (255, 255, 120)},
    {"type": "missile", "color": (255, 120, 0)},
]

# Planets keys (images)
PLANET_KEYS = ["rocky", "blue", "green"]
PLANET_COLORS = [(180, 180, 255), (255, 220, 120), (120, 255, 180), (255, 120, 180), (200, 200, 200)]

# Spawn tuning
CHUNK_HEIGHT = 180
STAR_COUNT = 90
PLANET_CHANCE = 0.06

CHUNK_ASTEROID_BASE = 2
CHUNK_ASTEROID_VARIANCE = 3
# increase overall alien chance and increase Tank & Dart presence
ALIEN_BASE_CHANCE = 0.192
POWERUP_FUEL_EVERY = 2
POWERUP_SPECIAL_EVERY = 3
RANDOM_POWERUP_BASE_CHANCE = 0.09

# Globals (runtime)
screen = None
clock = None
font = None
big_font = None
small_font = None

# ASSETS (images). Fill by load_assets()
ASSETS = {
    "ship": None,
    "planets": {},
    "heart": None,
    "half_heart": None,
    "missile": None,
    "shield": None,
    "bg": None,
    "powerups": {},  # powerup type -> image
}
ALIEN_IMAGES = {}     # name -> surface
ASTEROID_IMAGES = {}  # tier name -> surface

# Asset filenames you can drop into project folder:
# spaceship.png
# planet_1.png, planet_2.png, planet_3.png
# heart.png, half_heart.png
# missile.png
# shield.png
# alien_normal.png, alien_rapid.png, alien_tank.png, alien_dart.png
# as_1.png .. as_5.png
# space.jpg
# power_fuel.png, power_heal.png, power_missile.png, power_shield.png, power_firerate.png

def safe_load(path, size=None):
    if not path:
        return None
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        return None

def load_assets():
    # background
    ASSETS["bg"] = safe_load("assets/space.jpg", (WIDTH, HEIGHT))
    # ship
    ASSETS["ship"] = safe_load("assets/spaceship.png", (PLAYER_SHIP_W, PLAYER_SHIP_H))
    # planets
    ASSETS["planets"]["rocky"] = safe_load("assets/planet_1.png")
    ASSETS["planets"]["blue"] = safe_load("assets/planet_2.png")
    ASSETS["planets"]["green"] = safe_load("assets/planet_3.png")
    # hearts
    ASSETS["heart"] = safe_load("assets/heart.png", (26, 26))
    ASSETS["half_heart"] = safe_load("assets/half_heart.png", (26, 26))
    # missile & shield icon
    ASSETS["missile"] = safe_load("assets/missile.png", (16, 32))
    ASSETS["shield"] = safe_load("assets/shield.png", (28, 28))
    # powerups images (optional)
    ASSETS["powerups"]["fuel"] = safe_load("assets/power_fuel.png", (64, 64))
    ASSETS["powerups"]["heal"] = safe_load("assets/heart.png", (64, 64))
    ASSETS["powerups"]["missile"] = safe_load("assets/missile.png", (64, 64))
    ASSETS["powerups"]["shield"] = safe_load("assets/power_shield.png", (64, 64))
    ASSETS["powerups"]["firerate"] = safe_load("assets/power_firerate.png", (86, 86))

    # Aliens (per type)
    ALIEN_IMAGES["Normal"] = safe_load("assets/alien_normal.png", (44, 28)) or safe_load("assets/alien_small.png", (44, 28))
    ALIEN_IMAGES["Rapid"] = safe_load("assets/alien_rapid.png", (64, 48))
    ALIEN_IMAGES["Tank"] = safe_load("assets/alien_tank.png", (96, 96))
    ALIEN_IMAGES["Dart"] = safe_load("assets/alien_dart.png", (56, 40))

    # Asteroids
    ASTEROID_IMAGES["Tiny"] = safe_load("assets/as_1.png")
    ASTEROID_IMAGES["Small"] = safe_load("assets/as_2.png")
    ASTEROID_IMAGES["Medium"] = safe_load("assets/as_3.png")
    ASTEROID_IMAGES["Large"] = safe_load("assets/as_4.png")
    ASTEROID_IMAGES["Titan"] = safe_load("assets/as_5.png")  # you said you'll add later — code tolerates missing

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def draw_text(surf, text, size, x, y, color=WHITE, center=True, font_obj=None, alpha=None):
    f = font_obj or pygame.font.SysFont("consolas", size)
    ts = f.render(text, True, color)
    if alpha is not None:
        ts.set_alpha(alpha)
    rect = ts.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(ts, rect)

# ---------- UI: Button ----------
class Button:
    def __init__(self, text, x, y, w, h, font_obj=None, base=(200,200,200), hover=(255,255,255)):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font_obj or big_font
        self.base = base
        self.hover = hover

    def draw(self, surf):
        color = self.hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.base
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        pygame.draw.rect(surf, (255,255,255), self.rect, 2, border_radius=10)
        ts = self.font.render(self.text, True, (0,0,0))
        surf.blit(ts, ts.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

# ---------- Background ----------
class ParallaxBackground:
    def __init__(self):
        self.stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.8, 2.5)] for _ in range(STAR_COUNT)]
        self.planets = []
        self.planet_timer = 0.0

    def update(self, scroll_speed, dt):
        for s in self.stars:
            s[1] += (s[2] + scroll_speed * 0.3) * dt * FPS
            if s[1] > HEIGHT:
                s[0] = random.randint(0, WIDTH)
                s[1] = 0
                s[2] = random.uniform(0.8, 2.5)
        self.planet_timer += dt
        if self.planet_timer > 2.0 and random.random() < PLANET_CHANCE:
            px = random.randint(60, WIDTH - 60)
            pr = random.randint(28, 60)
            pkey = random.choice(PLANET_KEYS)
            color = random.choice(PLANET_COLORS)
            speed = random.uniform(0.3, 1.2)
            self.planets.append([px, -pr, pr, color, speed, pkey])
            self.planet_timer = 0.0
        for p in self.planets:
            p[1] += (p[4] + scroll_speed * 0.15) * dt * FPS
        self.planets = [p for p in self.planets if p[1] < HEIGHT + 80]

    def draw(self, surf):
        # stars
        for s in self.stars:
            pygame.draw.circle(surf, (200,200,200), (int(s[0]), int(s[1])), 1)
        # planets
        for x, y, r, color, spd, pkey in self.planets:
            img = ASSETS["planets"].get(pkey)
            if img:
                scaled = pygame.transform.smoothscale(img, (int(r*2), int(r*2)))
                surf.blit(scaled, scaled.get_rect(center=(int(x), int(y))))
            else:
                pygame.draw.circle(surf, color, (int(x), int(y)), int(r))

# ---------- Projectiles ----------
class Bullet:
    def __init__(self, x, y, speed, angle, damage, wtype):
        self.x = float(x); self.y = float(y)
        self.speed = float(speed); self.angle = float(angle)
        self.damage = float(damage); self.type = wtype
        self.rect = pygame.Rect(int(self.x-3), int(self.y-12), 6, 16)

    def update(self, dt):
        rad = math.radians(self.angle)
        self.x += math.sin(rad) * 8 * dt * FPS
        self.y += self.speed * dt * FPS
        self.rect.topleft = (int(self.x-3), int(self.y-12))

    def draw(self, surf):
        color = YELLOW if self.type == "minigun" else ORANGE
        pygame.draw.rect(surf, color, self.rect)

class Beam:
    """Beam follows player's X while active so it continues to hit new enemies."""
    def __init__(self, x, y, duration, dps, width, follow_player=True):
        self.x = float(x)
        self.y = float(y)
        self.timer = float(duration)
        self.dps = float(dps)
        self.width = int(width)
        self.follow_player = follow_player

    def update(self, dt, player_x=None):
        self.timer -= dt
        if self.follow_player and player_x is not None:
            self.x = float(player_x)  # follow player's X

    def active(self):
        return self.timer > 0

    def draw(self, surf):
        if self.active():
            pygame.draw.rect(surf, RED, (int(self.x - self.width // 2), 0, self.width, int(self.y)), border_radius=8)
            pygame.draw.rect(surf, (255,80,80), (int(self.x - self.width // 3), 0, int(self.width/1.5), int(self.y)), border_radius=6)

class Missile:
    def __init__(self, x, y, damage, radius):
        self.x = float(x); self.y = float(y)
        self.damage = float(damage); self.radius = float(radius)
        self.speed = -7.0; self.exploded = False; self.explode_timer = 0.0
        self.rect = pygame.Rect(int(self.x-8), int(self.y-16), 16, 32)

    def update(self, dt):
        if not self.exploded:
            self.y += self.speed * dt * FPS
            self.rect.topleft = (int(self.x-8), int(self.y-16))
        else:
            self.explode_timer += dt
            self.radius = min(self.radius + dt * 20, 100)

    def draw(self, surf):
        if not self.exploded:
            if ASSETS["missile"]:
                surf.blit(ASSETS["missile"], ASSETS["missile"].get_rect(center=(int(self.x), int(self.y))))
            else:
                pygame.draw.rect(surf, ORANGE, self.rect)
                pygame.draw.circle(surf, YELLOW, (int(self.x), int(self.y)), 8, 2)
        else:
            pygame.draw.circle(surf, (255,200,80), (int(self.x), int(self.y)), int(self.radius), 3)

# ---------- Weapons ----------
class Weapon:
    def __init__(self, player):
        self.player = player
        self.cooldown = 0.0

    def update(self, dt):
        if self.cooldown > 0: self.cooldown -= dt

    def try_fire(self, bullets, beams, missiles, holding, dt):
        pass

    def display_name(self): return "Weapon"
    def status_string(self): return ""

class Minigun(Weapon):
    def __init__(self, player):
        super().__init__(player)
        c = WEAPON_CONFIG["minigun"]
        self.magazine = c["magazine"]; self.rps = c["rps"]; self.damage = c["damage"]
        self.spread = c["spread"]; self.reload_time = c["reload_time"]
        self.ammo = self.magazine; self.reload = 0.0; self.fire_timer = 0.0

    def update(self, dt):
        super().update(dt)
        if self.reload > 0:
            self.reload -= dt
            if self.reload <= 0: self.ammo = self.magazine
        if self.fire_timer > 0: self.fire_timer -= dt

    def try_fire(self, bullets, beams, missiles, holding, dt):
        if self.reload > 0: return
        if holding and self.fire_timer <= 0 and self.ammo > 0:
            angle = random.uniform(-self.spread, self.spread)
            bullets.append(Bullet(self.player.x, self.player.y - PLAYER_SHIP_H // 2, -13, angle, self.damage, "minigun"))
            self.ammo -= 1; self.fire_timer = 1.0 / self.rps
            if self.ammo <= 0: self.reload = self.reload_time

    def display_name(self): return "Minigun"
    def status_string(self): return "Reloading..." if self.reload > 0 else f"Ammo: {self.ammo}/{self.magazine}"

class Shotgun(Weapon):
    def __init__(self, player):
        super().__init__(player)
        c = WEAPON_CONFIG["shotgun"]
        self.rps = c["rps"]; self.pellets = c["pellets"]; self.damage = c["damage"]; self.spread_angle = c["spread_angle"]
        self.fire_timer = 0.0

    def update(self, dt):
        super().update(dt)
        if self.fire_timer > 0: self.fire_timer -= dt

    def try_fire(self, bullets, beams, missiles, holding, dt):
        if holding and self.fire_timer <= 0:
            for i in range(self.pellets):
                angle = (i - (self.pellets - 1) / 2) * self.spread_angle
                bullets.append(Bullet(self.player.x, self.player.y - PLAYER_SHIP_H // 2, -11, angle, self.damage, "shotgun"))
            self.fire_timer = 1.0 / self.rps

    def display_name(self): return "Shotgun"
    def status_string(self): return "Ready"

class Laser(Weapon):
    def __init__(self, player):
        super().__init__(player)
        c = WEAPON_CONFIG["laser"]
        self.charge_time = c["charge_time"]; self.beam_duration = c["beam_duration"]
        self.dps = c["dps"]; self.charges = c["charges"]
        self.cooldown_time = c["cooldown"]; self.width = c["width"]
        self.charge = 0.0; self.beam = 0.0; self.cooldown = 0.0; self.remaining_charges = self.charges
        # NOTE: when a beam is spawned we set follow_player=True so beam.x keeps following player.x

    def update(self, dt):
        if self.cooldown > 0: self.cooldown -= dt
        if self.beam > 0: self.beam -= dt
        if self.charge > 0: self.charge -= dt

    def try_fire(self, bullets, beams, missiles, holding, dt):
        if self.cooldown > 0 or self.remaining_charges <= 0:
            return
        if holding:
            if self.beam > 0: return
            if self.charge <= 0:
                self.charge = self.charge_time
            else:
                self.charge -= dt
                if self.charge <= 0:
                    self.beam = self.beam_duration
                    self.remaining_charges -= 1
                    self.cooldown = self.cooldown_time
                    # spawn beam that follows player
                    beams.append(Beam(self.player.x, self.player.y - PLAYER_SHIP_H // 2, self.beam_duration, self.dps, self.width, follow_player=True))

    def display_name(self): return "Laser"
    def status_string(self):
        if self.cooldown > 0: return f"Cooldown: {self.cooldown:.1f}s"
        if self.beam > 0: return f"Beam: {self.beam:.1f}s"
        if self.charge > 0: return "Charging..."
        return f"Charges: {self.remaining_charges}/{self.charges}"

class MissileLauncher(Weapon):
    def __init__(self, player):
        super().__init__(player)
        c = WEAPON_CONFIG["missile"]
        self.windup = c["windup"]; self.cooldown_time = c["cooldown"]; self.capacity = c["capacity"]
        self.explosion_radius = c["explosion_radius"]; self.damage = c["damage"]
        self.missiles = self.capacity; self.cooldown = 0.0; self.windup_timer = 0.0

    def update(self, dt):
        if self.cooldown > 0: self.cooldown -= dt
        if self.windup_timer > 0: self.windup_timer -= dt

    def try_fire(self, bullets, beams, missiles, holding, dt):
        if self.cooldown > 0 or self.missiles <= 0: return
        if holding:
            if self.windup_timer <= 0:
                self.windup_timer = self.windup
            else:
                self.windup_timer -= dt
                if self.windup_timer <= 0:
                    missiles.append(Missile(self.player.x, self.player.y - PLAYER_SHIP_H // 2, self.damage, self.explosion_radius))
                    self.missiles -= 1; self.cooldown = self.cooldown_time

    def add_missile(self):
        self.missiles = clamp(self.missiles + 1, 0, self.capacity)

    def display_name(self): return "Missile"
    def status_string(self): return f"Cooldown: {self.cooldown:.1f}s" if self.cooldown > 0 else f"Missiles: {self.missiles}/{self.capacity}"

# ---------- Player ----------
class Player:
    def __init__(self, game):
        self.game = game
        self.x = WIDTH // 2
        self.y = HEIGHT - 120
        self.w, self.h = PLAYER_SHIP_W, PLAYER_SHIP_H
        self.speed = PLAYER_BASE_SPEED
        self.target_speed = PLAYER_BASE_SPEED
        self.dx = 0
        self.invincible = 0.0
        self.hearts = PLAYER_START_HEARTS
        self.max_hearts = PLAYER_MAX_HEARTS
        self.fuel = PLAYER_START_FUEL
        self.shield = 0.0
        self.weapons = [Minigun(self), Shotgun(self), Laser(self), MissileLauncher(self)]
        self.current_weapon_idx = 0
        self.current_weapon = self.weapons[self.current_weapon_idx]

    def update(self, keys, dt):
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move += 1
        self.dx = move * 9
        self.x = clamp(self.x + self.dx * dt * FPS, self.w // 2, WIDTH - self.w // 2)

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.target_speed = PLAYER_MAX_SPEED
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.target_speed = PLAYER_BASE_SPEED
        else:
            self.target_speed = (PLAYER_BASE_SPEED + PLAYER_MAX_SPEED) / 2

        if self.speed < self.target_speed: self.speed += PLAYER_ACCEL
        elif self.speed > self.target_speed: self.speed -= PLAYER_ACCEL
        self.speed = clamp(self.speed, PLAYER_BASE_SPEED, PLAYER_MAX_SPEED)

        drain = PLAYER_FUEL_DRAIN_BOOST if self.target_speed > PLAYER_BASE_SPEED else PLAYER_FUEL_DRAIN
        self.fuel = clamp(self.fuel - drain * dt * FPS, 0, PLAYER_MAX_FUEL)

        if self.invincible > 0: self.invincible -= dt * FPS
        if self.shield > 0: self.shield -= dt * FPS

        self.current_weapon.update(dt)

    def draw(self, surf):
        if ASSETS["ship"]:
            surf.blit(ASSETS["ship"], ASSETS["ship"].get_rect(center=(int(self.x), int(self.y))))
        else:
            tip = (int(self.x), int(self.y - self.h // 2))
            left = (int(self.x - self.w // 2), int(self.y + self.h // 2))
            right = (int(self.x + self.w // 2), int(self.y + self.h // 2))
            pygame.draw.polygon(surf, BLUE if self.invincible > 0 or self.shield > 0 else WHITE, [tip, left, right])
        if self.shield > 0:
            pygame.draw.circle(surf, (0, 200, 255), (int(self.x), int(self.y)), self.w, 2)

    def switch_weapon(self, d):
        self.current_weapon_idx = (self.current_weapon_idx + d) % len(self.weapons)
        self.current_weapon = self.weapons[self.current_weapon_idx]

    def switch_weapon_direct(self, idx):
        idx = int(clamp(idx, 0, len(self.weapons)-1))
        self.current_weapon_idx = idx
        self.current_weapon = self.weapons[idx]

    def take_damage(self, amt):
        if self.invincible > 0 or self.shield > 0: return
        self.hearts = clamp(self.hearts - amt, 0, self.max_hearts)
        self.invincible = PLAYER_INVINCIBLE_TIME

    def heal(self, amt):
        self.hearts = clamp(self.hearts + amt, 0, self.max_hearts)

    def add_fuel(self, amt):
        self.fuel = clamp(self.fuel + amt, 0, PLAYER_MAX_FUEL)

    def add_missile(self):
        for w in self.weapons:
            if isinstance(w, MissileLauncher): w.add_missile()

# ---------- Enemies & Objects ----------
class Asteroid:
    def __init__(self, tier, y0=None):
        t = ASTEROID_TIERS[tier]
        self.tier = tier
        self.radius = t["radius"]
        self.hp = float(t["hp"])
        self.max_hp = float(t["hp"])
        self.color = t["color"]
        self.x = float(random.randint(self.radius, WIDTH - self.radius))
        self.y = float(-self.radius if y0 is None else y0)
        self.speed = float(random.randint(*t["speed"]))
        self.name = t["name"]
        self.image = None
        img = ASTEROID_IMAGES.get(self.name)
        if img:
            self.image = pygame.transform.smoothscale(img, (self.radius*2, self.radius*2))
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        else:
            self.rect = pygame.Rect(int(self.x-self.radius), int(self.y-self.radius), self.radius*2, self.radius*2)

    def update(self, scroll_speed, dt):
        self.y += (self.speed + scroll_speed) * dt * FPS
        if self.image:
            self.rect.center = (int(self.x), int(self.y))
        else:
            self.rect.topleft = (int(self.x-self.radius), int(self.y-self.radius))

    def draw(self, surf):
        if self.image:
            surf.blit(self.image, self.rect)
        else:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        if self.max_hp > 1:
            pygame.draw.rect(surf, DARK_GRAY, (self.x-self.radius, self.y-self.radius-8, self.radius*2, 5))
            pygame.draw.rect(surf, GREEN, (self.x-self.radius, self.y-self.radius-8, int(self.radius*2*self.hp/self.max_hp), 5))

class Alien:
    def __init__(self, atype, y0=None):
        t = ALIEN_TYPES[atype]
        self.type = t
        self.color = t["color"]
        self.hp = float(t["hp"])
        self.max_hp = float(t["hp"])
        self.speed = float(t["speed"])
        self.fire_rate = float(t["fire_rate"])
        self.damage = float(t["damage"])
        self.name = t["name"]
        self.x = float(random.randint(40, WIDTH-40))
        self.y = float(-32 if y0 is None else y0)
        self.w = 44
        self.h = 28
        self.image = ALIEN_IMAGES.get(self.name)
        if self.image:
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            self.w, self.h = self.rect.width, self.rect.height
        else:
            self.rect = pygame.Rect(int(self.x - self.w//2), int(self.y - self.h//2), self.w, self.h)
        self.fire_timer = random.uniform(0.0, self.fire_rate)
        self.dodge_timer = 0.0

    def update(self, scroll_speed, player_x, dt):
        self.y += (self.speed + scroll_speed) * dt * FPS
        if self.name == "Dart":
            if self.dodge_timer <= 0:
                if abs(self.x - player_x) < 80:
                    self.x += random.choice([-1, 1]) * 12
                self.dodge_timer = 0.5
            else:
                self.dodge_timer -= dt
        if self.image:
            self.rect.center = (int(self.x), int(self.y))
        else:
            self.rect.topleft = (int(self.x-self.w//2), int(self.y-self.h//2))
        if self.fire_timer > 0: self.fire_timer -= dt

    def can_shoot(self): return self.fire_timer <= 0
    def shoot(self, bullets):
        bullets.append(AlienBullet(self.x, self.y + self.h//2, self.damage))
        self.fire_timer = self.fire_rate

    def draw(self, surf):
        if self.image:
            surf.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surf, self.color, self.rect)
        if self.max_hp > 1:
            pygame.draw.rect(surf, DARK_GRAY, (self.x - self.w//2, self.y - self.h//2 - 8, self.w, 5))
            pygame.draw.rect(surf, RED, (self.x - self.w//2, self.y - self.h//2 - 8, int(self.w * self.hp / self.max_hp), 5))

class AlienBullet:
    def __init__(self, x, y, damage):
        self.x = float(x); self.y = float(y); self.damage = float(damage); self.speed = 7.0
        self.rect = pygame.Rect(int(self.x - 4), int(self.y), 8, 16)

    def update(self, scroll_speed, dt):
        self.y += (self.speed + scroll_speed) * dt * FPS
        self.rect.topleft = (int(self.x - 4), int(self.y))

    def draw(self, surf):
        pygame.draw.rect(surf, RED, self.rect)

class PowerUp:
    def __init__(self, ptype, y0=None):
        t = next(p for p in POWERUP_TYPES if p["type"] == ptype)
        self.type = t["type"]
        self.color = t["color"]
        self.x = float(random.randint(30, WIDTH-30))
        self.y = float(-20 if y0 is None else y0)
        self.rect = pygame.Rect(int(self.x-14), int(self.y-14), 28, 28)

    def update(self, scroll_speed, dt):
        self.y += (4 + scroll_speed) * dt * FPS
        self.rect.topleft = (int(self.x-14), int(self.y-14))

    def draw(self, surf):
        img = ASSETS["powerups"].get(self.type)
        if img:
            surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        else:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 14)
            draw_text(surf, self.type[0].upper(), 16, int(self.x), int(self.y), BLACK)

# ---------- Spawner ----------
class ChunkSpawner:
    def __init__(self, game):
        self.game = game
        self.world_y = 0.0
        self.next_chunk_at = CHUNK_HEIGHT
        self.chunk_index = 0
        self.fuel_chunk_counter = 0
        self.special_chunk_counter = 0

    def update(self, scroll_speed, dt):
        self.world_y += scroll_speed * dt * FPS
        while self.world_y >= self.next_chunk_at:
            self.spawn_chunk(-CHUNK_HEIGHT)
            self.next_chunk_at += CHUNK_HEIGHT
            self.chunk_index += 1

    def spawn_chunk(self, y0):
        g = self.game
        level = g.level
        # asteroids
        n_ast = max(1, CHUNK_ASTEROID_BASE + random.randint(0, CHUNK_ASTEROID_VARIANCE) + (level // 10))
        for _ in range(n_ast):
            tier = min(len(ASTEROID_TIERS)-1, random.choices(range(len(ASTEROID_TIERS)), weights=[6,5,3,2,1])[0] + (level // 10))
            a = Asteroid(tier, y0 + random.randint(0, CHUNK_HEIGHT-40))
            g.asteroids.append(a)

        # aliens: higher chance and bias towards Tank and Dart
        if random.random() < ALIEN_BASE_CHANCE + 0.005 * level:
            # weights mapping: Normal, Rapid, Tank, Dart
            # increase Tank & Dart weight
            weights = [3, 2 + level // 12, 4 + level // 10, 5 + level // 8]
            atype = random.choices(range(len(ALIEN_TYPES)), weights=weights, k=1)[0]
            al = Alien(atype, y0 + random.randint(0, CHUNK_HEIGHT-60))
            g.aliens.append(al)

        # powerups
        self.fuel_chunk_counter += 1
        self.special_chunk_counter += 1
        if self.fuel_chunk_counter >= POWERUP_FUEL_EVERY:
            pu = PowerUp("fuel", y0 + random.randint(0, CHUNK_HEIGHT-30))
            g.powerups.append(pu)
            self.fuel_chunk_counter = 0
        elif self.special_chunk_counter >= POWERUP_SPECIAL_EVERY:
            ptype = random.choices(["heal", "missile", "heal1.5"], weights=[5,2,3], k=1)[0]
            pu = PowerUp(ptype, y0 + random.randint(0, CHUNK_HEIGHT-30))
            g.powerups.append(pu)
            self.special_chunk_counter = 0
        else:
            if random.random() < (RANDOM_POWERUP_BASE_CHANCE + 0.002 * level):
                ptype = random.choices([p["type"] for p in POWERUP_TYPES], weights=[2,2,4,3,3,2], k=1)[0]
                pu = PowerUp(ptype, y0 + random.randint(0, CHUNK_HEIGHT-30))
                g.powerups.append(pu)

# ---------- HUD ----------
class HUD:
    def __init__(self, game):
        self.game = game

    def draw(self, surf):
        g = self.game
        # Score
        draw_text(surf, f"Score: {g.score}", 22, HUD_SCORE_POS[0], HUD_SCORE_POS[1], WHITE, center=False)
        # Fuel bar
        fuel_w, fuel_h = 110, 12
        fuel_x, fuel_y = HUD_FUEL_POS
        pygame.draw.rect(surf, DARK_GRAY, (fuel_x, fuel_y, fuel_w, fuel_h), border_radius=6)
        pygame.draw.rect(surf, FUEL_BAR_COLOR, (fuel_x, fuel_y, int(fuel_w * g.player.fuel / PLAYER_MAX_FUEL), fuel_h), border_radius=6)
        # draw "Fuel" aligned vertically centered with bar
        draw_text(surf, "Fuel", 14, fuel_x + fuel_w + 8, fuel_y + fuel_h // 2, WHITE, center=False, font_obj=small_font)
        # Hearts
        self.draw_hearts(surf, g.player.hearts, HUD_HEARTS_POS[0], HUD_HEARTS_POS[1])
        # Weapon info
        self.draw_weapon(surf, g.player, HUD_WEAPON_POS[0], HUD_WEAPON_POS[1])
        # Level
        draw_text(surf, f"Level {g.level}", 20, HUD_LEVEL_POS[0], HUD_LEVEL_POS[1], WHITE, center=True)
        # Controls (moved right)
        self.draw_controls(surf, HUD_CONTROLS_POS[0], HUD_CONTROLS_POS[1])

    def draw_hearts(self, surf, hearts, x, y):
        full = int(hearts)
        half = 1 if hearts - full >= 0.5 else 0
        # center hearts inside a 26x26 area: we'll offset so they appear in row
        for i in range(int(PLAYER_MAX_HEARTS)):
            cx = x + i * 32
            if i < full:
                if ASSETS["heart"]:
                    img = ASSETS["heart"]
                    rect = img.get_rect(center=(cx + 13, y))
                    surf.blit(img, rect)
                else:
                    pygame.draw.circle(surf, HEART_COLOR, (cx + 13, y), 13)
            elif i == full and half:
                if ASSETS["half_heart"]:
                    img = ASSETS["half_heart"]
                    rect = img.get_rect(center=(cx + 13, y))
                    surf.blit(img, rect)
                else:
                    pygame.draw.circle(surf, HALF_HEART_COLOR, (cx + 13, y), 13)
                    pygame.draw.polygon(surf, WHITE, [(cx + 6, y), (cx + 20, y), (cx + 13, y + 13)], 2)
            else:
                pygame.draw.circle(surf, DARK_GRAY, (cx + 13, y), 13, 2)

    def draw_weapon(self, surf, player, x, y):
        weapon = player.current_weapon
        draw_text(surf, weapon.display_name(), 20, x, y, WHITE, center=False)
        draw_text(surf, weapon.status_string(), 16, x, y + 22, YELLOW, center=False, font_obj=small_font)

    def draw_controls(self, surf, x, y):
        lines = ["Controls:", "Move: AD / Arrows", "Shoot: Hold SPACE", "Switch: Q/E or 1-4", "Menu: Esc"]
        for i, line in enumerate(lines):
            draw_text(surf, line, 15, x, y + i * 20, (180, 180, 255), center=False, font_obj=small_font)

# ---------- Game ----------
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.level = 1
        self.scroll_y = 0.0
        self.player = Player(self)
        self.hud = HUD(self)
        self.bg = ParallaxBackground()
        self.asteroids = []
        self.aliens = []
        self.alien_bullets = []
        self.powerups = []
        self.bullets = []
        self.beams = []
        self.missiles = []
        self.spawner = ChunkSpawner(self)
        self.paused = False
        self.game_over = False
        self.high_score = self.load_high_score()
        self.frame_seconds = 0.0

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except Exception:
            return 0

    def save_high_score(self):
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    def update(self, keys, dt, holding_shoot):
        if self.paused or self.game_over: return
        # Level ramps each 20s
        self.frame_seconds += dt
        self.level = 1 + int(self.frame_seconds // 20)

        scroll_speed = self.player.speed * 0.7
        self.bg.update(scroll_speed, dt)
        self.spawner.update(scroll_speed, dt)
        self.player.update(keys, dt)

        # Firing (continuous)
        self.player.current_weapon.try_fire(self.bullets, self.beams, self.missiles, holding_shoot, dt)

        # update bullets
        for b in self.bullets[:]:
            b.update(dt)
            if b.y < -40 or b.y > HEIGHT + 40:
                try: self.bullets.remove(b)
                except ValueError: pass

        # update beams (and make them follow player.x if follow_player)
        for beam in self.beams[:]:
            beam.update(dt, player_x=self.player.x)
            if not beam.active():
                try: self.beams.remove(beam)
                except ValueError: pass

        # missiles
        for m in self.missiles[:]:
            m.update(dt)
            if not m.exploded and m.y < 0: m.exploded = True
            if m.exploded and m.explode_timer > 0.4:
                try: self.missiles.remove(m)
                except ValueError: pass

        # asteroids
        for a in self.asteroids[:]:
            a.update(scroll_speed, dt)
            if a.y - a.radius > HEIGHT + 80: 
                try: self.asteroids.remove(a)
                except ValueError: pass

        # aliens
        for al in self.aliens[:]:
            al.update(scroll_speed, self.player.x, dt)
            if al.y - al.h // 2 > HEIGHT + 80:
                try: self.aliens.remove(al)
                except ValueError: pass
            elif al.can_shoot():
                al.shoot(self.alien_bullets)

        # alien bullets
        for ab in self.alien_bullets[:]:
            ab.update(self.player.speed * 0.7, dt)
            if ab.y > HEIGHT + 100:
                try: self.alien_bullets.remove(ab)
                except ValueError: pass

        # powerups
        for pu in self.powerups[:]:
            pu.update(self.player.speed * 0.7, dt)
            if pu.y > HEIGHT + 80:
                try: self.powerups.remove(pu)
                except ValueError: pass

        # collisions
        self.handle_collisions()

        # score over time
        self.score += int(1 * dt * FPS)

        if self.player.fuel <= 0 or self.player.hearts <= 0:
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()

    def handle_collisions(self):
        # bullets vs asteroids
        for a in self.asteroids[:]:
            for b in self.bullets[:]:
                if a.rect.colliderect(b.rect):
                    if b.type == "shotgun" and a.tier == len(ASTEROID_TIERS) - 1:
                        a.hp -= max(1, int(a.max_hp * 0.85))
                    else:
                        a.hp -= b.damage
                    try: self.bullets.remove(b)
                    except ValueError: pass
                    if a.hp <= 0:
                        try: self.asteroids.remove(a)
                        except ValueError: pass
                        self.score += 30
                    break

        # bullets vs aliens
        for al in self.aliens[:]:
            for b in self.bullets[:]:
                if al.rect.colliderect(b.rect):
                    al.hp -= b.damage
                    try: self.bullets.remove(b)
                    except ValueError: pass
                    if al.hp <= 0:
                        try: self.aliens.remove(al)
                        except ValueError: pass
                        self.score += 60
                    break

        # beams vs asteroids/aliens (beam.x always follows player.x if set that way)
        for beam in list(self.beams):
            # use beam.x (already updated to player.x each frame if follow_player)
            for a in self.asteroids[:]:
                if abs(a.x - beam.x) < beam.width / 2:
                    # allow beam to damage entities regardless of whether they were present when fired
                    a.hp -= beam.dps * (1.0 / FPS)
                    if a.hp <= 0:
                        try: self.asteroids.remove(a)
                        except ValueError: pass
                        self.score += 30
            for al in self.aliens[:]:
                if abs(al.x - beam.x) < beam.width / 2:
                    al.hp -= beam.dps * (1.0 / FPS)
                    if al.hp <= 0:
                        try: self.aliens.remove(al)
                        except ValueError: pass
                        self.score += 60

        # missiles AoE
        for m in list(self.missiles):
            if not m.exploded:
                for a in self.asteroids:
                    if m.rect.colliderect(a.rect):
                        m.exploded = True
                        break
                for al in self.aliens:
                    if m.rect.colliderect(al.rect):
                        m.exploded = True
                        break
            if m.exploded:
                for a in self.asteroids[:]:
                    if math.hypot(a.x - m.x, a.y - m.y) < m.radius:
                        a.hp -= m.damage
                        if a.hp <= 0:
                            try: self.asteroids.remove(a)
                            except ValueError: pass
                            self.score += 30
                for al in self.aliens[:]:
                    if math.hypot(al.x - m.x, al.y - m.y) < m.radius:
                        al.hp -= m.damage
                        if al.hp <= 0:
                            try: self.aliens.remove(al)
                            except ValueError: pass
                            self.score += 60

        # asteroids vs player
        p_rect = pygame.Rect(int(self.player.x - self.player.w // 2), int(self.player.y - self.player.h // 2), self.player.w, self.player.h)
        for a in self.asteroids[:]:
            if p_rect.colliderect(a.rect):
                if self.player.invincible <= 0 and self.player.shield <= 0:
                    self.player.take_damage(0.5)
                try: self.asteroids.remove(a)
                except ValueError: pass

        # alien bullets vs player
        for ab in self.alien_bullets[:]:
            if p_rect.colliderect(ab.rect):
                if self.player.invincible <= 0 and self.player.shield <= 0:
                    self.player.take_damage(ab.damage)
                try: self.alien_bullets.remove(ab)
                except ValueError: pass

        # aliens vs player
        for al in self.aliens[:]:
            if p_rect.colliderect(al.rect):
                if self.player.invincible <= 0 and self.player.shield <= 0:
                    self.player.take_damage(al.damage)
                try: self.aliens.remove(al)
                except ValueError: pass

        # powerups
        for pu in self.powerups[:]:
            if p_rect.colliderect(pu.rect):
                if pu.type == "shield":
                    self.player.shield = FPS * 5
                elif pu.type == "firerate":
                    for w in self.player.weapons:
                        if hasattr(w, "rps"):
                            w.rps *= 1.4
                elif pu.type == "heal":
                    self.player.heal(1)
                elif pu.type == "heal1.5":
                    self.player.heal(1.5)
                elif pu.type == "fuel":
                    self.player.add_fuel(40)
                elif pu.type == "missile":
                    self.player.add_missile()
                try: self.powerups.remove(pu)
                except ValueError: pass

    def draw(self, surf):
        # background fill or image
        if ASSETS["bg"]:
            surf.blit(ASSETS["bg"], (0,0))
        else:
            surf.fill((6, 6, 14))
        self.bg.draw(surf)
        for a in self.asteroids: a.draw(surf)
        for al in self.aliens: al.draw(surf)
        for ab in self.alien_bullets: ab.draw(surf)
        for b in self.bullets: b.draw(surf)
        for beam in self.beams: beam.draw(surf)
        for m in self.missiles: m.draw(surf)
        for pu in self.powerups: pu.draw(surf)
        self.player.draw(surf)
        self.hud.draw(surf)

# ---------- Menus ----------
def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur + w) <= max_chars:
            cur += w + " "
        else:
            lines.append(cur.strip())
            cur = w + " "
    if cur: lines.append(cur.strip())
    return lines

def instructions_menu():
    back = Button("Back", WIDTH//2 - 160, HEIGHT - 100, 320, 50, big_font)
    while True:
        screen.fill(BLACK)
        draw_text(screen, "Instructions", 48, WIDTH//2, 80, (0,255,255))
        lines = [
            "Temple Run in Space! Move forward, dodge, shoot, survive.",
            "Controls:",
            "Move: Arrow keys or WASD",
            "Shoot: Hold SPACE",
            "Switch Gun: Q/E or 1-4",
            "Pause: P | Restart: R | Menu: ESC",
            "",
            "Collect power-ups for shields, fire rate, health, and fuel.",
            "If fuel runs out or you lose all lives, it's game over.",
            "",
            "Each weapon has unique ammo & cooldowns.",
            "Difficulty increases as you progress."
        ]
        y = 150
        for line in lines:
            for sub in wrap_text(line, 50):
                draw_text(screen, sub, 22, WIDTH//2, y, WHITE)
                y += 28
            y += 4

        # back button appearance
        bg_surf = pygame.Surface((back.rect.width, back.rect.height), pygame.SRCALPHA)
        hover = back.rect.collidepoint(pygame.mouse.get_pos())
        bg_surf.fill((80,80,80,200) if hover else (50,50,50,150))
        screen.blit(bg_surf, back.rect.topleft)
        ts = back.font.render(back.text, True, (255,255,255))
        screen.blit(ts, ts.get_rect(center=back.rect.center))

        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and back.rect.collidepoint(ev.pos):
                return

def pause_menu():
    resume = Button("Resume", WIDTH//2 - 160, HEIGHT//2, 320, 50, big_font)
    settings = Button("Settings", WIDTH//2 - 160, HEIGHT//2 + 70, 320, 50, big_font)
    menu = Button("Main Menu", WIDTH//2 - 160, HEIGHT//2 + 140, 320, 50, big_font)
    while True:
        screen.fill(BLACK)
        draw_text(screen, "PAUSED", 56, WIDTH//2, HEIGHT//2-120, (255,255,0))
        for b in (resume, settings, menu): b.draw(screen)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if resume.is_clicked(ev): return
            if settings.is_clicked(ev): settings_menu()
            if menu.is_clicked(ev): return

def settings_menu():
    back = Button("Back", WIDTH//2 - 100, HEIGHT//2 + 100, 200, 50, big_font)
    while True:
        screen.fill(BLACK)
        draw_text(screen, "Settings", 48, WIDTH//2, HEIGHT//2-80, (0,255,255))
        draw_text(screen, "Volume: (placeholder)", 32, WIDTH//2, HEIGHT//2, WHITE)
        back.draw(screen)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if back.is_clicked(ev): return

def game_over_screen(score, high_score):
    while True:
        screen.fill(BLACK)
        draw_text(screen, "GAME OVER", 56, WIDTH//2, HEIGHT//2-80, (255,80,80))
        draw_text(screen, f"Score: {score}", 36, WIDTH//2, HEIGHT//2-10, WHITE)
        draw_text(screen, f"High Score: {high_score}", 28, WIDTH//2, HEIGHT//2+40, YELLOW)
        draw_text(screen, "Press R to Restart or ESC for Menu", 26, WIDTH//2, HEIGHT//2+90, (180,180,255))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r: return True
                if ev.key == pygame.K_ESCAPE: return False

def main_menu():
    bg = ASSETS["bg"]
    start = Button("Start Game", WIDTH//2 - 160, HEIGHT//2, 320, 50, big_font)
    instr = Button("Instructions", WIDTH//2 - 160, HEIGHT//2 + 70, 320, 50, big_font)
    quitb = Button("Quit", WIDTH//2 - 160, HEIGHT//2 + 140, 320, 50, big_font)
    c = pygame.time.Clock()
    while True:
        c.tick(FPS)
        if bg: screen.blit(bg, (0,0))
        else: screen.fill((8, 8, 16))
        draw_text(screen, "Cosmic Adventure", 48, WIDTH//2, HEIGHT//2-120, (0,255,255))
        draw_text(screen, "The Journey of Star", 32, WIDTH//2, HEIGHT//2-70, (255,255,0))
        for b in (start, instr, quitb): b.draw(screen)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if start.is_clicked(ev): return True
            if instr.is_clicked(ev): instructions_menu()
            if quitb.is_clicked(ev): pygame.quit(); sys.exit()

# ---------- Main loop ----------
def game_loop(game):
    holding = False
    last = pygame.time.get_ticks()
    while True:
        now = pygame.time.get_ticks()
        dt = (now - last) / 1000.0
        last = now
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE: holding = True
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    game.player.switch_weapon_direct(ev.key - pygame.K_1)
                elif ev.key == pygame.K_q: game.player.switch_weapon(-1)
                elif ev.key == pygame.K_e: game.player.switch_weapon(1)
                elif ev.key in (pygame.K_p, pygame.K_ESCAPE):
                    game.paused = True
                    pause_menu()
                    game.paused = False
                elif ev.key == pygame.K_r and game.game_over:
                    return True
            elif ev.type == pygame.KEYUP:
                if ev.key == pygame.K_SPACE: holding = False

        if not game.paused and not game.game_over:
            game.update(keys, dt, holding)

        game.draw(screen)
        pygame.display.flip()

        if game.game_over:
            again = game_over_screen(game.score, game.high_score)
            return bool(again)

def main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init(); pygame.font.init()
    global screen, clock, font, big_font, small_font
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cosmic Adventure: The Journey of Star")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 22)
    big_font = pygame.font.SysFont("consolas", 48)
    small_font = pygame.font.SysFont("consolas", 16)

    load_assets()

    while True:
        if main_menu():
            g = Game()
            game_loop(g)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()