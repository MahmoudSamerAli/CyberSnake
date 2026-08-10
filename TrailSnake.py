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
pygame.display.set_caption("CyberSnake")

# Game area dimensions (centered)
GRID_SIZE = 20
GAME_WIDTH, GAME_HEIGHT = 600, 600
GAME_LEFT = (SCREEN_WIDTH - GAME_WIDTH) // 2
GAME_TOP = (SCREEN_HEIGHT - GAME_HEIGHT) // 2
FPS = 60

# Colors
COLORS = {
    "background": (30, 30, 30),
    "grass1": (34, 139, 34),
    "grass2": (0, 100, 0),
    "snake_head": (178, 30, 30),
    "snake_body": (178, 30, 30),
    "player2_head": (30, 30, 178),
    "player2_body": (30, 30, 178),
    "text": (255, 255, 255),
    "menu": (0, 255, 255),
    "heart": (255, 0, 0),
    "highlight": (255, 255, 0)
}

# Add these at the top with other constants
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
        "back": "Back",
        "single_player": "Single Player",
        "multiplayer": "Multiplayer",
        "p1_score": "Player 1: ",
        "p2_score": "Player 2: ",
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
        "back": "رجوع",
        "single_player": "لاعب واحد",
        "multiplayer": "لاعبين",
        "p1_score": "اللاعب 1: ",
        "p2_score": "اللاعب 2: ",
    }
}


def load_fonts():
    global font, large_font
    try:
        if current_language == "Arabic":
            arabic_font = pygame.font.Font("C:/Windows/Fonts/Arabic Typesetting.ttf", 24)
            large_arabic_font = pygame.font.Font("C:/Windows/Fonts/Arabic Typesetting.ttf", 36)
            font = arabic_font
            large_font = large_arabic_font
        else:
            font = pygame.font.SysFont("C:/Windows/Fonts/segoeui.ttf", 24, bold=False)
            large_font = pygame.font.SysFont("C:/Windows/Fonts/segoeui.ttf", 36, bold=False)
    except Exception as e:
        print(f"Error loading fonts: {e}")
        font = pygame.font.SysFont("C:/Windows/Fonts/segoeui.ttf", 24, bold=False)
        large_font = pygame.font.SysFont("C:/Windows/Fonts/segoeui.ttf", 36, bold=False)


# Settings state
defined_languages = ["English", "Arabic"]
current_language_idx = 0
current_language = defined_languages[current_language_idx]
load_fonts()
available_difficulties = ["Easy", "Medium", "Hard"]
current_difficulty_idx = 0

# Lives
global lives
MAX_LIVES = 3


class Snake:
    def __init__(self, difficulty, player=1):
        self.difficulty = difficulty
        self.player = player
        self.reset()

    def reset(self):
        center_x = GAME_WIDTH // 2 + (40 if self.player == 2 else -40)
        center_y = GAME_HEIGHT // 2
        self.positions = [
            (center_x, center_y),
            (center_x, center_y + GRID_SIZE),
            (center_x, center_y + 2 * GRID_SIZE)
        ]
        self.direction = (0, -GRID_SIZE)
        self.length = 3
        self.base_speed = 8
        self.speed = self.base_speed
        self.history = [list(self.positions)]

    def handle_input(self, event):
        if self.player == 1:
            if event.key == pygame.K_UP:
                self.set_direction((0, -GRID_SIZE))
            elif event.key == pygame.K_DOWN:
                self.set_direction((0, GRID_SIZE))
            elif event.key == pygame.K_LEFT:
                self.set_direction((-GRID_SIZE, 0))
            elif event.key == pygame.K_RIGHT:
                self.set_direction((GRID_SIZE, 0))
        elif self.player == 2:
            if event.key == pygame.K_w:
                self.set_direction((0, -GRID_SIZE))
            elif event.key == pygame.K_s:
                self.set_direction((0, GRID_SIZE))
            elif event.key == pygame.K_a:
                self.set_direction((-GRID_SIZE, 0))
            elif event.key == pygame.K_d:
                self.set_direction((GRID_SIZE, 0))

    def move(self):
        head_x, head_y = self.positions[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % GAME_WIDTH, (head_y + dy) % GAME_HEIGHT)

        self.history.append(list(self.positions))
        if len(self.history) > 10:
            self.history.pop(0)

        if self.difficulty == "Hard" and new_head in self.positions[:-1]:
            return False

        if self.difficulty == "Medium":
            if (head_x + dx < 0 or head_x + dx >= GAME_WIDTH or
                    head_y + dy < 0 or head_y + dy >= GAME_HEIGHT):
                return False
            new_head = ((head_x + dx) % GAME_WIDTH, (head_y + dy) % GAME_HEIGHT)

        self.positions = [new_head] + self.positions[:-1]
        return True

    def rewind(self, steps=3):
        if len(self.history) >= steps:
            self.positions = self.history[steps - 1]
        self.history.clear()

    def grow(self):
        self.positions.append(self.positions[-1])

    def set_direction(self, new_dir):
        if (new_dir[0] + self.direction[0], new_dir[1] + self.direction[1]) != (0, 0):
            self.direction = new_dir

    def draw(self, surface):
        for i, pos in enumerate(self.positions):
            if self.player == 1:
                col = COLORS['snake_head'] if i == 0 else COLORS['snake_body']
            else:
                col = COLORS['player2_head'] if i == 0 else COLORS['player2_body']
            r = pygame.Rect(GAME_LEFT + pos[0], GAME_TOP + pos[1], GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, col, r)


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
    except Exception as e:
        print(f"Error loading questions: {e}")
        return [{
            "question": "افتراضي: دائماً استخدم كلمات مرور قوية؟" if current_language == "Arabic"
            else "Default: Always use strong passwords?",
            "options": ["نعم", "لا"] if current_language == "Arabic" else ["Yes", "No"],
            "answer": 0
        }]


class Fruit:
    def __init__(self, snake_positions, existing_fruits, difficulty):
        self.questions = load_questions(difficulty)
        self.question_data = self.get_question()
        self.position = self.random_pos(snake_positions, existing_fruits)
        self.type = random.choice(['apple', 'banana', 'grapes', 'orange', 'strawberry'])

    def get_question(self):
        if self.questions:
            return self.questions.pop()
        return {
            "question": "Backup: Update software regularly?",
            "options": ["Yes", "No"],
            "answer": 0
        }

    def random_pos(self, snake_pos, fruits):
        valid_positions = [(x, y) for x in range(0, GAME_WIDTH, GRID_SIZE)
                           for y in range(0, GAME_HEIGHT, GRID_SIZE)
                           if (x, y) not in snake_pos and
                           all(f.position != (x, y) for f in fruits)]
        return random.choice(valid_positions) if valid_positions else (GAME_WIDTH // 2, GAME_HEIGHT // 2)

    def draw(self, surface):
        x, y = self.position
        cx = GAME_LEFT + x + GRID_SIZE // 2
        cy = GAME_TOP + y + GRID_SIZE // 2
        pygame.draw.circle(surface, (255, 0, 0), (cx, cy), GRID_SIZE // 2 - 2)


def draw_grass(surface):
    for x in range(0, GAME_WIDTH, GRID_SIZE):
        for y in range(0, GAME_HEIGHT, GRID_SIZE):
            col = COLORS['grass1'] if (x // GRID_SIZE + y // GRID_SIZE) % 2 == 0 else COLORS['grass2']
            pygame.draw.rect(surface, col, (GAME_LEFT + x, GAME_TOP + y, GRID_SIZE, GRID_SIZE))


def draw_text(surface, text, pos, color=COLORS['text'], font_type=None,
              center=True, lang="en"):
    if font_type is None:
        font_type = font

    if current_language == "Arabic" and lang == "ar":
        text = text[::-1]

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


def prompt_survey(qdata):
    global lives
    if not qdata: return False
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
                    return None
    return sel == qdata['answer']


def show_game_over(surface, score, difficulty):
    lang = "ar" if current_language == "Arabic" else "en"
    selected = 0
    options = [
        TRANSLATIONS[lang]["retry"],
        TRANSLATIONS[lang]["main_menu"]
    ]

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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        return game_loop(difficulty)
                    else:
                        return


def game_mode_menu():
    options = [
        TRANSLATIONS[current_language]["single_player"],
        TRANSLATIONS[current_language]["multiplayer"]
    ]
    selected = 0
    menu_rects = []

    while True:
        screen.fill(COLORS['background'])
        mouse_pos = pygame.mouse.get_pos()

        draw_text(screen, TRANSLATIONS[current_language]["title"],
                  (SCREEN_WIDTH // 2, 100), large_font)

        for i, opt in enumerate(options):
            y_pos = SCREEN_HEIGHT // 2 - 50 + i * 80
            color = COLORS['highlight'] if pygame.Rect(SCREEN_WIDTH // 2 - 100, y_pos - 20, 200, 50).collidepoint(
                mouse_pos) else COLORS['menu']
            draw_text(screen, opt, (SCREEN_WIDTH // 2, y_pos), color, large_font)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(len(options)):
                    y_pos = SCREEN_HEIGHT // 2 - 50 + i * 80
                    if pygame.Rect(SCREEN_WIDTH // 2 - 100, y_pos - 20, 200, 50).collidepoint(event.pos):
                        return i
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % 2
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % 2
                elif event.key == pygame.K_RETURN:
                    return selected
                elif event.key == pygame.K_ESCAPE:
                    return -1


def main_menu():
    selected = 0
    options = [
        TRANSLATIONS[lang]["start"],
        TRANSLATIONS[lang]["settings"],
        TRANSLATIONS[lang]["quit"]
    ]
    menu_rects = []

    while True:
        screen.fill(COLORS['background'])
        mouse_pos = pygame.mouse.get_pos()

        draw_text(screen, TRANSLATIONS[current_language]["title"],
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4),
                  color=COLORS['menu'], font_type=large_font)

        for i, opt in enumerate(options):
            y_pos = SCREEN_HEIGHT // 2 + i * 50
            text_surf = large_font.render(opt, True, COLORS['text'])
            rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            menu_rects.append(rect)

            if rect.collidepoint(mouse_pos):
                col = COLORS['highlight']
            else:
                col = COLORS['menu'] if i == selected else COLORS['text']

            draw_text(screen, opt, (SCREEN_WIDTH // 2, y_pos),
                      color=col, font_type=large_font)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(menu_rects):
                    if rect.collidepoint(e.pos):
                        return i
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    return selected


def settings_menu():
    global current_language_idx, current_language, current_difficulty_idx
    selected = 0
    lang = "ar" if current_language == "Arabic" else "en"
    options = [
        f"{TRANSLATIONS[lang]['language']}: {current_language}",
        f"{TRANSLATIONS[lang]['difficulty']}: {available_difficulties[current_difficulty_idx]}",
        TRANSLATIONS[lang]['controls_help'],
        TRANSLATIONS[lang]['back']
    ]

    while True:
        screen.fill(COLORS['background'])
        draw_text(screen, TRANSLATIONS[lang]['settings'],
                  (SCREEN_WIDTH // 2, 100),
                  color=COLORS['menu'], font_type=large_font)

        options[1] = f"{TRANSLATIONS[lang]['difficulty']}: {available_difficulties[current_difficulty_idx]}"

        for i, opt in enumerate(options):
            col = COLORS['menu'] if i == selected else COLORS['text']
            draw_text(screen, str(opt), (SCREEN_WIDTH // 2, 200 + i * 50), color=col)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    if selected == 0:
                        current_language_idx = (current_language_idx + 1) % len(defined_languages)
                        current_language = defined_languages[current_language_idx]
                        load_fonts()
                    elif selected == 1:
                        current_difficulty_idx = (current_difficulty_idx + 1) % len(available_difficulties)
                    elif selected == 2:
                        controls_help()
                    elif selected == 3:
                        return
                elif e.key == pygame.K_ESCAPE:
                    return


def controls_help():
    lang = "ar" if current_language == "Arabic" else "en"
    showing = True
    while showing:
        screen.fill(COLORS['background'])
        draw_text(screen, TRANSLATIONS[lang]['controls_help'],
                  (SCREEN_WIDTH // 2, 100),
                  color=COLORS['menu'], font_type=large_font)

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
                  color=COLORS['menu'], font_type=large_font)

        for i, opt in enumerate(options):
            color = COLORS['menu'] if i == selected else COLORS['text']
            draw_text(screen, opt,
                      (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 + i * 60),
                      color=color, font_type=large_font)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    return selected
                elif e.key == pygame.K_ESCAPE:
                    return 0
        clock.tick(15)


def game_loop(difficulty, players=1):
    global lives
    snakes = [Snake(difficulty, player=1)]
    if players == 2:
        snakes.append(Snake(difficulty, player=2))

    fruits = [Fruit([p for s in snakes for p in s.positions], [], difficulty)]
    scores = [0, 0]
    counter = 0
    clock = pygame.time.Clock()
    lives = MAX_LIVES
    lang = "ar" if current_language == "Arabic" else "en"

    while True:
        dt = clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    choice = handle_pause()
                    if choice == 0:
                        continue
                    elif choice == 1:
                        return game_loop(difficulty, players)
                    elif choice == 2:
                        settings_menu()
                    elif choice == 3:
                        return
                else:
                    for snake in snakes:
                        snake.handle_input(event)

        # Game logic
        for snake in snakes:
            if not snake.move():
                lives -= 1
                if lives <= 0:
                    show_game_over(max(scores), difficulty)
                    return
                else:
                    snake.rewind()

        # Fruit handling
        for f in fruits[:]:
            for i, snake in enumerate(snakes):
                if snake.positions[0] == f.position:
                    result = prompt_survey(f.question_data)
                    if result is None:
                        continue
                    elif result:
                        scores[i] += 1
                        snake.grow()
                    else:
                        lives -= 1
                        if lives <= 0:
                            show_game_over(max(scores), difficulty)
                            return
                    fruits.remove(f)
                    fruits.append(Fruit([p for s in snakes for p in s.positions], fruits, difficulty))

        # Spawn new fruit
        counter += 1
        if counter >= 20:
            counter = 0
            if len(fruits) < 5:
                fruits.append(Fruit([p for s in snakes for p in s.positions], fruits, difficulty))

        # Drawing
        screen.fill(COLORS['background'])
        draw_grass(screen)
        for f in fruits:
            f.draw(screen)
        for snake in snakes:
            snake.draw(screen)

        # HUD
        draw_text(screen, f"{TRANSLATIONS[lang]['p1_score']}{scores[0]}", (50, 30), center=False)
        if players == 2:
            draw_text(screen, f"{TRANSLATIONS[lang]['p2_score']}{scores[1]}", (SCREEN_WIDTH - 200, 30), center=False)
        draw_text(screen, f"{TRANSLATIONS[lang]['difficulty']}{difficulty}", (50, 60), center=False)
        draw_hearts(screen, lives)

        pygame.display.flip()

if __name__ == "__main__":
    while True:
        choice = main_menu()
        if choice == 0:
            game_mode = game_mode_menu()
            if game_mode == 0:
                game_loop(available_difficulties[current_difficulty_idx], 1)
            elif game_mode == 1:
                game_loop(available_difficulties[current_difficulty_idx], 2)
        elif choice == 1:
            settings_menu()
        elif choice == 2:
            pygame.quit()
            sys.exit()