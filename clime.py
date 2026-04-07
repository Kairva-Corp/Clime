#!/usr/bin/env python3
"""
CLIME.py — Cosmic Game Launcher (Textual Edition)
Layout: Left=Menu | Right-Top=Rotating Earth | Right-Bottom-Left=Preview | Right-Bottom-Right=About
"""

import math
import random
import os
import sys
import importlib

from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text
from rich.style import Style

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Earth map (land=@, ocean=.) 14 rows × 46 cols ─────────────────────────────
EARTH_MAP = [
    "....@@@@......@@@@@@@.........@@@@@@@@.......",
    "...@@@@@@@@..@@@@@@@@@@@@....@@@@@@@@@@......",
    "..@@@@@@@@@@@@@@@@@@@@@@@...@@@@@@@@@@@......",
    ".@@@@@@@@@@@@@@@@@@@@@@@@@.@@@@@@@@@@@@@.....",
    ".@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@......",
    "..@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@........",
    "....@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@.........",
    "......@@@@@@@@@@@@@@@@@@@@@@@@@@.............",
    "..........@@@@@@@@@@@@@@@@@@@................",
    ".............@@@@@@@@@@@@@@..................",
    "...............@@@@@@@@@@....................",
    "...................@@@.......................",
    "......................@......................",
    "........................@....................",
]
MAP_H = len(EARTH_MAP)
MAP_W = max(len(r) for r in EARTH_MAP)

# ── Game registry ──────────────────────────────────────────────────────────────
GAMES = [
    ("1", "PONG",    "Classic paddle game vs AI",   "pong"),
    ("2", "WORDLE",  "Guess the 5-letter word",     "wordle"),
    ("3", "SNAKE",   "Eat, grow, and survive",      "snake"),
    ("4", "PYWORDS", "Cosmic typing benchmark",     "pywords"),
    ("5", "LIFE",    "Conway's Game of Life",        "life"),
]

LOGO = [
    r"  ██████╗██╗     ██╗███╗   ███╗███████╗",
    r" ██╔════╝██║     ██║████╗ ████║██╔════╝",
    r" ██║     ██║     ██║██╔████╔██║█████╗  ",
    r" ██║     ██║     ██║██║╚██╔╝██║██╔══╝  ",
    r" ╚██████╗███████╗██║██║ ╚═╝ ██║███████╗",
    r"  ╚═════╝╚══════╝╚═╝╚═╝     ╚═╝╚══════╝",
]

TAGLINE = "✦  bringing the world to your terminal  ✦"
BYLINE  = "             by Kairva Corp."

STAR_CHARS = [".", "·", "*", "✦", "+", "°", "⁺"]

GAME_DESCRIPTIONS = {
    0: (
        "PONG",
        "The original. Move your paddle, beat the AI.\n\n"
        "  Controls:\n"
        "    W / S  — move paddle\n"
        "    Q      — quit\n\n"
        "  Survive as long as you can.",
        "green",
    ),
    1: (
        "WORDLE",
        "Six tries to find the hidden 5-letter word.\n\n"
        "  Colour hints:\n"
        "    Green  — correct position\n"
        "    Yellow — wrong position\n"
        "    Grey   — not in word\n\n"
        "  New word every session.",
        "cyan",
    ),
    2: (
        "SNAKE",
        "Classic snake. Eat, grow, don't die.\n\n"
        "  Controls:\n"
        "    Arrow keys — steer\n"
        "    Q          — quit\n\n"
        "  Walls are lethal.",
        "magenta",
    ),
    3: (
        "PYWORDS",
        "A cosmic typing speed benchmark.\n\n"
        "  Features:\n"
        "    WPM & accuracy tracking\n"
        "    Live error highlighting\n"
        "    Personal best record\n\n"
        "  Type fast. Type true.",
        "yellow",
    ),
    4: (
        "LIFE",
        "Conway's Game of Life: A cellular automaton.\n\n"
        "  Features:\n"
        "    P / Space — Pause/Resume\n"
        "    R         — Randomize\n"
        "    C         — Clear\n"
        "    Q         — Quit\n\n"
        "  Watch life bloom in the cosmos.",
        "red",
    ),
}

# ── CSS ────────────────────────────────────────────────────────────────────────
APP_CSS = """
Screen {
    layout: horizontal;
    background: #06060f;
}

/* ── Left column ── */
#left-col {
    width: 38%;
    height: 100%;
    border: solid #4b0082;
    background: #07071a;
}

/* ── Right column ── */
#right-col {
    width: 62%;
    height: 100%;
    layout: vertical;
}

/* ── Earth panel (top-right) ── */
EarthWidget {
    height: 60%;
    border: solid #4b0082;
    background: #000010;
}

/* ── Bottom row ── */
#bottom-row {
    height: 40%;
    layout: horizontal;
}

/* ── Preview panel (bottom-left of right col) ── */
#preview-panel {
    width: 55%;
    border: solid #4b0082;
    background: #07071a;
    padding: 1 2;
}

/* ── About panel (bottom-right of right col) ── */
#about-panel {
    width: 45%;
    border: solid #4b0082;
    background: #07071a;
    padding: 1 2;
}
"""

# ── Earth Widget ───────────────────────────────────────────────────────────────
class EarthWidget(Widget):
    """Rotating ASCII Earth with animated starfield background."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rot      = 0.0
        self._stars: list = []
        self._sw       = 0
        self._sh       = 0
        self._t        = 0.0

    def on_mount(self) -> None:
        self.set_interval(1 / 20, self._tick)   # 20 fps — balanced speed & load

    def _tick(self) -> None:
        self._rot = (self._rot + 0.030) % (2 * math.pi)
        self._t  += 0.05
        self.refresh()

    # Rebuild stars whenever terminal is resized
    def _ensure_stars(self, w: int, h: int) -> None:
        if self._sw == w and self._sh == h:
            return
        self._sw, self._sh = w, h
        self._stars = []
        for _ in range(int(w * h * 0.055)):
            sx   = random.randint(0, max(0, w - 1))
            sy   = random.randint(0, max(0, h - 1))
            sc   = random.choice(STAR_CHARS)
            ph   = random.uniform(0, 6.28)
            col  = random.choice(["cyan", "blue", "white", "bright_cyan"])
            self._stars.append((sx, sy, sc, ph, col))

    def render(self) -> Text:  # type: ignore[override]
        w, h = self.size.width, self.size.height
        if w == 0 or h == 0:
            return Text("")

        self._ensure_stars(w, h)

        # Grid of (char, style_str)
        gc = [[" "] * w for _ in range(h)]
        gs = [["black"] * w for _ in range(h)]

        # ── Stars with twinkle ────────────────────────────────────────────────
        t = self._t
        for sx, sy, sc, ph, col in self._stars:
            if sx >= w or sy >= h:
                continue
            brightness = (math.sin(t * 1.5 + ph) + 1) / 2
            if brightness > 0.55:
                gc[sy][sx] = sc
                gs[sy][sx] = f"bold {col}" if brightness > 0.8 else f"dim {col}"

        # ── Sphere projection ─────────────────────────────────────────────────
        R_c = min(w * 0.38, h * 0.80)
        R_r = R_c * 0.50
        cx, cy = w / 2.0, h / 2.0

        lx, ly, lz = 0.55, -0.40, 0.73
        ll = math.sqrt(lx*lx + ly*ly + lz*lz)
        lx, ly, lz = lx/ll, ly/ll, lz/ll

        rot = self._rot
        cos_r, sin_r = math.cos(rot), math.sin(rot)

        for row in range(h):
            for col in range(w):
                dx = (col - cx) / R_c
                dy = (row - cy) / R_r
                d2 = dx*dx + dy*dy
                if d2 >= 1.0:
                    continue

                dz = math.sqrt(max(0.0, 1.0 - d2))

                diffuse = max(0.0, dx * lx + dy * ly + dz * lz)
                light   = 0.10 + 0.90 * diffuse

                rx =  dx * cos_r + dz * sin_r
                rz = -dx * sin_r + dz * cos_r
                ry =  dy

                lat   = math.asin(max(-1.0, min(1.0, ry)))
                lon   = math.atan2(rx, rz)
                map_x = int((lon / (2 * math.pi) + 0.5) * MAP_W) % MAP_W
                map_y = max(0, min(MAP_H - 1, int((0.5 - lat / math.pi) * MAP_H)))

                row_str  = EARTH_MAP[map_y]
                is_land  = map_x < len(row_str) and row_str[map_x] == "@"

                if light < 0.12:
                    ch, st = "·", "bold #0a0a20" if is_land else " "
                    if not is_land:
                        ch, st = " ", "black"
                elif is_land:
                    if light > 0.80:
                        ch, st = "#", "bold bright_green"
                    elif light > 0.55:
                        ch, st = "+", "green"
                    elif light > 0.30:
                        ch, st = ".", "#306030"
                    else:
                        ch, st = "·", "#1a3010"
                else:
                    if light > 0.80:
                        ch, st = "≈", "bold bright_blue"
                    elif light > 0.55:
                        ch, st = "~", "blue"
                    elif light > 0.30:
                        ch, st = ".", "#001050"
                    else:
                        ch, st = " ", "#000820"

                gc[row][col] = ch
                gs[row][col] = st

        # ── Assemble Rich Text ────────────────────────────────────────────────
        text = Text(no_wrap=True, overflow="crop")
        for row in range(h):
            for col in range(w):
                text.append(gc[row][col], Style.parse(gs[row][col]))
            if row < h - 1:
                text.append("\n")
        return text


# ── Menu Widget ────────────────────────────────────────────────────────────────
class MenuWidget(Widget):
    """Left-panel game menu. Navigation handled at app level."""

    selected: reactive[int] = reactive(0)

    def render(self) -> Text:  # type: ignore[override]
        text = Text(no_wrap=True, overflow="crop")

        # Logo
        for i, line in enumerate(LOGO):
            col = "bold magenta" if i % 2 == 0 else "bold #6633cc"
            text.append(line + "\n", Style.parse(col))

        text.append("\n")
        text.append(TAGLINE + "\n", Style.parse("dim yellow"))
        text.append(BYLINE  + "\n\n", Style.parse("dim #888888"))

        # Separator
        sep = "─" * 40
        text.append(" " + sep + "\n\n", Style.parse("dim magenta"))

        # Column header
        text.append(f"  {'KEY':<5} {'GAME':<12} DESCRIPTION\n", Style.parse("bold cyan"))
        text.append(" " + sep + "\n", Style.parse("dim cyan"))

        for i, (key, name, desc, _) in enumerate(GAMES):
            if i == self.selected:
                line = f"  {key:<5} {name:<12} {desc}"
                text.append(line + "\n", Style.parse("bold black on cyan"))
            else:
                shade = "on #0d0d28" if i % 2 == 0 else "on #07071a"
                text.append(
                    f"  {key:<5} {name:<12} {desc}\n",
                    Style.parse(f"white {shade}")
                )

        text.append("\n")
        text.append(
            f"  Q     {'QUIT':<12} Exit the launcher\n",
            Style.parse("dim white")
        )
        text.append("\n " + sep + "\n\n", Style.parse("dim magenta"))
        text.append(
            "  ❯  ↑ ↓  navigate    ENTER  launch\n",
            Style.parse("bold cyan")
        )
        text.append(
            "  ❯  1-5  quick select    Q  quit\n",
            Style.parse("dim cyan")
        )
        return text

    def watch_selected(self, _val: int) -> None:
        self.refresh()


# ── Preview Widget ─────────────────────────────────────────────────────────────
class PreviewWidget(Static):
    """Shows info about the currently highlighted game."""
    pass


# ── About Widget ───────────────────────────────────────────────────────────────
class AboutWidget(Static):
    """About Kairva Corp + links."""

    def on_mount(self) -> None:
        t = Text()
        t.append("✦ Kairva Corp ✦\n", Style.parse("bold magenta"))
        t.append("https://github.com/Kairva-Corp\n\n", Style.parse("dim white"))
        
        t.append("─" * 22 + "\n\n", Style.parse("dim magenta"))
        
        t.append("Developers\n", Style.parse("bold cyan"))
        t.append(" → Kavin Jindal\n", Style.parse("cyan"))
        t.append("   github.com/kavin-jindal\n", Style.parse("dim cyan"))
        t.append(" → Sarthakk Anjariya\n", Style.parse("cyan"))
        t.append("   github.com/Solivagus17\n\n", Style.parse("dim cyan"))
        
        t.append("─" * 22 + "\n\n", Style.parse("dim magenta"))
        t.append("v1.0 Clime.py\n", Style.parse("dim #555577"))
        t.append("Built with Python Textual\n", Style.parse("dim #444466"))
        self.update(t)


# ── Main App ───────────────────────────────────────────────────────────────────
class CLIMEApp(App):
    CSS   = APP_CSS
    TITLE = "CLIME — Cosmic Game Launcher"

    BINDINGS = [
        ("up",    "nav_up",   "Up"),
        ("down",  "nav_down", "Down"),
        ("enter", "launch",   "Launch"),
        ("1", "pick_1"), ("2", "pick_2"), ("3", "pick_3"),
        ("4", "pick_4"), ("5", "pick_5"),
        ("q", "quit"),
        ("Q", "quit"),
    ]

    _selected: int = 0

    # ── Compose ───────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield MenuWidget(id="left-col")
            with Vertical(id="right-col"):
                yield EarthWidget()
                with Horizontal(id="bottom-row"):
                    yield PreviewWidget(id="preview-panel")
                    yield AboutWidget(id="about-panel")

    def on_mount(self) -> None:
        self._refresh_preview()

    # ── Navigation actions ────────────────────────────────────────────────────
    def action_nav_up(self) -> None:
        self._selected = (self._selected - 1) % len(GAMES)
        self._sync()

    def action_nav_down(self) -> None:
        self._selected = (self._selected + 1) % len(GAMES)
        self._sync()

    def action_pick_1(self) -> None: self._pick(0)
    def action_pick_2(self) -> None: self._pick(1)
    def action_pick_3(self) -> None: self._pick(2)
    def action_pick_4(self) -> None: self._pick(3)
    def action_pick_5(self) -> None: self._pick(4)

    def _pick(self, idx: int) -> None:
        self._selected = idx
        self._sync()

    def _sync(self) -> None:
        self.query_one(MenuWidget).selected = self._selected
        self._refresh_preview()

    # ── Launch ────────────────────────────────────────────────────────────────
    def action_launch(self) -> None:
        key, name, _desc, mod_name = GAMES[self._selected]
        self.notify(
            f"Launching [bold]{name}[/bold] …  (ensure games/{mod_name}.py is present)",
            title="CLIME",
            severity="information",
        )
        try:
            # Look in the 'games' sub-directory
            games_path = os.path.join(SCRIPT_DIR, "games")
            if games_path not in sys.path:
                sys.path.insert(0, games_path)

            if mod_name in sys.modules:
                mod = importlib.reload(sys.modules[mod_name])
            else:
                mod = __import__(mod_name)
            
            # Suspend Textual, run the curses game, resume
            with self.suspend():
                if hasattr(mod, "play"):
                    mod.play()
                elif hasattr(mod, "main"):
                    mod.main()
        except ImportError:
            self.notify(
                f"[red]games/{mod_name}.py not found.[/red]",
                title="Module missing",
                severity="error",
            )
        except Exception as exc:
            self.notify(str(exc), title="Error", severity="error")

    # ── Preview update ────────────────────────────────────────────────────────
    def _refresh_preview(self) -> None:
        idx  = self._selected
        name, body, accent = GAME_DESCRIPTIONS[idx]

        t = Text(no_wrap=True, overflow="crop")
        t.append("  Selected\n\n", Style.parse("dim cyan"))
        t.append(f"  {name}\n", Style.parse(f"bold {accent}"))
        t.append("  " + "─" * 22 + "\n\n", Style.parse(f"dim {accent}"))

        for line in body.split("\n"):
            t.append("  " + line + "\n", Style.parse("white"))

        t.append("\n")
        t.append("  ╔══ ENTER to launch ══╗\n", Style.parse(f"bold {accent}"))
        t.append(f"  ╚{'═'*20}╝\n", Style.parse(f"dim {accent}"))

        self.query_one("#preview-panel", PreviewWidget).update(t)


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    CLIMEApp().run()
