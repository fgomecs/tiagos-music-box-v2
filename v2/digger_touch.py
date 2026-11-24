#!/usr/bin/env python3
"""
digger_touch.py - play Digger on the touchscreen (runs as root while Digger is open).

Digger only understands the keyboard, so this reads the touchscreen and presses keys
on a virtual keyboard:
  * swipe          -> Digger turns and KEEPS going that way (like Pac-Man)
  * tap            -> fire (F1) / start a game on the title screen
  * hold any corner 3 s -> quit Digger and go back to Tiago's games
"""
import os
import select
import sys
import time

QUIT_FLAG = "/tmp/kidbox-digger-quit"      # kidbox closes Digger when this appears

from evdev import InputDevice, UInput, ecodes as e, list_devices

SWIPE = 0.06          # fraction of the screen a finger must move to count as a swipe
TAP_MAX = 0.35        # seconds
QUIT_HOLD = 3.0


def find_touch():
    for path in list_devices():
        d = InputDevice(path)
        caps = d.capabilities().get(e.EV_ABS, [])
        codes = [c[0] if isinstance(c, tuple) else c for c in caps]
        if e.ABS_MT_POSITION_X in codes or (e.ABS_X in codes and e.BTN_TOUCH in d.capabilities().get(e.EV_KEY, [])):
            return d
    return None


def main():
    try:
        os.remove(QUIT_FLAG)
    except FileNotFoundError:
        pass
    dev = find_touch()
    print("digger_touch: using", dev.path if dev else None, dev.name if dev else "", flush=True)
    if not dev:
        print("digger_touch: no touchscreen found", flush=True)
        time.sleep(3600)
        return
    ax = dev.absinfo(e.ABS_MT_POSITION_X if e.ABS_MT_POSITION_X in dict(dev.capabilities()[e.EV_ABS]) else e.ABS_X)
    ay = dev.absinfo(e.ABS_MT_POSITION_Y if e.ABS_MT_POSITION_Y in dict(dev.capabilities()[e.EV_ABS]) else e.ABS_Y)
    keys = [e.KEY_LEFT, e.KEY_RIGHT, e.KEY_UP, e.KEY_DOWN, e.KEY_F1, e.KEY_F10, e.KEY_ENTER]
    ui = UInput({e.EV_KEY: keys}, name="kidbox-digger-keys")
    held = None
    x = y = None
    down = None            # (x, y, t) where the finger landed
    start = None
    swiped = False
    quit_sent = False
    saw_btn = False

    def tap(k):
        ui.write(e.EV_KEY, k, 1); ui.syn(); time.sleep(0.06)
        ui.write(e.EV_KEY, k, 0); ui.syn()

    def hold(k):
        nonlocal held
        if held == k:
            return
        if held:
            ui.write(e.EV_KEY, held, 0)
        ui.write(e.EV_KEY, k, 1); ui.syn()
        held = k

    touching = False

    def finger(is_down):
        nonlocal touching, down, start, swiped, quit_sent
        if is_down:
            if not touching:
                touching, down, start, swiped, quit_sent = True, None, None, False, False
        else:
            if touching and down and not swiped and not quit_sent and time.time() - down[2] < TAP_MAX:
                tap(e.KEY_F1)                                    # tap = fire / start a game
            touching, down = False, None

    try:
        while True:
            r, _, _ = select.select([dev.fd], [], [], 0.1)
            now = time.time()
            in_corner = touching and down and (down[0] < 0.15 or down[0] > 0.85) and (down[1] < 0.2 or down[1] > 0.8)
            if in_corner and not swiped and not quit_sent and now - down[2] > QUIT_HOLD:
                quit_sent = True
                print("digger_touch: corner hold -> quit", flush=True)
                if held:
                    ui.write(e.EV_KEY, held, 0); ui.syn(); held = None
                open(QUIT_FLAG, "w").close()
            if not r:
                continue
            for ev in dev.read():
                if ev.type == e.EV_KEY and ev.code == e.BTN_TOUCH:
                    saw_btn = True
                    finger(ev.value == 1)
                elif ev.type == e.EV_ABS and ev.code == e.ABS_MT_TRACKING_ID:
                    if not saw_btn:                              # panels without BTN_TOUCH
                        finger(ev.value >= 0)
                elif ev.type == e.EV_ABS and ev.code in (e.ABS_MT_POSITION_X, e.ABS_X):
                    x = (ev.value - ax.min) / max(1, ax.max - ax.min)
                elif ev.type == e.EV_ABS and ev.code in (e.ABS_MT_POSITION_Y, e.ABS_Y):
                    y = (ev.value - ay.min) / max(1, ay.max - ay.min)
                elif ev.type == e.EV_SYN and touching and x is not None and y is not None:
                    if down is None:
                        down = (x, y, time.time())
                        start = (x, y)
                        continue
                    dx, dy = x - start[0], (y - start[1]) * 0.6   # screen is wider than tall
                    if max(abs(dx), abs(dy)) > SWIPE:
                        swiped = True
                        if abs(dx) > abs(dy):
                            hold(e.KEY_RIGHT if dx > 0 else e.KEY_LEFT)
                        else:
                            hold(e.KEY_DOWN if dy > 0 else e.KEY_UP)
                        start = (x, y)
    except KeyboardInterrupt:
        pass
    finally:
        if held:
            ui.write(e.EV_KEY, held, 0); ui.syn()
        ui.close()


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGTERM, lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    main()
