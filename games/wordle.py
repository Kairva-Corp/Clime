#!/usr/bin/env python3
"""
WORDLE.py — Terminal Wordle
Guess the 5-letter word. Dark cosmic theme matching CLIME.
"""

import time
import curses
import random
import os
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

# ── Color Pair IDs ────────────────────────────────────────────────────────────
CP_CORRECT   = 1
CP_ERROR     = 2
CP_UNTYPED   = 3
CP_HEADER    = 4
CP_LOGO1     = 5
CP_TAGLINE   = 6
CP_RESULT_HI = 7
CP_BORDER    = 8
CP_SPECIAL   = 9
CP_TILE_COR  = 10
CP_TILE_PRE  = 11
CP_TILE_ABS  = 12
CP_TILE_EMP  = 13
CP_KEY_COR   = 14
CP_KEY_PRE   = 15
CP_KEY_ABS   = 16
CP_KEY_DEF   = 17
CP_STAR      = 18
CP_FIREFLY   = 19

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_CORRECT,   curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_ERROR,     curses.COLOR_RED,     -1)
    curses.init_pair(CP_UNTYPED,   curses.COLOR_WHITE,   -1)
    curses.init_pair(CP_HEADER,    curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_LOGO1,     curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_TAGLINE,   curses.COLOR_WHITE,   -1)
    curses.init_pair(CP_RESULT_HI, curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_BORDER,    curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_SPECIAL,   curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_TILE_COR,  curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(CP_TILE_PRE,  curses.COLOR_BLACK,   curses.COLOR_YELLOW)
    curses.init_pair(CP_TILE_ABS,  curses.COLOR_WHITE,   curses.COLOR_RED)
    curses.init_pair(CP_TILE_EMP,  curses.COLOR_CYAN,    curses.COLOR_BLUE)
    curses.init_pair(CP_KEY_COR,   curses.COLOR_BLACK,   curses.COLOR_GREEN)
    curses.init_pair(CP_KEY_PRE,   curses.COLOR_BLACK,   curses.COLOR_YELLOW)
    curses.init_pair(CP_KEY_ABS,   curses.COLOR_WHITE,   curses.COLOR_RED)
    curses.init_pair(CP_KEY_DEF,   curses.COLOR_CYAN,    curses.COLOR_BLUE)
    curses.init_pair(CP_STAR,      curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_FIREFLY,   curses.COLOR_YELLOW,  -1)

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

# ── Load Words ────────────────────────────────────────────────────────────────
def load_words():
    words = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to root, then into assets/
    words_path = os.path.join(script_dir, "..", "assets", "words.txt")
    try:
        with open(words_path, "r") as f:
            for line in f:
                word = line.strip().upper()
                if len(word) == 5 and word.isalpha():
                    words.append(word)
    except FileNotFoundError:
        words = ["ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT",
                 "ADOPT", "ADULT", "AFTER", "AGAIN"]
    return words

WORD_LIST = load_words()
WORD_LEN = 5
MAX_GUESSES = 6

# ── Game Logic ────────────────────────────────────────────────────────────────
def get_feedback(guess, answer):
    feedback = ["absent"] * WORD_LEN
    answer_chars = list(answer)
    guess_chars = list(guess)
    for i in range(WORD_LEN):
        if guess_chars[i] == answer_chars[i]:
            feedback[i] = "correct"
            answer_chars[i] = None
            guess_chars[i] = None
    for i in range(WORD_LEN):
        if guess_chars[i] is None:
            continue
        if guess_chars[i] in answer_chars:
            feedback[i] = "present"
            idx = answer_chars.index(guess_chars[i])
            answer_chars[idx] = None
    return feedback

# ── Drawing Helpers ───────────────────────────────────────────────────────────
def draw_tile(win, row, col, letter, state):
    if state == "correct":
        attr = curses.color_pair(CP_TILE_COR) | curses.A_BOLD
    elif state == "present":
        attr = curses.color_pair(CP_TILE_PRE) | curses.A_BOLD
    elif state == "absent":
        attr = curses.color_pair(CP_TILE_ABS)
    elif state == "typing":
        attr = curses.color_pair(CP_TILE_EMP) | curses.A_BOLD | curses.A_UNDERLINE
    else:
        attr = curses.color_pair(CP_TILE_EMP)
    safe_addstr(win, row, col, f" {letter} ", attr)

def draw_board(win, start_row, start_col, guesses, feedbacks, current_input):
    for row in range(MAX_GUESSES):
        for col in range(WORD_LEN):
            if row < len(guesses):
                letter = guesses[row][col]
                state = feedbacks[row][col]
            elif row == len(guesses) and col < len(current_input):
                letter = current_input[col]
                state = "typing"
            else:
                letter = " "
                state = "empty"
            tile_col = start_col + col * 4
            draw_tile(win, start_row + row, tile_col, letter, state)

def draw_keyboard(win, start_row, start_col, guesses, feedbacks):
    rows = [
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM"),
    ]
    letter_states = {}
    for g, f in zip(guesses, feedbacks):
        for letter, state in zip(g, f):
            prev = letter_states.get(letter)
            if prev == "correct":
                continue
            if state == "correct":
                letter_states[letter] = "correct"
            elif state == "present" and prev != "correct":
                letter_states[letter] = "present"
            elif state == "absent" and prev not in ("correct", "present"):
                letter_states[letter] = "absent"

    for row_idx, row in enumerate(rows):
        row_start = start_row + row_idx
        offset = row_idx * 2
        for col_idx, letter in enumerate(row):
            col = start_col + col_idx * 4 + offset
            state = letter_states.get(letter, "unused")
            if state == "correct":
                attr = curses.color_pair(CP_KEY_COR) | curses.A_BOLD
            elif state == "present":
                attr = curses.color_pair(CP_KEY_PRE) | curses.A_BOLD
            elif state == "absent":
                attr = curses.color_pair(CP_KEY_ABS) | curses.A_DIM
            else:
                attr = curses.color_pair(CP_KEY_DEF) | curses.A_BOLD
            safe_addstr(win, row_start, col, f" {letter} ", attr)

def draw_game_over(win, start_row, cols, won, answer, guesses_count):
    for i in range(6):
        for x in range(cols):
            safe_addch(win, start_row + i, x, " ", curses.A_NORMAL)
    if won:
        title = "  YOU WIN!  "
        title_color = CP_RESULT_HI
    else:
        title = "  GAME OVER  "
        title_color = CP_ERROR
    safe_addstr(win, start_row, max(1, (cols - len(title)) // 2), title,
                curses.color_pair(title_color) | curses.A_BOLD)
    answer_text = f"The word was {answer}"
    safe_addstr(win, start_row + 2, max(1, (cols - len(answer_text)) // 2), answer_text,
                curses.color_pair(CP_UNTYPED) | curses.A_BOLD)
    score_text = f"Guessed in {guesses_count} attempts" if won else f"Failed after {MAX_GUESSES} attempts"
    safe_addstr(win, start_row + 3, max(1, (cols - len(score_text)) // 2), score_text,
                curses.color_pair(CP_TAGLINE) | curses.A_DIM)
    prompt = "Press SPACE to play again"
    safe_addstr(win, start_row + 5, max(1, (cols - len(prompt)) // 2), prompt,
                curses.color_pair(CP_TAGLINE) | curses.A_DIM)

# ── Main ──────────────────────────────────────────────────────────────────────
def main(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)

    h, w = stdscr.getmaxyx()

    answer = random.choice(WORD_LIST)
    guesses = []
    feedbacks = []
    current_input = ""
    game_over = False
    won = False
    running = True
    error_msg = ""
    error_timer = 0

    board_start_col = max(2, (w - WORD_LEN * 4) // 2)
    board_start_row = 4
    keyboard_start_row = board_start_row + MAX_GUESSES + 2
    keyboard_start_col = max(2, (w - 10 * 4) // 2)

    stars = StarField(h, w)
    fireflies = [Firefly(h, w) for _ in range(6)]
    t_start = time.time()
    prev_frame = t_start

    while running:
        now = time.time()
        t = now - t_start
        dt = now - prev_frame
        prev_frame = now

        # Update fireflies
        for ff in fireflies:
            ff.update(dt)

        stdscr.erase()

        # Starfield (muted)
        for (r, c, ch, phase) in stars.stars:
            intensity = (math.sin(t * 0.4 + phase * 6.28) + 1) / 2
            if intensity > 0.7:
                safe_addch(stdscr, r, c, ch, curses.color_pair(CP_STAR) | curses.A_DIM)

        # Fireflies
        for ff in fireflies:
            ff.draw(stdscr, t)

        # Cosmic border
        draw_cosmic_border(stdscr, t)

        # Header
        header_text = " ✦ WORDLE ✦ "
        safe_addstr(stdscr, 1, max(1, (w - len(header_text)) // 2), header_text,
                    curses.color_pair(CP_LOGO1) | curses.A_BOLD)
        sep = "─" * min(w - 4, 50)
        safe_addstr(stdscr, 2, max(1, (w - len(sep)) // 2), sep,
                    curses.color_pair(CP_BORDER) | curses.A_DIM)

        draw_board(stdscr, board_start_row, board_start_col, guesses, feedbacks, current_input)
        draw_keyboard(stdscr, keyboard_start_row, keyboard_start_col, guesses, feedbacks)

        attempt_text = f"Attempt {len(guesses) + 1}/{MAX_GUESSES}"
        attempt_row = keyboard_start_row + 4
        safe_addstr(stdscr, attempt_row, max(1, (w - len(attempt_text)) // 2), attempt_text,
                    curses.color_pair(CP_TAGLINE) | curses.A_DIM)

        if error_msg and error_timer > 0:
            error_timer -= 1
            safe_addstr(stdscr, attempt_row - 1, max(1, (w - len(error_msg)) // 2), error_msg,
                        curses.color_pair(CP_ERROR) | curses.A_BOLD)

        if game_over:
            overlay_row = board_start_row - 1
            draw_game_over(stdscr, overlay_row, w, won, answer, len(guesses))

        footer = "  [A-Z] type  [ENTER] guess  [BACKSPACE] delete  [Q] quit  "
        safe_addstr(stdscr, h - 2, max(1, (w - len(footer)) // 2), footer,
                    curses.color_pair(CP_TAGLINE) | curses.A_DIM)

        stdscr.refresh()

        key = stdscr.getch()
        if key != -1:
            if key in (ord("q"), ord("Q"), 27):
                running = False
                break
            if game_over:
                if key == ord(" "):
                    answer = random.choice(WORD_LIST)
                    guesses = []
                    feedbacks = []
                    current_input = ""
                    game_over = False
                    won = False
                    error_msg = ""
                    error_timer = 0
                continue
            if key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                if len(current_input) == WORD_LEN:
                    guess = current_input.upper()
                    if guess in [g for g in guesses]:
                        error_msg = "Already guessed!"
                        error_timer = 60
                    elif guess not in WORD_LIST:
                        error_msg = "Not in word list!"
                        error_timer = 60
                    else:
                        feedback = get_feedback(guess, answer)
                        guesses.append(guess)
                        feedbacks.append(feedback)
                        current_input = ""
                        error_msg = ""
                        if guess == answer:
                            won = True
                            game_over = True
                        elif len(guesses) >= MAX_GUESSES:
                            game_over = True
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                current_input = current_input[:-1]
                error_msg = ""
                error_timer = 0
            elif 32 <= key <= 126 and len(current_input) < WORD_LEN:
                current_input += chr(key).upper()
                error_msg = ""
                error_timer = 0

        if key == curses.KEY_RESIZE:
            h, w = stdscr.getmaxyx()
            board_start_col = max(2, (w - WORD_LEN * 4) // 2)
            keyboard_start_row = board_start_row + MAX_GUESSES + 2
            keyboard_start_col = max(2, (w - 10 * 4) // 2)
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
