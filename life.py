#!/usr/bin/env python3
"""
LIFE.py — Conway's Game of Life
Evolutionary simulation with a dark cosmic theme matching CLIME.
"""

import time
import curses
import random
import math

# ── Safe Draw Helpers ─────────────────────────────────────────────────────────
def safe_addstr(win, y, x, text, attr=0):
    try:
        max_y, max_x = win.getmaxyx()
        if y < 0 or y >= max_y or x < 0:
            return
        available = max_x - x
        if available <= 0:
            return
        win.addstr(y, x, text[:available], attr)
    except curses.error:
        pass

def safe_addch(win, y, x, ch, attr=0):
    try:
        max_y, max_x = win.getmaxyx()
        if y < 0 or y >= max_y or x < 0 or x >= max_x:
            return
        win.addch(y, x, ch, attr)
    except curses.error:
        pass

# ── Color Pairs ───────────────────────────────────────────────────────────────
CP_BG      = 1
CP_BORDER  = 2
CP_HEADER  = 3
CP_CELL    = 4
CP_RESULT  = 8
CP_SPECIAL = 9
CP_TAGLINE = 10
CP_ERROR   = 11
CP_STAR    = 12
CP_FIREFLY = 13

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_BG,      curses.COLOR_WHITE,   -1)
    curses.init_pair(CP_BORDER,  curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_HEADER,  curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_CELL,    curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_RESULT,  curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_SPECIAL, curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_TAGLINE, curses.COLOR_WHITE,   -1)
    curses.init_pair(CP_ERROR,   curses.COLOR_RED,     -1)
    curses.init_pair(CP_STAR,    curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_FIREFLY, curses.COLOR_YELLOW,  -1)

# ── Starfield ─────────────────────────────────────────────────────────────────
STAR_CHARS = [".", "·", "*", "✦", "+", "°", "⁺"]

class StarField:
    def __init__(self, h, w, density=0.025):
        self.stars = []
        self._build(h, w, density)

    def _build(self, h, w, density):
        self.stars = []
        count = int(h * w * density)
        for _ in range(count):
            r = random.randint(0, max(0, h - 1))
            c = random.randint(0, max(0, w - 1))
            ch = random.choice(STAR_CHARS)
            phase = random.random()
            self.stars.append((r, c, ch, phase))

    def rebuild(self, h, w):
        self._build(h, w, 0.025)

    def draw(self, win, t):
        for (r, c, ch, phase) in self.stars:
            intensity = (math.sin(t * 0.7 + phase * 6.28) + 1) / 2
            if intensity > 0.6:
                attr = curses.color_pair(CP_STAR) | curses.A_BOLD
            elif intensity > 0.3:
                attr = curses.color_pair(CP_STAR)
            else:
                attr = curses.color_pair(CP_STAR) | curses.A_DIM
            safe_addch(win, r, c, ch, attr)

# ── Fireflies ─────────────────────────────────────────────────────────────────
FIREFLY_CHAR = "✦"

class Firefly:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.reset()

    def reset(self):
        self.y = random.uniform(1, max(2, self.h - 2))
        self.x = random.uniform(1, max(2, self.w - 2))
        self.vy = random.uniform(-0.3, 0.3)
        self.vx = random.uniform(-0.5, 0.5)
        self.phase = random.uniform(0, 6.28)
        self.speed = random.uniform(0.5, 2.0)

    def update(self, dt):
        self.y += self.vy * dt * self.speed
        self.x += self.vx * dt * self.speed
        self.vy += random.uniform(-0.05, 0.05)
        self.vx += random.uniform(-0.05, 0.05)
        self.vy = max(-0.8, min(0.8, self.vy))
        self.vx = max(-1.0, min(1.0, self.vx))
        if self.y < 1:
            self.y = 1; self.vy = abs(self.vy)
        if self.y >= self.h - 1:
            self.y = self.h - 2; self.vy = -abs(self.vy)
        if self.x < 1:
            self.x = 1; self.vx = abs(self.vx)
        if self.x >= self.w - 1:
            self.x = self.w - 2; self.vx = -abs(self.vx)

    def draw(self, win, t):
        glow = (math.sin(t * 3.0 + self.phase) + 1) / 2
        if glow > 0.5:
            attr = curses.color_pair(CP_FIREFLY) | curses.A_BOLD
        else:
            attr = curses.color_pair(CP_FIREFLY) | curses.A_DIM
        safe_addch(win, int(self.y), int(self.x), FIREFLY_CHAR, attr)

# ── Cosmic Border ─────────────────────────────────────────────────────────────
def draw_cosmic_border(win, t):
    h, w = win.getmaxyx()
    phase = t * 0.5
    for col in range(w):
        glow = (math.sin(col * 0.15 + phase) + 1) / 2
        if glow > 0.6:
            attr = curses.color_pair(CP_BORDER) | curses.A_BOLD
        else:
            attr = curses.color_pair(CP_BORDER) | curses.A_DIM
        safe_addch(win, 0, col, "═", attr)
        safe_addch(win, h - 1, col, "═", attr)
    for row in range(h):
        glow = (math.sin(row * 0.2 + phase + 1.0) + 1) / 2
        if glow > 0.6:
            attr = curses.color_pair(CP_BORDER) | curses.A_BOLD
        else:
            attr = curses.color_pair(CP_BORDER) | curses.A_DIM
        safe_addch(win, row, 0, "║", attr)
        safe_addch(win, row, w - 1, "║", attr)
    c_attr = curses.color_pair(CP_BORDER) | curses.A_BOLD
    safe_addch(win, 0,     0,     "╔", c_attr)
    safe_addch(win, 0,     w - 1, "╗", c_attr)
    safe_addch(win, h - 1, 0,     "╚", c_attr)
    safe_addch(win, h - 1, w - 1, "╝", c_attr)

# ── Game Module ───────────────────────────────────────────────────────────────
class LifeGame:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.grid = [[0 for _ in range(w)] for _ in range(h)]
        self.paused = False
        self.randomize()

    def randomize(self):
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = 1 if random.random() < 0.12 else 0

    def clear(self):
        self.grid = [[0 for _ in range(self.w)] for _ in range(self.h)]

    def update(self):
        if self.paused:
            return
        new_grid = [[0 for _ in range(self.w)] for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                count = self._count_neighbours(y, x)
                if self.grid[y][x] == 1:
                    if count in (2, 3):
                        new_grid[y][x] = 1
                else:
                    if count == 3:
                        new_grid[y][x] = 1
        self.grid = new_grid

    def _count_neighbours(self, y, x):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.h and 0 <= nx < self.w:
                    count += self.grid[ny][nx]
        return count

def render(win, sr, sc, game, w, h, stars, fireflies, t):
    win.erase()

    # Starfield
    for (r, c, ch, phase) in stars.stars:
        intensity = (math.sin(t * 0.4 + phase * 6.28) + 1) / 2
        if intensity > 0.7:
            safe_addch(win, r, c, ch, curses.color_pair(CP_STAR) | curses.A_DIM)

    # Fireflies
    for ff in fireflies:
        ff.draw(win, t)

    # Cosmic Border
    draw_cosmic_border(win, t)

    # Header
    title = " ✦ CONWAY'S GAME OF LIFE ✦ "
    safe_addstr(win, 1, max(1, (w - len(title)) // 2), title,
                curses.color_pair(CP_HEADER) | curses.A_BOLD)

    # Grid logic
    for y in range(game.h):
        for x in range(game.w):
            if game.grid[y][x] == 1:
                safe_addch(win, sr + y + 1, sc + x + 1, "█",
                           curses.color_pair(CP_CELL) | curses.A_BOLD)

    # Status
    status = " PAUSED " if game.paused else " RUNNING "
    safe_addstr(win, sr + game.h + 2, max(1, (w - 10) // 2), status,
                curses.color_pair(CP_SPECIAL) | curses.A_BOLD)

    # Controls
    controls = " [P/Space] Pause  [R] Randomize  [C] Clear  [Q] Quit "
    safe_addstr(win, h - 2, max(1, (w - len(controls)) // 2), controls,
                curses.color_pair(CP_TAGLINE) | curses.A_DIM)

def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)

    h, w = stdscr.getmaxyx()
    # Expand to full window (subtracting space for header, footer, and borders)
    gh = max(1, h - 8)
    gw = max(1, w - 2)
    game = LifeGame(gh, gw)
    
    # Position grid inside the cosmic borders
    sc = 0
    sr = 3 

    stars = StarField(h, w)
    fireflies = [Firefly(h, w) for _ in range(6)]
    t_start = time.time()
    prev_frame = t_start

    while True:
        now = time.time()
        t = now - t_start
        dt = now - prev_frame
        prev_frame = now

        for ff in fireflies:
            ff.update(dt)

        game.update()
        render(stdscr, sr, sc, game, w, h, stars, fireflies, t)
        
        key = stdscr.getch()
        if key != -1:
            if key in (ord("q"), ord("Q"), 27):
                break
            elif key in (ord("p"), ord("P"), ord(" ")):
                game.paused = not game.paused
            elif key in (ord("r"), ord("R")):
                game.randomize()
            elif key in (ord("c"), ord("C")):
                game.clear()
            elif key == curses.KEY_RESIZE:
                h, w = stdscr.getmaxyx()
                gh = max(1, h - 8)
                gw = max(1, w - 2)
                # Create a new game instance with the new size
                # Note: this resets the current simulation state
                game = LifeGame(gh, gw)
                stars.rebuild(h, w)
                fireflies = [Firefly(h, w) for _ in range(6)]
                sc = 0
                sr = 3 

        stdscr.refresh()
        time.sleep(0.1)

def play():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    play()
