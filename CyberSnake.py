import pygame
import random
import sys
import os
import json

# Initialize Pygame
pygame.init()

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("CyberSnake - Cybersecurity Quiz Snake")

# Game area dimensions (centered)
GRID_SIZE = 20
GAME_WIDTH, GAME_HEIGHT = 600, 600
GAME_LEFT = (SCREEN_WIDTH - GAME_WIDTH) // 2
GAME_TOP = (SCREEN_HEIGHT - GAME_HEIGHT) // 2

# Colors
COLORS = {
    "background": (30, 30, 30),
    "grass1": (34, 139, 34),
    "grass2": (0, 100, 0),
    "snake_head": (178, 30, 30),
    "snake_body": (178, 30, 30),
    "text": (255, 255, 255),
    "menu": (0, 255, 255),
    "heart": (255, 0, 0)
}

# Translations
TRANSLATIONS = {
    "en": {
        "title": "CYBER SNAKE",
        "start": "Start Game",
        "settings": "Settings",
        "quit": "Quit Game",
        "difficulty": "Difficulty: ",
        "score": "Score: ",
        "speed": "Speed: ",
        "resume": "Resume",
        "retry": "Try Again",
        "main_menu": "Main Menu",
        "paused": "PAUSED",
        "game_over": "Game Over",
        "press_enter": "Press Enter to return",
        "controls_help": "Controls Help",
        "controls": ["Arrow Keys: Move Snake", "Eat fruit to quiz",
                     "Wrong answer loses life", "Self-collision rewinds",
                     "Esc: Pause/Quit"],
        "language": "Language",
        "back": "Back"
    },
    "ar": {
        "title": "الثعبان السيبراني",
        "start": "بدء اللعبة",
        "settings": "الإعدادات",
        "quit": "خروج",
        "difficulty": "الصعوبة: ",
        "score": "النقاط: ",
        "speed": "السرعة: ",
        "resume": "استئناف",
        "retry": "إعادة المحاولة",
        "main_menu": "القائمة الرئيسية",
        "paused": "مُتوقِف",
        "game_over": "انتهت اللعبة",
        "press_enter": "اضغط إنتر للعودة",
        "controls_help": "مساعدة التحكم",
        "controls": ["أسهم الحركة: تحريك الثعبان", "كل الفاكهة للأسئلة",
                     "إجابة خاطئة تفقد حياة", "الاصطدام الذاتي يرجع",
                     "Esc: إيقاف/خروج"],
        "language": "اللغة",
        "back": "رجوع"
    }
}

# Global settings
defined_languages = ["English", "Arabic"]
current_language_idx = 0
current_language = defined_languages[current_language_idx]
available_difficulties = ["Easy", "Medium", "Hard"]
current_difficulty_idx = 0
MAX_LIVES = 3
lives = MAX_LIVES    # will be overwritten in game_loop, but global reference needed

# Fonts
def load_fonts():
    global font, large_font
    try:
        if current_language == "Arabic":
            arabic_font = pygame.font.Font("C:/Windows/Fonts/Arabic Typestting Regular.ttf", 24)
            large_arabic_font = pygame.font.Font("C:/Windows/Fonts/Arabic Typestting Regular.ttf", 36)
            font = arabic_font
            large_font = large_arabic_font
        else:
            font = pygame.font.SysFont("segoeui", 24, bold=False)
            large_font = pygame.font.SysFont("segoeui", 36, bold=False)
    except Exception:
        font = pygame.font.SysFont("segoeui", 24, bold=False)
        large_font = pygame.font.SysFont("segoeui", 36, bold=False)

load_fonts()

# ------------------------------------------------------------
# Snake Class
# ------------------------------------------------------------
class Snake:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        center_x, center_y = GAME_WIDTH // 2, GAME_HEIGHT // 2
        self.positions = [
            (center_x, center_y),
            (center_x, center_y + GRID_SIZE),
            (center_x, center_y + 2 * GRID_SIZE)
        ]
        self.direction = (0, -GRID_SIZE)
        self.length = 3
        self.base_speed = 8.0
        self.speed = self.base_speed
        self.history = [list(self.positions)]

    def move(self):
        head_x, head_y = self.positions[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Save state for potential rewind
        self.history.append(list(self.positions))
        if len(self.history) > 10:
            self.history.pop(0)

        # --- Collision handling per difficulty ---
        if self.difficulty == "Easy":
            # Wrap around, no self-collision
            new_head = (new_head[0] % GAME_WIDTH, new_head[1] % GAME_HEIGHT)
        elif self.difficulty == "Medium":
            # No wrap, die on walls + self-collision
            if (new_head[0] < 0 or new_head[0] >= GAME_WIDTH or
                new_head[1] < 0 or new_head[1] >= GAME_HEIGHT):
                return False
            if new_head in self.positions:
                return False
        else:  # Hard
            # Wrap around, die on self-collision
            new_head = (new_head[0] % GAME_WIDTH, new_head[1] % GAME_HEIGHT)
            if new_head in self.positions:
                return False

        # Apply movement
        self.positions = [new_head] + self.positions[:-1]
        return True

    def rewind(self, steps=3):
        if len(self.history) >= steps:
            self.positions = self.history[steps - 1]
        self.history.clear()

    def grow(self):
        self.positions.append(self.positions[-1])

    def set_direction(self, new_dir):
        # Prevent 180-degree turns
        if (new_dir[0] + self.direction[0], new_dir[1] + self.direction[1]) != (0, 0):
            self.direction = new_dir

    def draw(self, surface):
        for i, pos in enumerate(self.positions):
            col = COLORS['snake_head'] if i == 0 else COLORS['snake_body']
            r = pygame.Rect(GAME_LEFT + pos[0], GAME_TOP + pos[1], GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, col, r)
            if i == 0:  # Eyes on head
                off = GRID_SIZE // 4
                pygame.draw.circle(surface, COLORS['text'], (r.left + off, r.top + off), 3)
                pygame.draw.circle(surface, COLORS['text'], (r.right - off - 3, r.top + off), 3)

# ------------------------------------------------------------
# Question loading
# ------------------------------------------------------------
def load_questions(difficulty):
    file_map = {
        "Easy": "EasyQ_ar.json" if current_language == "Arabic" else "EasyQ.json",
        "Medium": "MedQ_ar.json" if current_language == "Arabic" else "MedQ.json",
        "Hard": "HardQ_ar.json" if current_language == "Arabic" else "HardQ.json"
    }
    try:
        file_path = os.path.join("Q", file_map[difficulty])
        with open(file_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
            random.shuffle(questions)
            return questions
    except Exception:
        # Fallback question
        return [{
            "question": "افتراضي: دائماً استخدم كلمات مرور قوية؟" if current_language == "Arabic"
                       else "Default: Always use strong passwords?",
            "options": ["نعم", "لا"] if current_language == "Arabic" else ["Yes", "No"],
            "answer": 0
        }]

# ------------------------------------------------------------
# Fruit Class (with quiz attached)
# ------------------------------------------------------------
class Fruit:
    def __init__(self, snake_positions, existing_fruits, difficulty):
        self.questions = load_questions(difficulty)
        self.question_data = self.get_question()
        self.position = self.random_pos(snake_positions, existing_fruits)
        self.type = random.choice(['apple', 'banana', 'grapes', 'orange', 'strawberry'])

    def get_question(self):
        if self.questions:
            return self.questions.pop()
        # Backup
        return {
            "question": "Backup: Update software regularly?",
            "options": ["Yes", "No"],
            "answer": 0
        }

    def random_pos(self, snake_pos, fruits):
        for _ in range(100):
            x = random.randrange(0, GAME_WIDTH, GRID_SIZE)
            y = random.randrange(0, GAME_HEIGHT, GRID_SIZE)
            if (x, y) not in snake_pos and all(f.position != (x, y) for f in fruits):
                return (x, y)
        return (GAME_WIDTH // 2, GAME_HEIGHT // 2)

    def draw(self, surface):
        x, y = self.position
        cx = GAME_LEFT + x + GRID_SIZE // 2
        cy = GAME_TOP + y + GRID_SIZE // 2

        if self.type == 'apple':
            pygame.draw.circle(surface, (220, 20, 60), (cx, cy), GRID_SIZE // 2 - 2)
            pygame.draw.line(surface, (139, 69, 19), (cx, cy - GRID_SIZE // 2 + 2), (cx + 3, cy - GRID_SIZE // 2 - 5), 2)
            leaf = [(cx + 5, cy - GRID_SIZE // 2 - 5), (cx + 8, cy - GRID_SIZE // 2 - 8), (cx + 3, cy - GRID_SIZE // 2 - 10)]
            pygame.draw.polygon(surface, (34, 139, 34), leaf)
        elif self.type == 'banana':
            points = [(cx - 6, cy - 5), (cx - 3, cy - 8), (cx, cy - 9), (cx + 3, cy - 8),
                      (cx + 6, cy - 5), (cx + 4, cy), (cx + 1, cy + 3), (cx - 1, cy + 3), (cx - 4, cy)]
            pygame.draw.polygon(surface, (255, 225, 53), points)
            pygame.draw.circle(surface, (139, 69, 19), (cx - 6, cy - 5), 2)
            pygame.draw.circle(surface, (139, 69, 19), (cx + 6, cy - 5), 2)
        elif self.type == 'grapes':
            grape_color = (147, 112, 219)
            offsets = [(0, 0), (-5, -5), (5, -5), (-8, 0), (8, 0), (-5, 5), (5, 5), (0, 8)]
            for dx, dy in offsets:
                pygame.draw.circle(surface, grape_color, (cx + dx, cy + dy), 4)
            pygame.draw.line(surface, (34, 139, 34), (cx, cy - 8), (cx, cy - 12), 2)
        elif self.type == 'orange':
            pygame.draw.circle(surface, (255, 165, 0), (cx, cy), GRID_SIZE // 2 - 2)
            dimples = [(cx - 4, cy - 4), (cx + 5, cy), (cx, cy + 5), (cx - 3, cy + 3)]
            for pos in dimples:
                pygame.draw.circle(surface, (255, 215, 0), pos, 1)
        elif self.type == 'strawberry':
            points = [(cx, cy + 6), (cx + 6, cy - 4), (cx, cy - 8), (cx - 6, cy - 4)]
            pygame.draw.polygon(surface, (255, 0, 0), points)
            seeds = [(cx + 2, cy - 2), (cx - 2, cy), (cx + 3, cy + 2), (cx - 3, cy + 3)]
            for seed in seeds:
                pygame.draw.circle(surface, (255, 255, 0), seed, 1)
            leaf_points = [(cx - 4, cy - 8), (cx, cy - 12), (cx + 4, cy - 8)]
            pygame.draw.polygon(surface, (34, 139, 34), leaf_points)

# ------------------------------------------------------------
# Drawing helpers
# ------------------------------------------------------------
def draw_grass(surface):
    for x in range(0, GAME_WIDTH, GRID_SIZE):
        for y in range(0, GAME_HEIGHT, GRID_SIZE):
            col = COLORS['grass1'] if (x // GRID_SIZE + y // GRID_SIZE) % 2 == 0 else COLORS['grass2']
            pygame.draw.rect(surface, col, (GAME_LEFT + x, GAME_TOP + y, GRID_SIZE, GRID_SIZE))

def draw_text(surface, text, pos, color=COLORS['text'], font_type=None, center=True, lang="en"):
    if font_type is None:
        font_type = font
    # No RTL reversal; relies on font shaping
    surf = font_type.render(text, True, color)
    px, py = pos
    if center:
        px -= surf.get_width() // 2
        py -= surf.get_height() // 2
    surface.blit(surf, (px, py))

def draw_hearts(surface, lives):
    for i in range(lives):
        hx = SCREEN_WIDTH - 40 - 30 * i
        hy = 30
        w, h = 20, 20
        pygame.draw.circle(surface, COLORS['heart'], (hx + w // 4, hy + h // 4), w // 4)
        pygame.draw.circle(surface, COLORS['heart'], (hx + 3 * w // 4, hy + h // 4), w // 4)
        pts = [(hx, hy + h // 4), (hx + w, hy + h // 4), (hx + w // 2, hy + h)]
        pygame.draw.polygon(surface, COLORS['heart'], pts)

# ------------------------------------------------------------
# Quiz prompt
# ------------------------------------------------------------
def prompt_survey(qdata):
    if not qdata:
        return False
    sel, choosing = 0, True
    while choosing:
        screen.fill(COLORS['background'])
        draw_text(screen, qdata['question'], (SCREEN_WIDTH // 2, 150),
                  color=COLORS['text'], font_type=large_font)
        for i, opt in enumerate(qdata['options']):
            col = COLORS['menu'] if i == sel else COLORS['text']
            draw_text(screen, opt, (SCREEN_WIDTH // 2, 250 + i * 40),
                      color=col, font_type=font)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    sel = (sel - 1) % len(qdata['options'])
                elif e.key == pygame.K_DOWN:
                    sel = (sel + 1) % len(qdata['options'])
                elif e.key == pygame.K_RETURN:
                    choosing = False
                elif e.key == pygame.K_ESCAPE:
                    return None   # signal pause
    return sel == qdata['answer']

# ------------------------------------------------------------
# Game Over screen
# ------------------------------------------------------------
def show_game_over(surface, score, difficulty):
    lang = "ar" if current_language == "Arabic" else "en"
    selected = 0
    options = [TRANSLATIONS[lang]["retry"], TRANSLATIONS[lang]["main_menu"]]

    while True:
        surface.fill(COLORS['background'])
        draw_text(surface, TRANSLATIONS[lang]['game_over'],
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3),
                  color=COLORS['text'], font_type=large_font)
        draw_text(surface, f"{TRANSLATIONS[lang]['score']}{score}",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50),
                  color=COLORS['text'])
        for i, opt in enumerate(options):
            color = COLORS['menu'] if i == selected else COLORS['text']
            draw_text(surface, opt,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50 + i * 50),
                      color=color, font_type=font)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:   # Retry
                        game_loop(difficulty)
                        return
                    else:               # Main Menu
                        return

# ------------------------------------------------------------
# Pause Menu (correct single version)
# ------------------------------------------------------------
def handle_pause():
    lang = "ar" if current_language == "Arabic" else "en"
    options = [
        TRANSLATIONS[lang]["resume"],
        TRANSLATIONS[lang]["retry"],
        TRANSLATIONS[lang]["settings"],
        TRANSLATIONS[lang]["main_menu"]
    ]
    selected = 0
    clock = pygame.time.Clock()

    while True:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        draw_text(screen, TRANSLATIONS[lang]["paused"],
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150),
                  color=COLORS['menu'], font_type=large_font, lang=lang)

        for i, opt in enumerate(options):
            color = COLORS['menu'] if i == selected else COLORS['text']
            draw_text(screen, opt,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 + i * 60),
                      color=color, font_type=large_font, lang=lang)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    return selected
                elif e.key == pygame.K_ESCAPE:
                    return 0   # Resume
        clock.tick(15)

# ------------------------------------------------------------
# Settings Menu (fully updated)
# ------------------------------------------------------------
def settings_menu():
    global current_language_idx, current_language, current_difficulty_idx
    selected = 0
    # lang will be updated inside loop

    while True:
        lang = "ar" if current_language == "Arabic" else "en"
        options = [
            f"{TRANSLATIONS[lang]['language']}: {current_language}",
            f"{TRANSLATIONS[lang]['difficulty']}: {available_difficulties[current_difficulty_idx]}",
            TRANSLATIONS[lang]['controls_help'],
            TRANSLATIONS[lang]['back']
        ]

        screen.fill(COLORS['background'])
        draw_text(screen, TRANSLATIONS[lang]['settings'],
                  (SCREEN_WIDTH // 2, 100), color=COLORS['menu'], font_type=large_font)

        for i, opt in enumerate(options):
            col = COLORS['menu'] if i == selected else COLORS['text']
            draw_text(screen, str(opt), (SCREEN_WIDTH // 2, 200 + i * 50), color=col)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    if selected == 0:   # Language
                        current_language_idx = (current_language_idx + 1) % len(defined_languages)
                        current_language = defined_languages[current_language_idx]
                        load_fonts()
                    elif selected == 1: # Difficulty
                        current_difficulty_idx = (current_difficulty_idx + 1) % len(available_difficulties)
                    elif selected == 2: # Controls Help
                        controls_help()
                    elif selected == 3: # Back
                        return
                elif e.key == pygame.K_ESCAPE:
                    return

def controls_help():
    lang = "ar" if current_language == "Arabic" else "en"
    showing = True
    while showing:
        screen.fill(COLORS['background'])
        draw_text(screen, TRANSLATIONS[lang]['controls_help'],
                  (SCREEN_WIDTH // 2, 100), color=COLORS['menu'], font_type=large_font)
        for i, line in enumerate(TRANSLATIONS[lang]['controls']):
            draw_text(screen, line, (SCREEN_WIDTH // 2, 200 + i * 40),
                      color=COLORS['text'], font_type=font)
        draw_text(screen, TRANSLATIONS[lang]['press_enter'],
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100),
                  color=COLORS['text'], font_type=font)
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                showing = False

# ------------------------------------------------------------
# Main Menu
# ------------------------------------------------------------
def main_menu():
    selected = 0
    while True:
        lang = "ar" if current_language == "Arabic" else "en"
        options = [
            TRANSLATIONS[lang]["start"],
            TRANSLATIONS[lang]["settings"],
            TRANSLATIONS[lang]["quit"]
        ]
        screen.fill(COLORS['background'])
        draw_text(screen, TRANSLATIONS[lang]["title"],
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4),
                  color=COLORS['menu'], font_type=large_font)
        for i, opt in enumerate(options):
            col = COLORS['menu'] if i == selected else COLORS['text']
            draw_text(screen, opt, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 50),
                      color=col, font_type=large_font)
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    return selected

# ------------------------------------------------------------
# Main Game Loop
# ------------------------------------------------------------
def game_loop(difficulty):
    global lives
    # speed and spawn rate per difficulty
    base_speed, spawn_rate = {
        'Easy': (8, 20),
        'Medium': (12, 15),
        'Hard': (15, 10)
    }[difficulty]

    snake = Snake(difficulty)
    snake.base_speed = snake.speed = base_speed
    fruits = [Fruit(snake.positions, [], difficulty)]
    score = 0
    counter = 0
    clock = pygame.time.Clock()
    lives = MAX_LIVES

    while True:
        # Update language each frame for dynamic text
        lang = "ar" if current_language == "Arabic" else "en"

        # --- Event Handling ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    choice = handle_pause()
                    if choice == 0:       # Resume
                        pass
                    elif choice == 1:     # Try Again
                        return game_loop(difficulty)
                    elif choice == 2:     # Settings
                        settings_menu()
                        # After returning, continue with current difficulty
                    elif choice == 3:     # Main Menu
                        return
                    continue
                # Movement
                if e.key == pygame.K_UP:
                    snake.set_direction((0, -GRID_SIZE))
                elif e.key == pygame.K_DOWN:
                    snake.set_direction((0, GRID_SIZE))
                elif e.key == pygame.K_LEFT:
                    snake.set_direction((-GRID_SIZE, 0))
                elif e.key == pygame.K_RIGHT:
                    snake.set_direction((GRID_SIZE, 0))

        # --- Move snake & collision ---
        alive = snake.move()
        if not alive:
            lives -= 1
            if lives <= 0:
                break
            else:
                snake.rewind()

        # --- Fruit collision & Quiz ---
        head = snake.positions[0]
        for f in fruits[:]:
            if head == f.position:
                result = prompt_survey(f.question_data)
                if result is None:   # ESC pressed during quiz
                    choice = handle_pause()
                    if choice == 0:
                        pass
                    elif choice == 1:
                        return game_loop(difficulty)
                    elif choice == 2:
                        settings_menu()
                    elif choice == 3:
                        return
                elif result:
                    score += 1
                    snake.grow()
                    snake.speed = min(snake.speed + 0.5, 30)
                else:
                    lives -= 1
                    if lives <= 0:
                        break
                fruits.remove(f)
                fruits.append(Fruit(snake.positions, fruits, difficulty))

        if lives <= 0:
            break

        # --- Spawn new fruit periodically ---
        counter += 1
        if counter >= spawn_rate:
            counter = 0
            if len(fruits) < 5:
                fruits.append(Fruit(snake.positions, fruits, difficulty))

        # --- Drawing ---
        screen.fill(COLORS['background'])
        draw_grass(screen)
        for f in fruits:
            f.draw(screen)
        snake.draw(screen)

        # HUD
        draw_text(screen, f"{TRANSLATIONS[lang]['score']}{score}",
                  (50, 30), center=False, lang=lang)
        draw_text(screen, f"{TRANSLATIONS[lang]['speed']}{int(snake.speed)}",
                  (50, 60), center=False, lang=lang)
        draw_text(screen, f"{TRANSLATIONS[lang]['difficulty']}{difficulty}",
                  (50, 90), center=False, lang=lang)
        draw_hearts(screen, lives)

        pygame.display.flip()
        clock.tick(snake.speed)

    # Game Over
    show_game_over(screen, score, difficulty)

# ------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------
def main():
    while True:
        choice = main_menu()
        if choice == 0:
            game_loop(available_difficulties[current_difficulty_idx])
        elif choice == 1:
            settings_menu()
        elif choice == 2:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()