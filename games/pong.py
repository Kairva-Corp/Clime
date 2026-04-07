#!/usr/bin/env python3
"""
PONG.py — Terminal Pong
Classic paddle game vs AI. Dark cosmic theme matching CLIME.
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
CP_BG       = 1
CP_BORDER   = 2
CP_HEADER   = 3
CP_PADDLE1  = 4
CP_PADDLE2  = 5
CP_BALL     = 6
CP_RESULT   = 7
CP_SPECIAL  = 8
CP_TAGLINE  = 9
CP_ERROR    = 10
CP_CENTER   = 11
CP_STAR     = 12
CP_FIREFLY  = 13

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_BG,      curses.COLOR_WHITE,   -1)
    curses.init_pair(CP_BORDER,  curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_HEADER,  curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_PADDLE1, curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(CP_PADDLE2, curses.COLOR_BLACK,   curses.COLOR_MAGENTA)
    curses.init_pair(CP_BALL,    curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_RESULT,  curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_SPECIAL, curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_TAGLINE, curses.COLOR_WHITE,   -1)
    curses.init_pair(CP_ERROR,   curses.COLOR_RED,     -1)
    curses.init_pair(CP_CENTER,  curses.COLOR_MAGENTA, -1)
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
FIELD_W = 50
FIELD_H = 18
PADDLE_H = 4
AI_REACTION = 0.55

class Ball:
    def __init__(self):
        self.x = FIELD_W // 2
        self.y = FIELD_H // 2
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])
    def move(self):
        self.x += self.dx
        self.y += self.dy
    def bounce_y(self): self.dy *= -1
    def bounce_x(self): self.dx *= -1

class Game:
    def __init__(self):
        self.paddle1_y = FIELD_H // 2 - PADDLE_H // 2
        self.paddle2_y = FIELD_H // 2 - PADDLE_H // 2
        self.ball = Ball()
        self.score1 = 0
        self.score2 = 0
        self.game_over = False
        self.tick = 0
        self.running = True

    def restart(self):
        self.paddle1_y = FIELD_H // 2 - PADDLE_H // 2
        self.paddle2_y = FIELD_H // 2 - PADDLE_H // 2
        self.ball = Ball()
        self.game_over = False

    def move_ball(self):
        self.ball.move()
        if self.ball.y <= 0 or self.ball.y >= FIELD_H - 1:
            self.ball.bounce_y()
        if self.ball.x <= 1:
            if self.paddle1_y <= self.ball.y < self.paddle1_y + PADDLE_H:
                self.ball.bounce_x()
                self.ball.x = 2
            else:
                self.score2 += 1
                self.game_over = True
        if self.ball.x >= FIELD_W - 2:
            if self.paddle2_y <= self.ball.y < self.paddle2_y + PADDLE_H:
                self.ball.bounce_x()
                self.ball.x = FIELD_W - 3
            else:
                self.score1 += 1
                self.game_over = True

    def move_ai(self):
        # Only react some of the time
        if random.random() > AI_REACTION:
            return
        # Only track when ball is heading toward AI
        if self.ball.dx > 0:
            target = self.ball.y - PADDLE_H // 2
            if self.paddle2_y < target:
                self.paddle2_y = min(self.paddle2_y + 1, FIELD_H - PADDLE_H)
            elif self.paddle2_y > target:
                self.paddle2_y = max(self.paddle2_y - 1, 0)

# ── Render ────────────────────────────────────────────────────────────────────
def render(win, sr, sc, game, w, h, stars, fireflies, t):
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
    title = " ✦ PONG ✦ "
    safe_addstr(win, 1, max(1, (w - len(title)) // 2), title,
                curses.color_pair(CP_HEADER) | curses.A_BOLD)
    sep = "─" * min(w - 4, 50)
    safe_addstr(win, 2, max(1, (w - len(sep)) // 2), sep,
                curses.color_pair(CP_BORDER) | curses.A_DIM)

    # Field border
    for y in range(FIELD_H + 2):
        safe_addch(win, sr + y, sc, "│", curses.color_pair(CP_BORDER) | curses.A_BOLD)
        safe_addch(win, sr + y, sc + FIELD_W + 1, "│", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr, sc, "╭", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr, sc + FIELD_W + 1, "╮", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr + FIELD_H + 1, sc, "╰", curses.color_pair(CP_BORDER) | curses.A_BOLD)
    safe_addch(win, sr + FIELD_H + 1, sc + FIELD_W + 1, "╯", curses.color_pair(CP_BORDER) | curses.A_BOLD)

    # Center line
    for y in range(1, FIELD_H + 1):
        safe_addch(win, sr + y, sc + FIELD_W // 2 + 1, "│", curses.color_pair(CP_CENTER) | curses.A_DIM)

    # Paddles
    for i in range(PADDLE_H):
        py = game.paddle1_y + i
        if 0 <= py < FIELD_H:
            safe_addch(win, sr + py + 1, sc + 1, "█", curses.color_pair(CP_PADDLE1) | curses.A_BOLD)
    for i in range(PADDLE_H):
        py = game.paddle2_y + i
        if 0 <= py < FIELD_H:
            safe_addch(win, sr + py + 1, sc + FIELD_W, "█", curses.color_pair(CP_PADDLE2) | curses.A_BOLD)

    # Ball
    bx = max(0, min(FIELD_W - 1, game.ball.x))
    by = max(0, min(FIELD_H - 1, game.ball.y))
    safe_addstr(win, sr + by + 1, sc + bx + 1, "●", curses.color_pair(CP_BALL) | curses.A_BOLD)

    # Score
    score_text = f"  YOU {game.score1}  :  {game.score2} AI  "
    score_row = sr + FIELD_H + 3
    sc_color = CP_RESULT if game.score1 > game.score2 else (CP_SPECIAL if game.score2 > game.score1 else CP_HEADER)
    safe_addstr(win, score_row, max(1, (w - len(score_text)) // 2), score_text,
                curses.color_pair(sc_color) | curses.A_BOLD)

    # Game over overlay
    if game.game_over:
        o = sr + FIELD_H // 2 - 2
        for i in range(6):
            for x in range(w):
                safe_addch(win, o + i, x, " ", curses.A_NORMAL)
        safe_addstr(win, o, max(1, (w - 13) // 2), "  GAME OVER  ",
                    curses.color_pair(CP_ERROR) | curses.A_BOLD)
        if game.score1 > game.score2:
            wt, wc = "  YOU WIN!  ", CP_RESULT
        elif game.score2 > game.score1:
            wt, wc = "  AI WINS!  ", CP_SPECIAL
        else:
            wt, wc = "  IT'S A TIE!  ", CP_HEADER
        safe_addstr(win, o + 2, max(1, (w - len(wt)) // 2), wt,
                    curses.color_pair(wc) | curses.A_BOLD)
        res = f"YOU {game.score1}  :  {game.score2} AI"
        safe_addstr(win, o + 3, max(1, (w - len(res)) // 2), res,
                    curses.color_pair(CP_TAGLINE) | curses.A_BOLD)
        safe_addstr(win, o + 5, max(1, (w - 22) // 2), "Press SPACE to restart",
                    curses.color_pair(CP_TAGLINE) | curses.A_DIM)

    # Footer
    footer = "  [W/S] move  [SPACE] restart  [Q] quit  "
    safe_addstr(win, h - 2, max(1, (w - len(footer)) // 2), footer,
                curses.color_pair(CP_TAGLINE) | curses.A_DIM)

# ── Main ──────────────────────────────────────────────────────────────────────
def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)

    h, w = stdscr.getmaxyx()
    game = Game()
    fw = FIELD_W + 2
    fh = FIELD_H + 2
    sc = (w - fw) // 2
    sr = max(4, (h - fh - 6) // 2)

    stars = StarField(h, w)
    fireflies = [Firefly(h, w) for _ in range(6)]
    t_start = time.time()
    prev_frame = t_start

    while game.running:
        now = time.time()
        t = now - t_start
        dt = now - prev_frame
        prev_frame = now

        # Update fireflies
        for ff in fireflies:
            ff.update(dt)

        render(stdscr, sr, sc, game, w, h, stars, fireflies, t)

        key = stdscr.getch()
        if key != -1:
            if key in (ord("q"), ord("Q"), 27):
                break
            if game.game_over:
                if key == ord(" "):
                    game.restart()
            else:
                if key in (ord("w"), ord("W"), curses.KEY_UP):
                    game.paddle1_y = max(0, game.paddle1_y - 1)
                elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
                    game.paddle1_y = min(FIELD_H - PADDLE_H, game.paddle1_y + 1)

        if not game.game_over:
            game.tick += 1
            if game.tick % 2 == 0:
                game.move_ball()
            game.move_ai()

        stdscr.refresh()
        if key == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()
            sc = (w - fw) // 2
            sr = max(4, (h - fh - 6) // 2)
            stars.rebuild(h, w)
            fireflies = [Firefly(h, w) for _ in range(6)]
        time.sleep(0.03)

def play():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    play()
