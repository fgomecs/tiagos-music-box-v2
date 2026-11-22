import sys
from svglib import SVG

s = SVG(1500, 1060)
s.title("Tiago's Music Box V2 · wiring",
        "Raspberry Pi 3 · Waveshare 4.3\" DSI capacitive touch (800×480) · PiSugar S Plus 5000 mAh · Pi Camera v1.3 · touch only")

# ---------------- Pi 3 (top view) ----------------
PX, PY, PW, PH = 470, 210, 520, 340
s.rect(PX, PY, PW, PH, fill="#1e7a3c", stroke="#0d4d22", sw=3, rx=14)
s.text(PX + PW / 2, PY + 175, "Raspberry Pi 3", 20, "#fff", "middle", "bold")
s.text(PX + PW / 2, PY + 198, "(top view)", 12, "#bfe3c9", "middle")
s.rect(PX + 190, PY + 100, 90, 60, fill="#bbb", stroke="#666", rx=4)          # SoC shield
# GPIO header: 2x20 along the top edge, pin 1 at the left, even pins on the outer row
pin_xy = {}
for i in range(20):
    for row in range(2):
        n = i * 2 + (2 if row == 0 else 1)
        cx = PX + 40 + i * 21
        cy = PY + 18 + row * 20
        hot = n in (2, 4, 6)
        fill = "#d62828" if n in (2, 4) else ("#111" if n == 6 else "#9a9a9a")
        s.rect(cx - 7, cy - 7, 14, 14, fill=fill, stroke="#000", sw=1, rx=2)
        pin_xy[n] = (cx, cy)
s.text(PX + 40, PY + 66, "pin 1", 10, "#fff", "middle")

# ports
s.rect(PX + PW - 10, PY + 30, 50, 70, fill="#ccc", stroke="#666", rx=3)
s.rect(PX + PW - 10, PY + 120, 50, 70, fill="#ccc", stroke="#666", rx=3)
s.rect(PX + PW - 10, PY + 220, 55, 80, fill="#ccc", stroke="#666", rx=3)
s.text(PX + PW + 50, PY + 70, "USB", 11, "#333")
s.text(PX + PW + 50, PY + 160, "USB", 11, "#333")
s.text(PX + PW + 52, PY + 265, "Ethernet", 11, "#333")
s.rect(PX + 30, PY + PH - 20, 40, 30, fill="#ccc", stroke="#666", rx=3)
s.text(PX + 50, PY + PH + 26, "micro-USB", 10, "#333", "middle")
s.text(PX + 50, PY + PH + 39, "(do NOT use)", 10, "#d62828", "middle")
s.rect(PX + 130, PY + PH - 20, 70, 30, fill="#ccc", stroke="#666", rx=3)
s.text(PX + 165, PY + PH + 26, "HDMI", 10, "#333", "middle")
s.rect(PX + 380, PY + PH - 24, 36, 34, fill="#222", stroke="#000", rx=17)
s.text(PX + 398, PY + PH + 26, "3.5 mm audio", 10, "#333", "middle")
s.text(PX + 398, PY + PH + 39, "→ speaker", 10, "#333", "middle")
# DSI (left edge) and CSI (bottom area) connectors
s.rect(PX + 12, PY + 120, 16, 110, fill="#f4f4f4", stroke="#555", rx=2)
s.text(PX + 40, PY + 180, "DSI", 11, "#fff")
s.rect(PX + 270, PY + PH - 40, 90, 14, fill="#f4f4f4", stroke="#555", rx=2)
s.text(PX + 315, PY + PH - 48, "CSI (camera)", 11, "#fff", "middle")

# ---------------- screen ----------------
SX, SY = 40, 230
s.rect(SX, SY, 330, 220, fill="#111", stroke="#000", sw=3, rx=10)
s.rect(SX + 16, SY + 16, 298, 178, fill="#24476e", stroke="#335", rx=4)
s.text(SX + 165, SY + 95, "Waveshare 4.3\" DSI", 15, "#cfe8ff", "middle", "bold")
s.text(SX + 165, SY + 117, "800×480 · capacitive touch", 12, "#cfe8ff", "middle")
s.text(SX + 165, SY + 137, "(touch data goes over the ribbon)", 11, "#9ec3e6", "middle")
s.pin(SX + 330, SY + 30)
s.pin(SX + 330, SY + 55)
s.text(SX + 316, SY + 34, "5V", 10, "#fff", "end")
s.text(SX + 316, SY + 59, "GND", 10, "#fff", "end")

# DSI ribbon
s.wire([(SX + 330, SY + 150), (PX - 10, SY + 150), (PX - 10, PY + 175), (PX + 20, PY + 175)], "#e9e9e9", 22, dots=False)
s.text(415, SY + 155, "DSI ribbon (15-pin)", 11, "#333", "middle")
# screen power from the GPIO header
x2, y2 = pin_xy[2]
x6, y6 = pin_xy[6]
s.wire([(SX + 330, SY + 30), (410, SY + 30), (410, PY - 70), (x2, PY - 70), (x2, y2)], "red", 4,
       "5V → pin 2", (470, PY - 70))
s.wire([(SX + 330, SY + 55), (440, SY + 55), (440, PY - 45), (x6, PY - 45), (x6, y6)], "black", 4,
       "GND → pin 6", (490, PY - 45))

# ---------------- camera ----------------
CX, CY = PX + 260, 660
s.rect(CX, CY, 110, 100, fill="#1e7a3c", stroke="#0d4d22", sw=2, rx=6)
s.circle(CX + 55, CY + 50, 22, fill="#222", stroke="#000")
s.circle(CX + 55, CY + 50, 9, fill="#3a5f8f", stroke="#000", sw=1)
s.text(CX + 125, CY + 50, "Pi Camera v1.3", 13, "#222", "start", "bold"); s.text(CX + 125, CY + 68, "on the back, facing out", 11, "#555")
s.wire([(PX + 315, PY + PH - 26), (PX + 315, CY)], "#f0dfa8", 16, dots=False)
s.text(PX + 340, 620, "CSI ribbon", 11, "#333")

# ---------------- PiSugar ----------------
BX, BY = 1115, 210
s.rect(BX, BY, 330, 230, fill="#2b2b2b", stroke="#000", sw=3, rx=12)
s.rect(BX + 20, BY + 70, 290, 130, fill="#3a3a3a", stroke="#555", rx=8)
s.text(BX + 165, BY + 125, "PiSugar S Plus", 16, "#fff", "middle", "bold")
s.text(BX + 165, BY + 147, "5000 mAh LiPo (mounted UNDER the Pi)", 11, "#ccc", "middle")
s.rect(BX + 25, BY + 18, 60, 30, fill="#ccc", stroke="#666", rx=6)
s.text(BX + 55, BY + 62, "USB-C", 10, "#fff", "middle")
s.text(BX + 100, BY + 32, "← charge HERE", 13, "#7CFC9A", weight="bold")
s.text(BX + 100, BY + 48, "(never the Pi's micro-USB)", 11, "#ccc")
s.circle(BX + 290, BY + 34, 12, fill="#e63946", stroke="#000")
s.text(BX + 270, BY + 38, "power", 10, "#fff", "end")
for i, (lab, n, c) in enumerate((("5V", 2, "#d62828"), ("5V", 4, "#d62828"), ("GND", 6, "#111"))):
    py = BY + 160 + i * 24
    s.rect(BX - 9, py - 6, 18, 12, fill="#d4af37", stroke="#000", sw=1, rx=3)
    s.text(BX + 16, py + 4, f"pogo {lab}", 10, "#fff")
    hx, hy = pin_xy[n]
    lvl = PY - 22 + i * 7 if False else PY - 100 - i * 12
    vx = BX - 40 - i * 14
    s.add(f'<polyline points="{hx},{hy - 8} {hx},{lvl} {vx},{lvl} {vx},{py} {BX - 9},{py}" fill="none" '
          f'stroke="{c}" stroke-width="2" stroke-dasharray="6 5"/>')
s.text(BX + 165, BY + 260, "pogo pins press on the underside of header pins 2 · 4 · 6 (no wires)", 11, "#333", "middle")

# ---------------- stack side view ----------------
TX, TY = 60, 615
s.text(TX, TY, "Stack (side view, back → front)", 15, "#222", weight="bold")
layers = [("Raspberry Pi 3  ← DSI + CSI ribbons, 2 power wires", "#1e7a3c", 26),
          ("PiSugar S Plus  ← pogo pins under the Pi", "#2b2b2b", 30),
          ("M2.5 standoffs ~20 mm", None, 46),
          ("4.3\" screen  ← faces Tiago; camera faces out the back", "#111", 22)]
yy = TY + 20
for lab, c, h in layers:
    if c:
        s.rect(TX, yy, 330, h, fill=c, stroke="#000", sw=1.5, rx=4)
    else:
        for k in range(4):
            s.rect(TX + 20 + k * 95, yy, 8, h, fill="#c9a227", stroke="#7a5a1e", sw=1, rx=1)
    s.text(TX + 345, yy + h / 2 + 4, lab, 12, "#333")
    yy += h + 8

s.legend_box(60, 870, 920, [
    "• Display overlay (setup.sh): dtoverlay=vc4-kms-dsi-waveshare-panel,4_3_inch in /boot/firmware/config.txt",
    "• Camera: picamera2, opened only on the Camera screen to save battery. Photos → ~/Pictures/kidbox",
    "• The screen gets power from the header (5V pin 2, GND pin 6); video + touch go over the DSI ribbon.",
    "• No GPIO buttons in V2: everything is touch. Free GPIO pins are left for future add-ons.",
    "• Ribbons: blue/contact side matters. DSI and CSI latches must be fully closed or nothing shows.",
], "Notes")

s.save(sys.argv[1])
