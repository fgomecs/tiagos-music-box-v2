# 🎵 Tiago's Music Box V2 (handheld, touch)

Pi 3 + Waveshare 4.3" DSI capacitive touch (800×480) + PiSugar S Plus 5000 mAh + Pi camera. Touch only. V1 (button + OLED) lives in [music-button-pi](https://github.com/fgomecs/music-button-pi) and is separate.

![V2 wiring diagram](docs/wiring-v2.png)

_Details: see [Wiring](#wiring)._

## Screenshots

_Rendered from the real code (`v2/kidbox.py`, `v2/games.py`, `portal.py`) at the panel's 800×480. The camera/photo images are drawn samples, not real photos. Scripts: `docs/src/kidbox_shots.py`, `docs/src/shoot.py`._

### Touch screen

| Home | Music (playing) | Home + now playing |
|---|---|---|
| <img src="docs/screenshots/v2-1-home.png" width="260"> | <img src="docs/screenshots/v2-2-music.png" width="260"> | <img src="docs/screenshots/v2-3-home-playing.png" width="260"> |
| **Camera** | **Photos** | **Photo viewer** |
| <img src="docs/screenshots/v2-4-camera.png" width="260"> | <img src="docs/screenshots/v2-5-photos.png" width="260"> | <img src="docs/screenshots/v2-6-viewer.png" width="260"> |
| **Draw** | **Games** | **Bricks** |
| <img src="docs/screenshots/v2-7-draw.png" width="260"> | <img src="docs/screenshots/v2-8-games.png" width="260"> | <img src="docs/screenshots/v2-9-bricks.png" width="260"> |
| **Fish Maze** | | |
| <img src="docs/screenshots/v2-10-maze.png" width="260"> | | |

### Web portal (http://&lt;pi-ip&gt;:8080)

| Desktop | Phone |
|---|---|
| <img src="docs/screenshots/portal-desktop.png" width="560"> | <img src="docs/screenshots/portal-phone.png" width="200"> |

```mermaid
flowchart LR
    HOME[Home] --> MUSIC[🎵 Music<br/>playlist · ⏮ ⏯ ⏭ · animations]
    HOME --> CAM[📷 Camera<br/>live viewfinder · big shutter]
    HOME --> PH[🖼 Photos<br/>grid · swipe · long-press delete]
    CAM --> PH
    HOME --> DRAW[🖌 Draw<br/>colours · rainbow · undo · save to Photos]
    HOME --> GAMES[🎮 Games<br/>Bricks · Fish Maze]
    DRAW --> PH
    PORTAL[Web portal :8080] -. now playing · add songs · photos · language .- MUSIC
```

## Wiring

_Diagram source: `docs/src/gen_v2.py` (regenerate: `cd docs/src && python3 gen_v2.py ../wiring-v2.svg && rsvg-convert -w 1500 ../wiring-v2.svg -o ../wiring-v2.png`)._

## Hardware stack (back to front)
```
 [ Pi 3 ]          ← DSI ribbon + 2 power wires to the screen, camera ribbon on CSI
 [ PiSugar S Plus ]← battery, pogo pins under the Pi (charge HERE, never the Pi's port)
 ║  ║  ║  ║       ← M2.5 standoffs (~20 mm)
 [ 4.3" screen ]   ← faces the kid; camera on the back faces out
```

## Setup
```bash
git clone git@github.com:fgomecs/tiagos-music-box-v2.git ~/kidbox
cd ~/kidbox && bash v2/setup.sh && sudo reboot
```
Installs packages, enables the 4.3" DSI overlay, starts the kids app at boot, installs the portal (http://<pi-ip>:8080).

## Adding songs & stories
Portal → *Add songs & stories* → paste `URL Name` rows → *Check size & space* → *Download & add*. Or SSH: `python3 add_songs.py`. Songs (`song*.mp3`) and photos are not stored in git.

## Files
| File | Purpose |
|---|---|
| `v2/kidbox.py` | Kids app (music, camera, photos, draw, games menu), 800×480 touch |
| `v2/games.py` | Draw pad, Bricks (drag paddle, tap to launch), Fish Maze (swipe or tap to steer) |
| `v2/setup.sh` | One-time setup |
| `portal.py` | Web portal: now playing + live screen mirror, add songs, photos, language |
| `add_songs.py` | Song download engine (yt-dlp + deno), library/capacity report |
| `musicstate.py` | Shared state between app and portal (/dev/shm) |
| `config.py` | V2 song list (SONGS + SONG_NAMES, same order) |
| `song_sources.json` | YouTube URL per song file |

<!-- SONGS:START -->
| # | File | Name | Source |
|---|---|---|---|
<!-- SONGS:END -->

## Notes
- Video is locked: audio-only (`v2/settings.json` → `video_unlocked`).
- Photos: `~/Pictures/kidbox`. Download/delete from the portal.
- Test on a PC: `KIDBOX_WINDOW=1 python3 v2/kidbox.py`
