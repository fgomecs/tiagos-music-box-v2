"""
games.py - activities for Tiago's Music Box V2: Draw, Brick Breaker, Fish Maze.

Each activity has:  handle(ev)   update(dt)   draw(surf)
kidbox.py calls setup(kidbox_module) once so we can reuse its colours, fonts and helpers.
Everything is touch-first (taps, drags, swipes); arrow keys also work for testing.
"""
import colorsys
import math
import os
import random
import time

import pygame

K = None          # the kidbox module (helpers, colours, W/H, PHOTO_DIR)
TOP = 70          # top bar height (home button, score, lives)


def setup(kidbox_module):
    global K
    K = kidbox_module


# ------------------------------------------------------------ sound effects
# Little beeps made in code (no sound files). The sound card is opened only while a game
# runs (music is stopped then), and released on the way out so mpv can use it again.
_RAW = {}
_SFX = {}
_SR = 22050


def _tone(notes, vol=0.35, wave="square"):
    """notes = [(freq_start, freq_end, ms), ...] -> raw 16-bit mono samples."""
    import array
    buf = array.array("h")
    phase = 0.0
    for f0, f1, ms in notes:
        n = int(_SR * ms / 1000)
        for i in range(n):
            f = f0 + (f1 - f0) * i / max(1, n)
            phase += f / _SR
            env = min(1, i / 80) * (1 - i / n) ** 0.6          # quick attack, smooth fade
            if f0 == 0:
                v = random.uniform(-1, 1) * env                  # noise burst
            elif wave == "square":
                v = (1 if (phase % 1) < 0.5 else -1) * env * 0.6
            else:
                v = math.sin(phase * 2 * math.pi) * env
            buf.append(int(v * vol * 32767))
    return buf.tobytes()


def build_sounds():
    if _RAW:
        return
    _RAW.update({
        "paddle": _tone([(330, 330, 50)]),
        "wall": _tone([(220, 220, 30)], 0.2),
        "brick": _tone([(660, 990, 70)]),
        "lose": _tone([(440, 330, 150), (330, 220, 150), (220, 110, 300)], wave="sine"),
        "win": _tone([(523, 523, 110), (659, 659, 110), (784, 784, 110), (1047, 1047, 260)], wave="sine"),
        "launch": _tone([(300, 700, 120)], 0.25),
        "pearl": _tone([(800, 600, 45)], 0.2),
        "pearl2": _tone([(600, 800, 45)], 0.2),
        "power": _tone([(300, 1200, 300)], 0.3, "sine"),
        "eat": _tone([(400, 400, 60), (600, 600, 60), (900, 900, 120)]),
    })


def audio_on():
    try:
        build_sounds()
        if not pygame.mixer.get_init():
            pygame.mixer.init(_SR, -16, 1, 1024)
        _SFX.clear()
        _SFX.update({k: pygame.mixer.Sound(buffer=v) for k, v in _RAW.items()})
    except Exception as e:
        print("sfx off:", e)
        _SFX.clear()


def audio_off():
    _SFX.clear()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
    except Exception:
        pass


def sfx(name):
    snd = _SFX.get(name)
    if snd:
        try:
            snd.play()
        except Exception:
            pass


def touch_mouse(ev):
    """True if this mouse event was synthesised by SDL from a finger touch."""
    return getattr(ev, "touch", False)


def heart(surf, c, s, color):
    x, y = c
    r = s // 4
    pygame.draw.circle(surf, color, (x - r, y - r // 2), r)
    pygame.draw.circle(surf, color, (x + r, y - r // 2), r)
    pygame.draw.polygon(surf, color, [(x - 2 * r, y - r // 3), (x + 2 * r, y - r // 3), (x, y + 2 * r)])


def icon_again(surf, c, s, color):
    x, y = c
    r = s // 2 - 4
    rect = pygame.Rect(x - r, y - r, 2 * r, 2 * r)
    pygame.draw.arc(surf, color, rect, math.radians(40), math.radians(330), max(4, s // 9))
    a = math.radians(40)
    tip = (x + math.cos(a) * r, y - math.sin(a) * r)
    pygame.draw.polygon(surf, color, [(tip[0] - s * 0.22, tip[1] - s * 0.05), (tip[0] + s * 0.12, tip[1] - s * 0.2),
                                      (tip[0] + s * 0.05, tip[1] + s * 0.18)])


class Overlay:
    """Big friendly 'Game over / Great!' card with a play-again button."""

    def __init__(self, title, color, on_again):
        self.title, self.color, self.on_again = title, color, on_again
        self.btn = pygame.Rect(K.W // 2 - 70, K.H // 2 + 10, 140, 110)

    def draw(self, s, score):
        dim = pygame.Surface((K.W, K.H))
        dim.set_alpha(150)
        dim.fill((0, 0, 0))
        s.blit(dim, (0, 0))
        box = K.rbox(s, K.WHITE, (K.W // 2 - 230, K.H // 2 - 150, 460, 300), 30)
        K.text(s, self.title, 40, self.color, center=(box.centerx, box.top + 55))
        K.text(s, f"★ {score}", 30, K.INK, center=(box.centerx, box.top + 112))
        K.rbox(s, K.GREEN, self.btn, 26)
        icon_again(s, self.btn.center, 70, K.WHITE)

    def tap(self, pos):
        if self.btn.collidepoint(pos):
            self.on_again()


def top_bar(s, score, lives, extra=""):
    pygame.draw.rect(s, (12, 16, 44), (0, 0, K.W, TOP))
    K.text(s, f"★ {score}", 30, K.YELLOW, topleft=(95, 18))
    if extra:
        K.text(s, extra, 24, K.WHITE, center=(K.W // 2, TOP // 2))
    for i in range(lives):
        heart(s, (K.W - 40 - i * 46, TOP // 2), 36, K.RED)


# ============================================================== DRAW
COLORS = [(235, 50, 50), (255, 150, 40), (255, 214, 50), (60, 200, 90), (40, 200, 230),
          (60, 110, 255), (150, 80, 230), (255, 100, 180), (140, 90, 50), (20, 20, 30)]
SIZES = [6, 16, 34]


class DrawPad:
    CANVAS = pygame.Rect(0, 0, 700, 480)

    def __init__(self, app):
        self.app = app
        self.canvas = pygame.Surface(self.CANVAS.size)
        self.canvas.fill((255, 255, 255))
        self.color, self.rainbow, self.eraser = COLORS[5], False, False
        self.size = SIZES[1]
        self.hue = 0.0
        self.strokes = {}            # finger id -> last point
        self.undo = []
        self.toast, self.toast_t = "", 0
        self.flash = 0
        self.buttons = []

    # ---- palette layout (right column)
    def layout(self):
        b = []
        for i, c in enumerate(COLORS):
            b.append((pygame.Rect(706 + (i % 2) * 48, 8 + (i // 2) * 44, 42, 40), ("color", c)))
        b.append((pygame.Rect(706, 232, 42, 40), ("rainbow", None)))
        b.append((pygame.Rect(754, 232, 42, 40), ("eraser", None)))
        for i, sz in enumerate(SIZES):
            b.append((pygame.Rect(706 + (i % 2) * 48, 280 + (i // 2) * 46, 42, 42), ("size", sz)))
        b.append((pygame.Rect(754, 326, 42, 42), ("undo", None)))
        b.append((pygame.Rect(706, 380, 90, 44), ("save", None)))
        b.append((pygame.Rect(706, 430, 90, 44), ("clear", None)))
        return b

    def press(self, kind, val):
        if kind == "color":
            self.color, self.rainbow, self.eraser = val, False, False
        elif kind == "rainbow":
            self.rainbow, self.eraser = True, False
        elif kind == "eraser":
            self.eraser, self.rainbow = True, False
        elif kind == "size":
            self.size = val
        elif kind == "undo" and self.undo:
            self.canvas = self.undo.pop()
        elif kind == "clear":
            self.push_undo()
            self.canvas.fill((255, 255, 255))
        elif kind == "save":
            self.save()

    def push_undo(self):
        self.undo.append(self.canvas.copy())
        del self.undo[:-12]

    def save(self):
        os.makedirs(K.PHOTO_DIR, exist_ok=True)
        path = os.path.join(K.PHOTO_DIR, time.strftime("IMG_%Y%m%d_%H%M%S.jpg"))
        try:
            pygame.image.save(self.canvas, path)
            self.app.photos_dirty = True
            self.toast, self.toast_t, self.flash = "✓", 1.5, 1.0
        except Exception as e:
            print("draw save:", e)
            self.toast, self.toast_t = "!", 1.5

    def ink(self):
        if self.eraser:
            return (255, 255, 255)
        if self.rainbow:
            r, g, b = colorsys.hsv_to_rgb(self.hue % 1, 0.85, 1)
            return int(r * 255), int(g * 255), int(b * 255)
        return self.color

    def stroke(self, a, b):
        size = self.size * (2 if self.eraser else 1)
        col = self.ink()
        pygame.draw.line(self.canvas, col, a, b, size)
        pygame.draw.circle(self.canvas, col, b, size // 2)
        self.hue += math.dist(a, b) / 900

    def start(self, fid, p):
        if not self.CANVAS.collidepoint(p):
            for r, (kind, val) in self.layout():
                if r.collidepoint(p):
                    self.press(kind, val)
            return
        if pygame.Rect(0, 0, 84, 84).collidepoint(p):      # home button corner
            return
        if not self.strokes:
            self.push_undo()
        self.strokes[fid] = p
        size = self.size * (2 if self.eraser else 1)
        pygame.draw.circle(self.canvas, self.ink(), p, size // 2)

    def move(self, fid, p):
        if fid in self.strokes:
            p = (min(p[0], self.CANVAS.right - 1), p[1])
            self.stroke(self.strokes[fid], p)
            self.strokes[fid] = p

    def end(self, fid):
        self.strokes.pop(fid, None)

    def handle(self, ev):
        if ev.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            p = (int(ev.x * K.W), int(ev.y * K.H))
            fid = ("f", ev.finger_id)
            {pygame.FINGERDOWN: self.start, pygame.FINGERMOTION: self.move}.get(ev.type, lambda f, p: self.end(f))(fid, p)
            return
        if touch_mouse(ev):            # same touch already handled as a finger
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.start("m", ev.pos)
        elif ev.type == pygame.MOUSEMOTION and ev.buttons[0]:
            self.move("m", ev.pos)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.end("m")

    def update(self, dt):
        self.toast_t = max(0, self.toast_t - dt)
        self.flash = max(0, self.flash - dt * 3)

    def draw(self, s):
        s.blit(self.canvas, (0, 0))
        pygame.draw.rect(s, (24, 28, 60), (700, 0, 100, 480))
        for r, (kind, val) in self.layout():
            on = ((kind == "color" and val == self.color and not self.rainbow and not self.eraser)
                  or (kind == "rainbow" and self.rainbow) or (kind == "eraser" and self.eraser)
                  or (kind == "size" and val == self.size))
            if on:
                pygame.draw.rect(s, K.WHITE, r.inflate(6, 6), 3, border_radius=12)
            if kind == "color":
                pygame.draw.circle(s, val, r.center, 17)
            elif kind == "rainbow":
                for k in range(6):
                    cr = colorsys.hsv_to_rgb(k / 6, 0.85, 1)
                    pygame.draw.circle(s, [int(v * 255) for v in cr], r.center, 18 - k * 3)
            elif kind == "eraser":
                er = pygame.Rect(0, 0, 30, 20)
                er.center = r.center
                pygame.draw.rect(s, (255, 170, 190), er, border_radius=4)
                pygame.draw.rect(s, K.WHITE, (er.left, er.top, 11, er.h), border_radius=4)
            elif kind == "size":
                pygame.draw.circle(s, K.WHITE, r.center, max(3, val // 2))
            elif kind == "undo":
                pygame.draw.arc(s, K.WHITE, r.inflate(-14, -14), math.radians(-60), math.radians(200), 4)
                pygame.draw.polygon(s, K.WHITE, [(r.left + 5, r.centery - 2), (r.left + 17, r.centery - 2), (r.left + 11, r.centery + 8)])
            elif kind == "save":
                K.rbox(s, K.GREEN, r, 12, shadow=False)
                K.icon_photo(s, r.center, 32, K.WHITE)
            elif kind == "clear":
                K.rbox(s, K.RED, r, 12, shadow=False)
                K.icon_trash(s, r.center, 30, K.WHITE)
        if self.flash:
            fl = pygame.Surface(self.CANVAS.size)
            fl.fill(K.WHITE)
            fl.set_alpha(int(200 * self.flash))
            s.blit(fl, (0, 0))
        if self.toast_t:
            r = K.rbox(s, K.GREEN, (350 - 60, 200, 120, 90), 24)
            K.text(s, self.toast, 54, K.WHITE, center=r.center)


# ============================================================== BRICK BREAKER
BRICK_COLORS = [(255, 92, 168), (255, 150, 50), (255, 214, 64), (72, 214, 120), (64, 210, 230), (90, 140, 255)]


class Bricks:
    COLS, ROWS = 10, 5
    BW, BH, GAP = 70, 26, 6

    def __init__(self, app):
        self.app = app
        self.score, self.lives, self.level = 0, 3, 1
        self.paddle = pygame.Rect(0, 0, 150, 18)
        self.paddle.center = (K.W // 2, 440)
        self.parts = []
        self.overlay = None
        self.down = None
        self.new_level()

    def pattern(self, c, r):
        lv = (self.level - 1) % 4
        if lv == 0:
            return True
        if lv == 1:
            return (c + r) % 2 == 0
        if lv == 2:
            return abs(c - 4.5) <= r + 0.5
        return r != 2 or c in (0, 9)

    def new_level(self):
        x0 = (K.W - (self.COLS * (self.BW + self.GAP) - self.GAP)) // 2
        self.bricks = []
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if self.pattern(c, r):
                    rect = pygame.Rect(x0 + c * (self.BW + self.GAP), TOP + 22 + r * (self.BH + self.GAP), self.BW, self.BH)
                    self.bricks.append((rect, BRICK_COLORS[r % len(BRICK_COLORS)]))
        self.reset_ball()

    def reset_ball(self):
        self.stuck = True
        self.speed = min(520, 280 + (self.level - 1) * 35)
        self.ball = [float(self.paddle.centerx), float(self.paddle.top - 11)]
        self.vel = [0.0, 0.0]

    def launch(self):
        if self.stuck and not self.overlay:
            self.stuck = False
            sfx("launch")
            a = math.radians(random.uniform(-30, 30))
            self.vel = [self.speed * math.sin(a), -self.speed * math.cos(a)]

    def restart(self):
        self.score, self.lives, self.level = 0, 3, 1
        self.overlay = None
        self.new_level()

    def next_level(self):
        self.level += 1
        self.overlay = None
        self.new_level()

    def aim(self, x):
        self.paddle.centerx = max(self.paddle.w // 2, min(K.W - self.paddle.w // 2, int(x)))

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.down = ev.pos
            if not self.overlay and ev.pos[1] > TOP:
                self.aim(ev.pos[0])
        elif ev.type == pygame.MOUSEMOTION and ev.buttons[0] and not self.overlay:
            self.aim(ev.pos[0])
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.overlay:
                self.overlay.tap(ev.pos)
            elif self.down and ev.pos[1] > TOP and math.dist(self.down, ev.pos) < 25:
                self.launch()
            self.down = None
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE:
                self.launch()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.aim(self.paddle.centerx - 500 * dt)
        if keys[pygame.K_RIGHT]:
            self.aim(self.paddle.centerx + 500 * dt)
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 600 * dt
            p[4] -= dt
        self.parts = [p for p in self.parts if p[4] > 0]
        if self.overlay:
            return
        if self.stuck:
            self.ball = [float(self.paddle.centerx), float(self.paddle.top - 11)]
            return
        # move in small steps so a fast ball never skips a brick
        steps = max(1, int(self.speed * dt / 6))
        for _ in range(steps):
            self.step(dt / steps)
            if self.stuck or self.overlay:
                break

    def step(self, dt):
        R = 10
        bx, by = self.ball
        bx += self.vel[0] * dt
        by += self.vel[1] * dt
        if bx < R or bx > K.W - R:
            self.vel[0] = -self.vel[0]
            bx = max(R, min(K.W - R, bx))
            sfx("wall")
        if by < TOP + R:
            self.vel[1] = abs(self.vel[1])
            by = TOP + R
            sfx("wall")
        # paddle
        if self.vel[1] > 0 and self.paddle.top - R <= by <= self.paddle.bottom and \
                self.paddle.left - R <= bx <= self.paddle.right + R:
            off = (bx - self.paddle.centerx) / (self.paddle.w / 2)
            a = math.radians(max(-1, min(1, off)) * 60)
            self.vel = [self.speed * math.sin(a), -self.speed * math.cos(a)]
            by = self.paddle.top - R
            sfx("paddle")
        # bricks
        ball = pygame.Rect(bx - R, by - R, 2 * R, 2 * R)
        for i, (rect, col) in enumerate(self.bricks):
            if rect.colliderect(ball):
                ox = min(ball.right - rect.left, rect.right - ball.left)
                oy = min(ball.bottom - rect.top, rect.bottom - ball.top)
                if ox < oy:
                    self.vel[0] = -self.vel[0]
                else:
                    self.vel[1] = -self.vel[1]
                del self.bricks[i]
                self.score += 10
                sfx("brick")
                for _ in range(10):
                    self.parts.append([rect.centerx, rect.centery, random.uniform(-160, 160),
                                       random.uniform(-260, 0), random.uniform(0.4, 0.8), col])
                break
        self.ball = [bx, by]
        if by > K.H + R:
            self.lives -= 1
            sfx("lose")
            if self.lives <= 0:
                self.overlay = Overlay(self.app.w("game_over"), K.RED, self.restart)
            else:
                self.reset_ball()
        elif not self.bricks:
            sfx("win")
            self.overlay = Overlay(self.app.w("great"), K.GREEN, self.next_level)

    def draw(self, s):
        s.blit(self.app.bg, (0, 0))
        for rect, col in self.bricks:
            pygame.draw.rect(s, (10, 10, 30), rect.move(0, 4), border_radius=8)
            pygame.draw.rect(s, col, rect, border_radius=8)
            pygame.draw.rect(s, (255, 255, 255), (rect.left + 8, rect.top + 5, rect.w - 16, 5), border_radius=3)
        for x, y, _, _, life, col in self.parts:
            pygame.draw.circle(s, col, (int(x), int(y)), max(1, int(life * 8)))
        pygame.draw.rect(s, (10, 10, 30), self.paddle.move(0, 4), border_radius=9)
        pygame.draw.rect(s, K.CYAN, self.paddle, border_radius=9)
        bx, by = self.ball
        pygame.draw.circle(s, K.WHITE, (int(bx), int(by)), 10)
        pygame.draw.circle(s, K.YELLOW, (int(bx) - 3, int(by) - 3), 4)
        top_bar(s, self.score, self.lives, f"{self.app.w('level')} {self.level}")
        if self.stuck and not self.overlay:
            K.text(s, self.app.w("tap_start"), 30, K.WHITE, center=(K.W // 2, 330))
        if self.overlay:
            self.overlay.draw(s, self.score)


# ============================================================== FISH MAZE
MAZE = [
    "###################",
    "#o.......#.......o#",
    "#.##.###.#.###.##.#",
    "#.................#",
    "#.##.#.#####.#.##.#",
    "#....#...C...#....#",
    "##.#.###.#.###.#.##",
    "#........P........#",
    "#.##.###.#.###.##.#",
    "#o...C...#.......o#",
    "###################",
]
DIRS = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}


class Mover:
    def __init__(self, col, row, speed):
        self.home = (col, row)
        self.col, self.row = col, row
        self.dir = (0, 0)
        self.t = 0.0
        self.speed = speed

    def pos(self, cell, ox, oy):
        x = self.col + self.dir[0] * self.t
        y = self.row + self.dir[1] * self.t
        return ox + x * cell + cell / 2, oy + y * cell + cell / 2

    def reset(self):
        self.col, self.row = self.home
        self.dir, self.t = (0, 0), 0.0


class FishMaze:
    def __init__(self, app):
        self.app = app
        self.score, self.lives, self.level = 0, 3, 1
        self.cell = min((K.W - 20) // len(MAZE[0]), (K.H - TOP - 6) // len(MAZE))
        self.ox = (K.W - self.cell * len(MAZE[0])) // 2
        self.oy = TOP + (K.H - TOP - self.cell * len(MAZE)) // 2
        self.walls = set()
        crabs, start = [], (9, 7)
        for r, line in enumerate(MAZE):
            for c, ch in enumerate(line):
                if ch == "#":
                    self.walls.add((c, r))
                elif ch == "P":
                    start = (c, r)
                elif ch == "C":
                    crabs.append((c, r))
        self.fish = Mover(*start, 4.6)
        self.crabs = [Mover(c, r, 3.0) for c, r in crabs]
        self.crab_cols = [(255, 90, 70), (255, 140, 40), (230, 60, 140)]
        self.wall_img = self.render_walls()
        self.overlay = None
        self.down = None
        self.swiped = False
        self.new_level()

    def open(self, c, r):
        return (c, r) not in self.walls and 0 <= r < len(MAZE) and 0 <= c < len(MAZE[0])

    def new_level(self):
        # pearls everywhere the fish can actually reach
        seen, todo = {(self.fish.home)}, [self.fish.home]
        while todo:
            c, r = todo.pop()
            for dx, dy in DIRS.values():
                n = (c + dx, r + dy)
                if self.open(*n) and n not in seen:
                    seen.add(n)
                    todo.append(n)
        self.pearls = {p for p in seen if MAZE[p[1]][p[0]] in ".P C"}
        self.power = {p for p in seen if MAZE[p[1]][p[0]] == "o"}
        self.pearls.discard(self.fish.home)
        for cr in self.crabs:
            cr.speed = min(4.2, 2.8 + 0.25 * self.level)
        self.reset_round()

    def reset_round(self):
        self.fish.reset()
        self.want = (0, 0)
        for cr in self.crabs:
            cr.reset()
            cr.dead = 0
        self.scared = 0
        self.ready = 1.5

    def restart(self):
        self.score, self.lives, self.level = 0, 3, 1
        self.overlay = None
        self.new_level()

    def next_level(self):
        self.level += 1
        self.overlay = None
        self.new_level()

    def render_walls(self):
        img = pygame.Surface((K.W, K.H))      # opaque: fast to blit on a Pi 3
        img.fill((14, 30, 70))
        c = self.cell
        for (x, y) in self.walls:
            r = pygame.Rect(self.ox + x * c, self.oy + y * c, c, c)
            pygame.draw.rect(img, (40, 110, 200), r.inflate(-4, -4), border_radius=9)
            for dx, dy in DIRS.values():          # join neighbouring wall blocks
                if (x + dx, y + dy) in self.walls:
                    j = r.inflate(-4, -4).move(dx * c // 2, dy * c // 2)
                    pygame.draw.rect(img, (40, 110, 200), j, border_radius=4)
        for (x, y) in self.walls:
            r = pygame.Rect(self.ox + x * c, self.oy + y * c, c, c)
            pygame.draw.rect(img, (90, 170, 255), r.inflate(-14, -14), border_radius=6)
        return img

    # ---- input
    def handle(self, ev):
        if ev.type == pygame.KEYDOWN:
            m = {pygame.K_LEFT: "L", pygame.K_RIGHT: "R", pygame.K_UP: "U", pygame.K_DOWN: "D"}.get(ev.key)
            if m:
                self.want = DIRS[m]
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.down, self.swiped = ev.pos, False
        elif ev.type == pygame.MOUSEMOTION and ev.buttons[0] and self.down and not self.overlay:
            dx, dy = ev.pos[0] - self.down[0], ev.pos[1] - self.down[1]
            if max(abs(dx), abs(dy)) > 30:                # swipe: turn right away
                self.want = DIRS["R" if dx > 0 else "L"] if abs(dx) > abs(dy) else DIRS["D" if dy > 0 else "U"]
                self.down, self.swiped = ev.pos, True
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.overlay:
                self.overlay.tap(ev.pos)
            elif not self.swiped and ev.pos[1] > TOP:     # tap: head toward the finger
                fx, fy = self.fish.pos(self.cell, self.ox, self.oy)
                dx, dy = ev.pos[0] - fx, ev.pos[1] - fy
                if max(abs(dx), abs(dy)) > self.cell * 0.6:
                    self.want = DIRS["R" if dx > 0 else "L"] if abs(dx) > abs(dy) else DIRS["D" if dy > 0 else "U"]
            self.down = None

    # ---- movement
    def advance(self, m, dt, choose):
        speed = m.speed * (0.6 if getattr(m, "scaredy", False) else 1)
        if m.dir == (0, 0):
            nd = choose(m)
            if nd != (0, 0) and self.open(m.col + nd[0], m.row + nd[1]):
                m.dir, m.t = nd, 0.0
            else:
                return
        m.t += speed * dt
        while m.t >= 1:
            m.col += m.dir[0]
            m.row += m.dir[1]
            m.t -= 1
            self.arrive(m)
            nd = choose(m)
            if nd != (0, 0) and self.open(m.col + nd[0], m.row + nd[1]):
                m.dir = nd
            elif not self.open(m.col + m.dir[0], m.row + m.dir[1]):
                m.dir, m.t = (0, 0), 0.0
                break

    def choose_fish(self, m):
        w = self.want
        if w != (0, 0) and m.dir == (-w[0], -w[1]) and m.t > 0:
            return w
        return w if w != (0, 0) and self.open(m.col + w[0], m.row + w[1]) else m.dir

    def choose_crab(self, m):
        opts = [d for d in DIRS.values() if self.open(m.col + d[0], m.row + d[1])]
        back = (-m.dir[0], -m.dir[1])
        if len(opts) > 1 and back in opts:
            opts.remove(back)
        if not opts:
            return (0, 0)
        fx, fy = self.fish.col, self.fish.row
        if random.random() < (0.35 + 0.05 * self.level):
            key = lambda d: (m.col + d[0] - fx) ** 2 + (m.row + d[1] - fy) ** 2
            return (max if self.scared else min)(opts, key=key)
        return random.choice(opts)

    def arrive(self, m):
        if m is not self.fish:
            return
        p = (m.col, m.row)
        if p in self.pearls:
            self.pearls.discard(p)
            self.score += 10
            self.waka = not getattr(self, "waka", False)
            sfx("pearl" if self.waka else "pearl2")
        elif p in self.power:
            self.power.discard(p)
            self.score += 50
            self.scared = 7.0
            sfx("power")

    def update(self, dt):
        if self.overlay:
            return
        if self.ready > 0:
            self.ready -= dt
            return
        # instant turn-around for the fish
        f = self.fish
        if self.want != (0, 0) and f.dir == (-self.want[0], -self.want[1]) and f.t > 0:
            f.col, f.row = f.col + f.dir[0], f.row + f.dir[1]
            f.dir, f.t = self.want, 1 - f.t
        self.advance(f, dt, self.choose_fish)
        self.scared = max(0, self.scared - dt)
        for cr in self.crabs:
            if cr.dead > 0:
                cr.dead -= dt
                if cr.dead <= 0:
                    cr.reset()
                continue
            cr.scaredy = self.scared > 0
            self.advance(cr, dt, self.choose_crab)
            fx, fy = f.pos(self.cell, self.ox, self.oy)
            cx, cy = cr.pos(self.cell, self.ox, self.oy)
            if math.dist((fx, fy), (cx, cy)) < self.cell * 0.65:
                if self.scared > 0:
                    cr.dead = 3.0
                    self.score += 100
                    sfx("eat")
                else:
                    self.lives -= 1
                    sfx("lose")
                    if self.lives <= 0:
                        self.overlay = Overlay(self.app.w("game_over"), K.RED, self.restart)
                    else:
                        self.reset_round()
                    return
        if not self.pearls and not self.power:
            sfx("win")
            self.overlay = Overlay(self.app.w("great"), K.GREEN, self.next_level)

    # ---- drawing
    def draw_fish(self, s, x, y):
        c = self.cell
        d = self.fish.dir if self.fish.dir != (0, 0) else (self.want if self.want != (0, 0) else (1, 0))
        img = pygame.Surface((c * 2, c * 2), pygame.SRCALPHA)
        m = c                                   # centre of the little surface
        wig = math.sin(self.app.t * 14) * c * 0.12
        pygame.draw.polygon(img, (255, 120, 40), [(m - c * 0.35, m), (m - c * 0.8, m - c * 0.38 + wig), (m - c * 0.8, m + c * 0.38 + wig)])
        pygame.draw.ellipse(img, (255, 170, 40), (m - c * 0.45, m - c * 0.36, c * 0.95, c * 0.72))
        pygame.draw.ellipse(img, (255, 220, 120), (m - c * 0.2, m - c * 0.05, c * 0.5, c * 0.28))
        pygame.draw.circle(img, K.WHITE, (int(m + c * 0.22), int(m - c * 0.08)), max(3, c // 8))
        pygame.draw.circle(img, K.INK, (int(m + c * 0.25), int(m - c * 0.08)), max(2, c // 14))
        if d[0] < 0:
            img = pygame.transform.flip(img, True, False)
        elif d[1] != 0:
            img = pygame.transform.rotate(img, -90 if d[1] > 0 else 90)
        s.blit(img, img.get_rect(center=(int(x), int(y))))

    def draw_crab(self, s, x, y, col, i):
        c = self.cell
        r = int(c * 0.4)
        wob = math.sin(self.app.t * 10 + i) * 2
        if self.scared > 0:
            col = (90, 120, 255) if (self.scared > 2 or int(self.app.t * 8) % 2) else K.WHITE
        x, y = int(x), int(y + wob)
        for sx in (-1, 1):
            pygame.draw.line(s, col, (x + sx * r * 0.6, y + r * 0.4), (x + sx * r * 1.3, y + r * 0.9), 3)
            pygame.draw.circle(s, col, (int(x + sx * r * 1.25), int(y - r * 0.15)), int(r * 0.45))
        pygame.draw.ellipse(s, col, (x - r, y - r * 0.7, 2 * r, r * 1.5))
        for sx in (-1, 1):
            ex = int(x + sx * r * 0.4)
            pygame.draw.line(s, col, (ex, y - r * 0.5), (ex, y - r * 1.0), 3)
            pygame.draw.circle(s, K.WHITE, (ex, int(y - r * 1.05)), max(3, r // 3))
            pygame.draw.circle(s, K.INK, (ex, int(y - r * 1.05)), max(2, r // 6))

    def draw(self, s):
        s.blit(self.wall_img, (0, 0))
        c = self.cell
        for (x, y) in self.pearls:
            pygame.draw.circle(s, (235, 240, 255), (self.ox + x * c + c // 2, self.oy + y * c + c // 2), max(3, c // 9))
        pr = c // 4 + int(math.sin(self.app.t * 6) * 2)
        for (x, y) in self.power:
            pygame.draw.circle(s, (255, 120, 200), (self.ox + x * c + c // 2, self.oy + y * c + c // 2), pr)
        for i, cr in enumerate(self.crabs):
            if cr.dead <= 0:
                self.draw_crab(s, *cr.pos(c, self.ox, self.oy), self.crab_cols[i % 3], i)
        self.draw_fish(s, *self.fish.pos(c, self.ox, self.oy))
        top_bar(s, self.score, self.lives, f"{self.app.w('level')} {self.level}")
        if self.ready > 0 and not self.overlay:
            r = K.rbox(s, K.WHITE, (K.W // 2 - 110, K.H // 2 - 36, 220, 72), 24)
            K.text(s, self.app.w("ready"), 32, K.INK, center=r.center)
        if self.overlay:
            self.overlay.draw(s, self.score)


# ============================================================== MOLE DIG (a digging game)
class MoleDig:
    """Dig tunnels, collect gems, drop treasure chests on the beetles, pop them with bubbles.
    Hold a finger where the mole should go; tap the round button to blow a bubble."""
    COLS, ROWS, CELL = 15, 10, 40

    def __init__(self, app):
        self.app = app
        self.score, self.lives, self.level = 0, 3, 1
        self.ox = (K.W - self.COLS * self.CELL) // 2
        self.oy = TOP + (K.H - TOP - self.ROWS * self.CELL) // 2
        self.fire_btn = pygame.Rect(K.W - 92, K.H - 120, 84, 84)
        self.overlay = None
        self.target = None              # finger position while held
        self.new_level()

    # ---- level
    def new_level(self):
        rnd = random.Random(self.level * 7919 + random.randint(0, 9999))
        C, R = self.COLS, self.ROWS
        self.dirt = [[True] * C for _ in range(R)]
        self.spawn = (C - 1, 0)
        for c in range(C - 6, C):                      # beetle nest tunnel, top right
            self.dirt[0][c] = False
        self.start = (C // 2, R - 1)
        self.dirt[R - 1][C // 2] = False
        self.gems = set()
        while len(self.gems) < 18 + 2 * min(self.level, 6):    # gems in little clusters
            c, r = rnd.randrange(C), rnd.randrange(1, R - 1)
            for dc, dr in ((0, 0), (1, 0), (0, 1), (1, 1)):
                p = (c + dc, r + dr)
                if p[0] < C and p[1] < R - 1 and p != self.start:
                    self.gems.add(p)
        self.chests = []                                # dicts: c, r, state, t, fell, y
        tries = 0
        while len(self.chests) < 5 + min(self.level, 4) and tries < 500:
            tries += 1
            c, r = rnd.randrange(C), rnd.randrange(1, R - 3)
            if (c, r) in self.gems or any(ch["c"] == c and abs(ch["r"] - r) < 2 for ch in self.chests):
                continue
            self.chests.append({"c": c, "r": r, "state": "still", "t": 0.0, "fell": 0, "y": float(r)})
        self.coins = {}                                 # cell -> time left
        self.render_dirt()
        self.reset_round()

    def reset_round(self):
        self.mole = Mover(*self.start, 4.2)
        self.facing = (1, 0)
        self.beetles = []
        self.spawned = 0
        self.spawn_t = 2.5
        self.bubble = None
        self.cool = 0.0
        self.ready = 1.5
        self.dist = {}
        self.dist_from = None

    def restart(self):
        self.score, self.lives, self.level = 0, 3, 1
        self.overlay = None
        self.new_level()

    def next_level(self):
        self.level += 1
        self.overlay = None
        self.new_level()

    # ---- grid helpers
    def inside(self, c, r):
        return 0 <= c < self.COLS and 0 <= r < self.ROWS

    def chest_at(self, c, r, still_only=False):
        for ch in self.chests:
            if ch["c"] == c and ch["r"] == r and (not still_only or ch["state"] != "fall"):
                return ch
        return None

    def px(self, c, r):
        return self.ox + c * self.CELL + self.CELL / 2, self.oy + r * self.CELL + self.CELL / 2

    def cell_of(self, pos):
        return int((pos[0] - self.ox) // self.CELL), int((pos[1] - self.oy) // self.CELL)

    def render_dirt(self):
        img = pygame.Surface((K.W, K.H))
        img.fill((30, 18, 12))
        rnd = random.Random(3)
        for r in range(self.ROWS):
            band = [(150, 98, 52), (138, 88, 46), (126, 78, 40), (114, 70, 36)][min(3, r * 4 // self.ROWS)]
            for c in range(self.COLS):
                rect = pygame.Rect(self.ox + c * self.CELL, self.oy + r * self.CELL, self.CELL, self.CELL)
                pygame.draw.rect(img, band, rect)
                for _ in range(4):
                    pygame.draw.circle(img, (band[0] - 30, band[1] - 22, band[2] - 14),
                                       (rect.left + rnd.randrange(4, 36), rect.top + rnd.randrange(4, 36)), rnd.randrange(1, 4))
        pygame.draw.rect(img, (70, 140, 60), (self.ox, self.oy - 6, self.COLS * self.CELL, 6))      # grass
        self.dirt_img = img
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if not self.dirt[r][c]:
                    self.dig(c, r, force=True)

    def dig(self, c, r, force=False):
        if not self.inside(c, r) or (not self.dirt[r][c] and not force):
            return
        self.dirt[r][c] = False
        rect = pygame.Rect(self.ox + c * self.CELL + 3, self.oy + r * self.CELL + 3, self.CELL - 6, self.CELL - 6)
        pygame.draw.rect(self.dirt_img, (30, 18, 12), rect, border_radius=10)
        for dc, dr in DIRS.values():                    # open the wall toward dug neighbours
            n = (c + dc, r + dr)
            if self.inside(*n) and not self.dirt[n[1]][n[0]]:
                pygame.draw.rect(self.dirt_img, (30, 18, 12), rect.move(dc * self.CELL // 2, dr * self.CELL // 2), border_radius=6)
        self.dist_from = None                           # tunnels changed: recompute beetle paths

    # ---- input
    def handle(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
            self.fire()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.overlay:
                return
            if self.fire_btn.collidepoint(ev.pos):
                self.fire()
            elif ev.pos[1] > TOP:
                self.target = ev.pos
        elif ev.type == pygame.MOUSEMOTION and ev.buttons[0] and self.target:
            self.target = ev.pos
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.overlay:
                self.overlay.tap(ev.pos)
            self.target = None

    def want(self):
        keys = pygame.key.get_pressed()
        for k, d in ((pygame.K_LEFT, "L"), (pygame.K_RIGHT, "R"), (pygame.K_UP, "U"), (pygame.K_DOWN, "D")):
            if keys[k]:
                return [DIRS[d]]
        if not self.target:
            return []
        tc, tr = self.cell_of(self.target)
        dc, dr = tc - self.mole.col, tr - self.mole.row
        if dc == 0 and dr == 0:
            return []
        h = [(1 if dc > 0 else -1, 0)] if dc else []
        v = [(0, 1 if dr > 0 else -1)] if dr else []
        return h + v if abs(dc) >= abs(dr) else v + h

    def can_enter(self, d):
        c, r = self.mole.col + d[0], self.mole.row + d[1]
        if not self.inside(c, r):
            return False
        ch = self.chest_at(c, r)
        if not ch:
            return True
        if d[1] != 0 or ch["state"] == "fall":
            return False
        b = (c + d[0], r)                               # push the chest sideways
        if not self.inside(*b) or self.chest_at(*b) or any((bt.col, bt.row) == b for bt in self.beetles):
            return False
        ch["c"], ch["state"], ch["t"] = b[0], "still", 0.0
        self.dig(*b)
        return True

    def fire(self):
        if self.cool > 0 or self.bubble or self.overlay or self.ready > 0:
            return
        x, y = self.mole.pos(self.CELL, self.ox, self.oy)
        self.bubble = [x, y, self.facing]
        self.cool = 2.5
        sfx("launch")

    # ---- update
    def move_mole(self, dt):
        m = self.mole
        wants = self.want()
        if m.dir != (0, 0) and wants and wants[0] == (-m.dir[0], -m.dir[1]):     # turn around mid-cell
            m.col, m.row = m.col + m.dir[0], m.row + m.dir[1]
            m.dir, m.t = wants[0], 1 - m.t
            self.facing = m.dir
        if m.dir == (0, 0):
            for d in wants:
                if self.can_enter(d):
                    m.dir, m.t = d, 0.0
                    self.facing = d
                    self.dig(m.col + d[0], m.row + d[1])
                    break
            else:
                return
        m.t += m.speed * dt
        if m.t >= 1:
            m.col += m.dir[0]
            m.row += m.dir[1]
            m.dir, m.t = (0, 0), 0.0
            p = (m.col, m.row)
            if p in self.gems:
                self.gems.discard(p)
                self.score += 25
                sfx("pearl")
            if p in self.coins:
                del self.coins[p]
                self.score += 100
                sfx("power")

    def update_chests(self, dt):
        for ch in list(self.chests):
            c, r = ch["c"], ch["r"]
            below = (c, r + 1)
            mole_cells = {(self.mole.col, self.mole.row), (self.mole.col + self.mole.dir[0], self.mole.row + self.mole.dir[1])}
            free = (self.inside(*below) and not self.dirt[below[1]][below[0]]
                    and not self.chest_at(*below) and below not in mole_cells)
            if ch["state"] == "still":
                if free:
                    ch["state"], ch["t"] = "wobble", 0.6
                    sfx("wall")
            elif ch["state"] == "wobble":
                ch["t"] -= dt
                if not free:
                    ch["state"] = "still"
                elif ch["t"] <= 0:
                    ch["state"], ch["fell"], ch["y"] = "fall", 0, float(r)
            elif ch["state"] == "fall":
                ch["y"] += 7 * dt
                while ch["y"] >= ch["r"] + 1:
                    if free:
                        ch["r"] += 1
                        ch["fell"] += 1
                        for bt in list(self.beetles):           # squash beetles underneath
                            if (bt.col, bt.row) == (ch["c"], ch["r"]) or (bt.col + bt.dir[0], bt.row + bt.dir[1]) == (ch["c"], ch["r"]):
                                self.beetles.remove(bt)
                                self.score += 250
                                sfx("eat")
                        below = (ch["c"], ch["r"] + 1)
                        mole_cells = {(self.mole.col, self.mole.row)}
                        free = (self.inside(*below) and not self.dirt[below[1]][below[0]]
                                and not self.chest_at(*below) and below not in mole_cells)
                    else:
                        ch["y"] = float(ch["r"])
                        if ch["fell"] >= 2:                   # big drop: it cracks open
                            self.chests.remove(ch)
                            self.coins[(ch["c"], ch["r"])] = 10.0
                            sfx("brick")
                        else:
                            ch["state"] = "still"
                        break

    def beetle_paths(self):
        src = (self.mole.col, self.mole.row)
        if self.dist_from == src:
            return
        self.dist_from = src
        self.dist = {src: 0}
        todo = [src]
        while todo:
            nxt = []
            for c, r in todo:
                for dc, dr in DIRS.values():
                    n = (c + dc, r + dr)
                    if self.inside(*n) and not self.dirt[n[1]][n[0]] and n not in self.dist:
                        self.dist[n] = self.dist[(c, r)] + 1
                        nxt.append(n)
            todo = nxt

    def move_beetles(self, dt):
        self.spawn_t -= dt
        alive_max = 2 + self.level // 2
        if self.spawn_t <= 0 and len(self.beetles) < alive_max and self.spawned < 4 + self.level:
            if not self.chest_at(*self.spawn):
                self.beetles.append(Mover(*self.spawn, min(3.4, 2.0 + 0.2 * self.level)))
                self.spawned += 1
            self.spawn_t = 4.0
        self.beetle_paths()
        for b in self.beetles:
            digging = getattr(b, "digging", False)
            b.t += b.speed * dt * (0.45 if digging else 1) if b.dir != (0, 0) else 0
            if b.dir != (0, 0) and b.t < 1:
                continue
            if b.dir != (0, 0):
                b.col, b.row = b.col + b.dir[0], b.row + b.dir[1]
                self.dig(b.col, b.row)
            b.t = 0.0
            b.digging = False
            opts = []
            if (b.col, b.row) in self.dist:                 # a tunnel leads to the mole: follow it
                for d in DIRS.values():
                    n = (b.col + d[0], b.row + d[1])
                    if self.inside(*n) and not self.dirt[n[1]][n[0]] and not self.chest_at(*n):
                        opts.append((self.dist.get(n, 999) + random.random() * 1.5, d))
            else:                                           # no tunnel yet: slowly dig toward the mole
                for d in DIRS.values():
                    n = (b.col + d[0], b.row + d[1])
                    if self.inside(*n) and not self.chest_at(*n):
                        far = abs(n[0] - self.mole.col) + abs(n[1] - self.mole.row)
                        opts.append((far + random.random() * 2, d))
            b.dir = min(opts)[1] if opts else (0, 0)
            if b.dir != (0, 0):
                n = (b.col + b.dir[0], b.row + b.dir[1])
                b.digging = self.dirt[n[1]][n[0]]

    def move_bubble(self, dt):
        if not self.bubble:
            return
        x, y, d = self.bubble
        x += d[0] * 9 * self.CELL * dt
        y += d[1] * 9 * self.CELL * dt
        c, r = self.cell_of((x, y))
        if not self.inside(c, r) or self.dirt[r][c] or self.chest_at(c, r):
            self.bubble = None
            return
        self.bubble = [x, y, d]
        for b in list(self.beetles):
            if math.dist((x, y), b.pos(self.CELL, self.ox, self.oy)) < self.CELL * 0.6:
                self.beetles.remove(b)
                self.bubble = None
                self.score += 250
                sfx("eat")
                return

    def update(self, dt):
        if self.overlay:
            return
        if self.ready > 0:
            self.ready -= dt
            return
        self.cool = max(0, self.cool - dt)
        self.move_mole(dt)
        self.update_chests(dt)
        self.move_beetles(dt)
        self.move_bubble(dt)
        for p in list(self.coins):
            self.coins[p] -= dt
            if self.coins[p] <= 0:
                del self.coins[p]
        mx, my = self.mole.pos(self.CELL, self.ox, self.oy)
        for b in self.beetles:
            if math.dist((mx, my), b.pos(self.CELL, self.ox, self.oy)) < self.CELL * 0.6:
                self.lives -= 1
                sfx("lose")
                if self.lives <= 0:
                    self.overlay = Overlay(self.app.w("game_over"), K.RED, self.restart)
                else:
                    self.reset_round()
                return
        if not self.gems:
            sfx("win")
            self.overlay = Overlay(self.app.w("great"), K.GREEN, self.next_level)

    # ---- drawing
    def draw_mole(self, s, x, y):
        c = self.CELL
        img = pygame.Surface((c * 2, c * 2), pygame.SRCALPHA)
        m = c
        step = math.sin(self.app.t * 16) * 2 if self.mole.dir != (0, 0) else 0
        pygame.draw.ellipse(img, (70, 60, 70), (m - c * 0.45, m - c * 0.35, c * 0.9, c * 0.72))
        pygame.draw.ellipse(img, (110, 95, 110), (m - c * 0.3, m - c * 0.05, c * 0.5, c * 0.3))
        pygame.draw.circle(img, (255, 140, 170), (int(m + c * 0.46), int(m)), int(c * 0.12))
        pygame.draw.circle(img, K.INK, (int(m + c * 0.22), int(m - c * 0.12)), 3)
        for k in (-1, 1):                               # little digging claws
            pygame.draw.circle(img, (255, 200, 180), (int(m + c * 0.25 + step * k), int(m + c * 0.3)), 5)
        if self.facing[0] < 0:
            img = pygame.transform.flip(img, True, False)
        s.blit(img, img.get_rect(center=(int(x), int(y))))

    def draw_beetle(self, s, x, y, i):
        c = self.CELL
        x, y = int(x), int(y)
        leg = math.sin(self.app.t * 18 + i) * 4
        for k in (-1, 0, 1):
            pygame.draw.line(s, K.INK, (x - 14, y + k * 7), (x - 21, y + k * 7 + leg), 3)
            pygame.draw.line(s, K.INK, (x + 14, y + k * 7), (x + 21, y + k * 7 - leg), 3)
        pygame.draw.ellipse(s, (150, 60, 200), (x - 15, y - 13, 30, 28))
        pygame.draw.line(s, (90, 30, 130), (x, y - 12), (x, y + 14), 2)
        pygame.draw.circle(s, (90, 30, 130), (x, y - 14), 8)
        for k in (-1, 1):
            pygame.draw.line(s, K.INK, (x + k * 3, y - 20), (x + k * 9, y - 27 + leg / 2), 2)
            pygame.draw.circle(s, K.WHITE, (x + k * 4, y - 15), 3)

    def draw(self, s):
        s.blit(self.dirt_img, (0, 0))
        c = self.CELL
        for (gc, gr) in self.gems:
            x, y = self.px(gc, gr)
            pts = [(x, y - 11), (x + 10, y - 2), (x, y + 12), (x - 10, y - 2)]
            pygame.draw.polygon(s, (60, 220, 110), pts)
            pygame.draw.polygon(s, (190, 255, 210), [(x, y - 11), (x + 4, y - 3), (x - 4, y - 3)])
        for (cc, cr) in self.coins:
            x, y = self.px(cc, cr)
            for k, (dx, dy) in enumerate(((-7, 6), (6, 7), (0, -2))):
                pygame.draw.circle(s, (240, 180, 30), (int(x + dx), int(y + dy)), 8)
                pygame.draw.circle(s, (255, 230, 120), (int(x + dx - 2), int(y + dy - 2)), 3)
        for ch in self.chests:
            x, y = self.px(ch["c"], ch["y"] if ch["state"] == "fall" else ch["r"])
            if ch["state"] == "wobble":
                x += math.sin(self.app.t * 40) * 3
            box = pygame.Rect(0, 0, 34, 28)
            box.center = (int(x), int(y) + 2)
            pygame.draw.rect(s, (30, 18, 12), box.inflate(4, 4), border_radius=7)
            pygame.draw.rect(s, (200, 120, 40), box, border_radius=6)
            pygame.draw.rect(s, (160, 85, 30), (box.left, box.top, box.w, 11), border_radius=6)
            pygame.draw.rect(s, (255, 215, 70), (box.left, box.top + 9, box.w, 4))
            pygame.draw.rect(s, (255, 215, 70), (box.centerx - 4, box.top + 7, 8, 10), border_radius=2)
        for i, b in enumerate(self.beetles):
            self.draw_beetle(s, *b.pos(c, self.ox, self.oy), i)
        self.draw_mole(s, *self.mole.pos(c, self.ox, self.oy))
        if self.bubble:
            pygame.draw.circle(s, (150, 220, 255), (int(self.bubble[0]), int(self.bubble[1])), 10)
            pygame.draw.circle(s, K.WHITE, (int(self.bubble[0]) - 3, int(self.bubble[1]) - 3), 3)
        # bubble button (right margin)
        fb = self.fire_btn
        ready = self.cool == 0 and not self.bubble
        pygame.draw.circle(s, (10, 10, 30), (fb.centerx, fb.centery + 5), fb.w // 2)
        pygame.draw.circle(s, K.CYAN if ready else (80, 90, 110), fb.center, fb.w // 2)
        if not ready and self.cool:
            pygame.draw.arc(s, K.WHITE, fb.inflate(-8, -8), math.pi / 2, math.pi / 2 + 2 * math.pi * (1 - self.cool / 2.5), 5)
        pygame.draw.circle(s, K.WHITE, fb.center, 18, 4)
        pygame.draw.circle(s, K.WHITE, (fb.centerx - 6, fb.centery - 6), 5)
        top_bar(s, self.score, self.lives, f"{self.app.w('level')} {self.level}  ◆ {len(self.gems)}")
        if self.ready > 0 and not self.overlay:
            r = K.rbox(s, K.WHITE, (K.W // 2 - 110, K.H // 2 - 36, 220, 72), 24)
            K.text(s, self.app.w("ready"), 32, K.INK, center=r.center)
        if self.overlay:
            self.overlay.draw(s, self.score)


GAMES = [("bricks", Bricks), ("maze", FishMaze), ("dig", MoleDig)]
