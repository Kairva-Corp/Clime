#!/usr/bin/env python3
"""
SNAKE.py — Terminal Snake
Eat, grow, survive. Dark cosmic theme matching CLIME.
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
        win.addstr(y, x, text[:max_x - x], attr)
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
CP_SNAKE_H = 4
CP_SNAKE_B = 5
CP_SNAKE_T = 6
CP_FOOD    = 7
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
    curses.init_pair(CP_SNAKE_H, curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(CP_SNAKE_B, curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(CP_SNAKE_T, curses.COLOR_BLACK,   curses.COLOR_MAGENTA)
    curses.init_pair(CP_FOOD,    curses.COLOR_BLACK,   curses.COLOR_YELLOW)
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

# ── Game Constants ────────────────────────────────────────────────────────────
FW = 30
FH = 20
SPD = 0.12
INC = 0.002

class Snake:
    def __init__(self):
        self.body = [(FW // 2, FH // 2)]
        self.dir = (1, 0)
        self.ndir = (1, 0)
        self.food = self.spawn()
        self.score = 0
        self.high = 0
        self.over = False
        self.run = True
        self.spd = SPD

    def spawn(self):
        while True:
            x = random.randint(0, FW - 1)
            y = random.randint(0, FH - 1)
            if (x, y) not in self.body:
                return (x, y)

    def steer(self, dx, dy):
        if (dx, dy) != (-self.dir[0], -self.dir[1]):
            self.ndir = (dx, dy)

    def move(self):
        if self.over:
            return
        self.dir = self.ndir
        nh = (self.body[0][0] + self.dir[0], self.body[0][1] + self.dir[1])
        if nh[0] < 0 or nh[0] >= FW or nh[1] < 0 or nh[1] >= FH or nh in self.body:
            self.over = True
            if self.score > self.high:
                self.high = self.score
            return
        self.body.insert(0, nh)
        if nh == self.food:
            self.score += 10
            self.food = self.spawn()
            self.spd = max(0.04, self.spd - INC)
        else:
            self.body.pop()

# ── Render ────────────────────────────────────────────────────────────────────
def render(win, sr, sc, snake, w, h, stars, fireflies, t):
    win.erase()

    # Starfield (muted during gameplay)
    for (r, c, ch, phase) in stars.stars:
        intensity = (math.sin(t * 0.4 + phase * 6.28) + 1) / 2
        if intensity > 0.7:
            safe_addch(win, r, c, ch, curses.color_pair(CP_STAR) | curses.A_DIM)

    # Fireflies
    for ff in fireflies:
        ff.draw(win, t)

    # Cosmic border
    draw_cosmic_border(win, t)

    # Header
    safe_addstr(win, 1, max(1, (w - 11) // 2), " ✦ SNAKE ✦ ",
                curses.color_pair(CP_HEADER) | curses.A_BOLD)
    safe_addstr(win, 2, max(1, (w - min(w - 4, 50)) // 2), "─" * min(w - 4, 50),
                curses.color_pair(CP_BORDER) | curses.A_DIM)

    # Field border
    for y in range(FH + 2):
        safe_addch(win, sr + y, sc, "│", curses.color_pair(CP_BORDER) | curses.A_BOLD)
        safe_addch(win, sr + y, sc + FW + 1, "│", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr, sc, "╭", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr, sc + FW + 1, "╮", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr + FH + 1, sc, "╰", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr + FH + 1, sc + FW + 1, "╯", curses.color_pair(CP_BORDER) | curses.A_BOLD)

    # Food
    fx, fy = snake.food
    safe_addch(win, sr + fy + 1, sc + fx + 1, "●", curses.color_pair(CP_FOOD) | curses.A_BOLD)

    # Snake body
    for i, (sx, sy) in enumerate(snake.body):
        if i == 0:
            attr = curses.color_pair(CP_SNAKE_H) | curses.A_BOLD
            ch = "█"
        elif i == len(snake.body) - 1:
            attr = curses.color_pair(CP_SNAKE_T) | curses.A_BOLD
            ch = "▓"
        else:
            attr = curses.color_pair(CP_SNAKE_B) | curses.A_BOLD
            ch = "█"
        safe_addch(win, sr + sy + 1, sc + sx + 1, ch, attr)

    # Score
    st = f"Score: {snake.score}    Length: {len(snake.body)}    High: {snake.high}"
    safe_addstr(win, sr + FH + 3, max(1, (w - len(st)) // 2), st,
                curses.color_pair(CP_HEADER) | curses.A_BOLD)

    # Game over overlay
    if snake.over:
        o = sr + FH // 2 - 2
        for i in range(6):
            for x in range(w):
                safe_addch(win, o + i, x, " ", curses.A_NORMAL)
        safe_addstr(win, o, max(1, (w - 13) // 2), "  GAME OVER  ",
                    curses.color_pair(CP_ERROR) | curses.A_BOLD)
        safe_addstr(win, o + 2, max(1, (w - 14) // 2), f"Score: {snake.score}",
                    curses.color_pair(CP_TAGLINE) | curses.A_BOLD)
        safe_addstr(win, o + 3, max(1, (w - 20) // 2), f"High Score: {snake.high}",
                    curses.color_pair(CP_SPECIAL) | curses.A_BOLD)
        safe_addstr(win, o + 5, max(1, (w - 22) // 2), "Press SPACE to restart",
                    curses.color_pair(CP_TAGLINE) | curses.A_DIM)

    # Footer
    footer = "  [WASD/Arrows] move  [SPACE] restart  [Q] quit  "
    safe_addstr(win, h - 2, max(1, (w - len(footer)) // 2), footer,
                curses.color_pair(CP_TAGLINE) | curses.A_DIM)

# ── Main ──────────────────────────────────────────────────────────────────────
def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)

    h, w = stdscr.getmaxyx()
    snake = Snake()
    fw, fh = FW + 2, FH + 2
    sc = (w - fw) // 2
    sr = max(4, (h - fh - 6) // 2)

    stars = StarField(h, w)
    fireflies = [Firefly(h, w) for _ in range(6)]
    t_start = time.time()
    prev_frame = t_start

    while snake.run:
        now = time.time()
        t = now - t_start
        dt = now - prev_frame
        prev_frame = now

        # Update fireflies
        for ff in fireflies:
            ff.update(dt)

        render(stdscr, sr, sc, snake, w, h, stars, fireflies, t)

        key = stdscr.getch()
        if key != -1:
            if key in (ord("q"), ord("Q"), 27):
                break
            if snake.over:
                if key == ord(" "):
                    oh = snake.high
                    snake = Snake()
                    snake.high = oh
                continue
            if key in (ord("w"), ord("W"), curses.KEY_UP):
                snake.steer(0, -1)
            elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
                snake.steer(0, 1)
            elif key in (ord("a"), ord("A"), curses.KEY_LEFT):
                snake.steer(-1, 0)
            elif key in (ord("d"), ord("D"), curses.KEY_RIGHT):
                snake.steer(1, 0)

        snake.move()
        stdscr.refresh()

        if key == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()
            sc = (w - fw) // 2
            sr = max(4, (h - fh - 6) // 2)
            stars.rebuild(h, w)
            fireflies = [Firefly(h, w) for _ in range(6)]

        time.sleep(snake.spd)

def play():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    play()
