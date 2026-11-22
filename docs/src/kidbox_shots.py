"""Render the real V2 kidbox screens (800x480) to PNGs, headless.
Usage: python3 kidbox_shots.py <v2 sandbox dir> <out dir>"""
import math
import os
import sys

repo, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["KIDBOX_WINDOW"] = "1"
os.environ["KIDBOX_PHOTOS"] = os.path.join(out, "_photos")
sys.path.insert(0, os.path.join(repo, "v2"))

import pygame                      # noqa: E402
import kidbox as kb                # noqa: E402
import games                       # noqa: E402
from PIL import Image, ImageDraw   # noqa: E402


# ---------- sample pictures for the camera/photos screens (drawn, not real photos)
def scene(seed, w=640, h=480):
    import random
    r = random.Random(seed)
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    sky_top = r.choice([(110, 180, 255), (255, 170, 120), (140, 200, 255), (90, 150, 230)])
    for y in range(h):
        k = y / h
        d.line((0, y, w, y), fill=tuple(int(c * (1 - k * 0.35) + 255 * k * 0.25) for c in sky_top))
    gy = int(h * r.uniform(0.6, 0.72))
    d.rectangle((0, gy, w, h), fill=r.choice([(90, 180, 90), (230, 205, 140), (70, 150, 80)]))
    sx, sy = r.randint(60, w - 60), r.randint(40, 140)
    d.ellipse((sx - 40, sy - 40, sx + 40, sy + 40), fill=(255, 220, 80))
    for _ in range(r.randint(1, 3)):                       # trees
        tx = r.randint(40, w - 40)
        d.rectangle((tx - 8, gy - 60, tx + 8, gy + 10), fill=(110, 70, 40))
        d.ellipse((tx - 45, gy - 140, tx + 45, gy - 40), fill=(50, 140, 60))
    if r.random() < 0.6:                                   # house
        hx = r.randint(100, w - 200)
        d.rectangle((hx, gy - 110, hx + 140, gy + 10), fill=r.choice([(240, 120, 110), (250, 240, 220), (120, 160, 240)]))
        d.polygon([(hx - 15, gy - 110), (hx + 70, gy - 175), (hx + 155, gy - 110)], fill=(150, 60, 50))
        d.rectangle((hx + 55, gy - 50, hx + 85, gy + 10), fill=(90, 60, 40))
    return im


os.makedirs(os.environ["KIDBOX_PHOTOS"], exist_ok=True)
for i in range(10):
    scene(i).save(os.path.join(os.environ["KIDBOX_PHOTOS"], f"IMG_202611{10 + i:02d}_101500.jpg"), quality=88)

app = kb.KidBox()


class FakeProc:                     # makes the player look like it is playing
    def poll(self):
        return None


def save(name, frames=1, dt=1 / 30):
    for _ in range(frames):
        app.t += dt
        app.buttons = []
        getattr(app, "draw_" + app.page)(dt)
    pygame.image.save(app.screen, os.path.join(out, name))
    print(name)


# 1 home (nothing playing)
app.t = 0.6
save("v2-1-home.png", 30)

# 2 music, playing song #10
app.player.proc, app.player.index, app.player.pos, app.player.dur = FakeProc(), 9, 52.0, 141.0
app.player.poll = lambda: True
app.scroll = 64 * 5
app.go("music")
save("v2-2-music.png", 20)

# 3 home with the now-playing bar
app.go("home")
save("v2-3-home-playing.png", 10)

# 4 camera viewfinder (fake frame instead of the Pi camera)
cam_img = scene(42)
app.camera.open = lambda: True
app.camera.cam = object()
app.camera.frame = lambda: pygame.image.fromstring(cam_img.tobytes(), cam_img.size, "RGB")
app.go("camera")
save("v2-4-camera.png", 3)

# 5 photos grid
app.camera.close = lambda: None
app.go("photos")
save("v2-5-photos.png", 3)

# 6 photo viewer
app.open_photo(2)
save("v2-6-viewer.png", 2)

# 7 draw pad with a drawing
app.start(games.DrawPad)
pad = app.activity


def stroke(points):
    E = pygame.event.Event
    pad.handle(E(pygame.MOUSEBUTTONDOWN, pos=points[0], button=1, touch=False))
    for p in points[1:]:
        pad.handle(E(pygame.MOUSEMOTION, pos=p, rel=(0, 0), buttons=(1, 0, 0), touch=False))
        pad.update(1 / 60)
    pad.handle(E(pygame.MOUSEBUTTONUP, pos=points[-1], button=1, touch=False))


pad.press("rainbow", None)
pad.press("size", games.SIZES[-1])
for rad in (230, 200):
    stroke([(350 + rad * math.cos(math.radians(a)), 420 - rad * math.sin(math.radians(a))) for a in range(180, -1, -3)])
pad.press("color", games.COLORS[2])
stroke([(120 + 40 * math.cos(math.radians(a)), 100 + 40 * math.sin(math.radians(a))) for a in range(0, 365, 8)])
pad.press("color", games.COLORS[0])
stroke([(300, 400), (300, 330), (350, 290), (400, 330), (400, 400), (300, 400)])
save("v2-7-draw.png", 2)

# 8 games menu
app.go("games")
save("v2-8-games.png", 20)

# 9 bricks, 10 fish maze (a few frames in)
for name, cls in (("v2-9-bricks.png", games.Bricks), ("v2-10-maze.png", games.FishMaze)):
    app.start(cls)
    save(name, 45)
