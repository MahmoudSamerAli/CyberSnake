"""
CyberSnake - Cybersecurity Quiz Snake Game (Final Version)
Fixed: game speed, question timer, graphics, Arabic RTL shaping
"""

import pygame
import random
import sys
import os
import json
import time
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Try to import Arabic shaping libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False
    print("Note: Install 'arabic-reshaper' and 'python-bidi' for proper Arabic text shaping:")
    print("  pip install arabic-reshaper python-bidi")

# ============================================================
# CONFIGURATION
# ============================================================

GRID_SIZE = 20
GAME_WIDTH, GAME_HEIGHT = 600, 600
MAX_LIVES = 3
MAX_FRUITS = 5
MAX_HISTORY = 10
MAX_SNAKE_SPEED = 25

# Question timer (seconds per question)
QUESTION_TIME_LIMIT = 15

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_DIR = os.path.join(BASE_DIR, "Q")

# Difficulty settings - balanced for playability
DIFFICULTY_SETTINGS = {
    "Easy":   {"base_speed": 6, "spawn_rate": 25, "wrap_walls": True,  "self_collision": False, "speed_increment": 0.3, "question_time": 20},
    "Medium": {"base_speed": 9, "spawn_rate": 18, "wrap_walls": False, "self_collision": True,  "speed_increment": 0.4, "question_time": 15},
    "Hard":   {"base_speed": 12, "spawn_rate": 12, "wrap_walls": False,  "self_collision": True,  "speed_increment": 0.5, "question_time": 10},
}

LANGUAGES = ["English", "Arabic"]
LANG_CODES = {"English": "en", "Arabic": "ar"}

COLORS = {
    "background": (15, 15, 25),
    "grass1": (25, 100, 25),
    "grass2": (20, 80, 20),
    "snake_head": (220, 50, 50),
    "snake_body": (200, 40, 40),
    "snake_body_alt": (180, 35, 35),
    "text": (240, 240, 240),
    "menu": (0, 220, 220),
    "menu_selected": (255, 255, 100),
    "heart": (220, 30, 30),
    "overlay": (0, 0, 0, 200),
    "quiz_bg": (25, 25, 45),
    "timer_bg": (50, 20, 20),
    "timer_fg": (255, 100, 100),
    "correct_green": (80, 255, 80),
    "wrong_red": (255, 80, 80),
    "particle": (255, 200, 50),
}

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
        "controls": ["Arrow Keys: Move Snake", "Eat fruit to answer quiz",
                     "Wrong answer loses a life", "Self-collision rewinds",
                     "Esc: Pause/Quit"],
        "language": "Language",
        "back": "Back",
        "correct": "Correct!",
        "wrong": "Wrong!",
        "time_up": "Time's Up!",
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
        "controls": ["أسهم الحركة: تحريك الثعبان", "أكل الفاكهة للإجابة",
                     "إجابة خاطئة تفقد حياة", "الاصطدام الذاتي يرجع",
                     "Esc: إيقاف/خروج"],
        "language": "اللغة",
        "back": "رجوع",
        "correct": "صحيح!",
        "wrong": "خطأ!",
        "time_up": "انتهى الوقت!",
    },
}

QUESTION_FILES = {
    "Easy": {"en": "EasyQ.json", "ar": "EasyQ_ar.json"},
    "Medium": {"en": "MedQ.json", "ar": "MedQ_ar.json"},
    "Hard": {"en": "HardQ.json", "ar": "HardQ_ar.json"},
}

FRUIT_TYPES = ['apple', 'banana', 'grapes', 'orange', 'strawberry']


# ============================================================
# ARABIC TEXT SHAPING
# ============================================================

def shape_arabic_text(text: str) -> str:
    """Properly shape Arabic text with ligatures and RTL ordering."""
    if not HAS_ARABIC_SUPPORT:
        # Fallback: simple reversal for RTL display
        return text[::-1] if any('\u0600' <= ch <= '\u06FF' for ch in text) else text
    
    try:
        # Reshape for ligatures (connect letters)
        reshaped = arabic_reshaper.reshape(text)
        # Apply BiDi algorithm for RTL ordering
        return get_display(reshaped)
    except Exception:
        return text[::-1] if any('\u0600' <= ch <= '\u06FF' for ch in text) else text


def is_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


# ============================================================
# UTILITY CLASSES
# ============================================================

@dataclass
class GameSettings:
    current_language: str = "English"
    current_difficulty: str = "Easy"
    lives: int = MAX_LIVES
    
    @property
    def lang_code(self) -> str:
        return LANG_CODES[self.current_language]
    
    @property
    def difficulty_config(self) -> dict:
        return DIFFICULTY_SETTINGS[self.current_difficulty]
    
    @property
    def is_arabic(self) -> bool:
        return self.current_language == "Arabic"


class FontManager:
    """Manages font loading and text rendering with caching."""
    
    def __init__(self):
        self._fonts: Dict[str, pygame.font.Font] = {}
        self._text_cache: Dict[Tuple, pygame.Surface] = {}
        self._load_fonts()
    
    def _load_fonts(self):
        # English fonts
        self._fonts["en"] = pygame.font.SysFont("segoeui", 22, bold=False)
        self._fonts["en_large"] = pygame.font.SysFont("segoeui", 34, bold=True)
        self._fonts["en_title"] = pygame.font.SysFont("segoeui", 52, bold=True)
        self._fonts["en_timer"] = pygame.font.SysFont("consolas", 28, bold=True)
        
        # Arabic fonts - try multiple common Arabic fonts
        arabic_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/tradbdo.ttf",
            "C:/Windows/Fonts/arabtype.ttf",
        ]
        
        arabic_font_path = None
        for path in arabic_fonts:
            if os.path.exists(path):
                arabic_font_path = path
                break
        
        if arabic_font_path:
            try:
                self._fonts["ar"] = pygame.font.Font(arabic_font_path, 24)
                self._fonts["ar_large"] = pygame.font.Font(arabic_font_path, 36)
                self._fonts["ar_title"] = pygame.font.Font(arabic_font_path, 54)
                self._fonts["ar_timer"] = pygame.font.Font(arabic_font_path, 30)
            except Exception:
                self._fonts["ar"] = self._fonts["en"]
                self._fonts["ar_large"] = self._fonts["en_large"]
                self._fonts["ar_title"] = self._fonts["en_title"]
                self._fonts["ar_timer"] = self._fonts["en_timer"]
        else:
            self._fonts["ar"] = self._fonts["en"]
            self._fonts["ar_large"] = self._fonts["en_large"]
            self._fonts["ar_title"] = self._fonts["en_title"]
            self._fonts["ar_timer"] = self._fonts["en_timer"]
    
    def get_font(self, lang_code: str, size: str = "normal") -> pygame.font.Font:
        key = f"{lang_code}_{size}"
        return self._fonts.get(key, self._fonts["en"])
    
    def render(self, text: str, lang_code: str, color: Tuple[int, int, int], 
               size: str = "normal", center: bool = True) -> pygame.Surface:
        # Apply Arabic shaping
        display_text = shape_arabic_text(text) if lang_code == "ar" else text
        
        cache_key = (display_text, lang_code, color, size)
        if cache_key not in self._text_cache:
            font = self.get_font(lang_code, size)
            self._text_cache[cache_key] = font.render(display_text, True, color)
        return self._text_cache[cache_key]
    
    def clear_cache(self):
        self._text_cache.clear()


class AssetManager:
    """Manages all game assets with enhanced graphics."""
    
    def __init__(self):
        self.grass_surface: Optional[pygame.Surface] = None
        self.fruit_surfaces: Dict[str, pygame.Surface] = {}
        self.heart_surface: Optional[pygame.Surface] = None
        self.snake_head_surf: Optional[pygame.Surface] = None
        self.snake_body_surf: Optional[pygame.Surface] = None
        self.snake_body_alt_surf: Optional[pygame.Surface] = None
        self._create_assets()
    
    def _create_assets(self):
        self._create_grass_surface()
        self._create_fruit_surfaces()
        self._create_heart_surface()
        self._create_snake_surfaces()
    
    def _create_grass_surface(self):
        """Pre-render grass with subtle pattern."""
        self.grass_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        for x in range(0, GAME_WIDTH, GRID_SIZE):
            for y in range(0, GAME_HEIGHT, GRID_SIZE):
                base_col = COLORS['grass1'] if (x // GRID_SIZE + y // GRID_SIZE) % 2 == 0 else COLORS['grass2']
                # Add subtle noise
                noise = random.randint(-5, 5)
                col = tuple(max(0, min(255, c + noise)) for c in base_col)
                pygame.draw.rect(self.grass_surface, col, (x, y, GRID_SIZE, GRID_SIZE))
    
    def _create_fruit_surfaces(self):
        """Pre-render enhanced fruit surfaces with details."""
        fruit_size = GRID_SIZE
        radius = fruit_size // 2 - 1
        center = fruit_size // 2
        
        for fruit_type in FRUIT_TYPES:
            surf = pygame.Surface((fruit_size, fruit_size), pygame.SRCALPHA)
            cx, cy = center, center
            
            if fruit_type == 'apple':
                # Apple with gradient-like effect
                pygame.draw.circle(surf, (200, 30, 50), (cx, cy), radius)
                pygame.draw.circle(surf, (255, 80, 80), (cx - 3, cy - 3), radius // 3)
                # Stem
                pygame.draw.line(surf, (100, 60, 20), (cx, cy - radius), (cx + 2, cy - radius - 4), 2)
                # Leaf
                leaf = [(cx + 4, cy - radius - 4), (cx + 8, cy - radius - 8), (cx + 2, cy - radius - 10)]
                pygame.draw.polygon(surf, (50, 180, 50), leaf)
            
            elif fruit_type == 'banana':
                # Curved banana
                points = [(cx - 7, cy - 4), (cx - 4, cy - 7), (cx, cy - 8), (cx + 4, cy - 7),
                          (cx + 7, cy - 4), (cx + 5, cy + 1), (cx + 2, cy + 3), (cx - 2, cy + 3), (cx - 5, cy + 1)]
                pygame.draw.polygon(surf, (255, 230, 60), points)
                pygame.draw.polygon(surf, (255, 210, 40), points, 2)
                # Tips
                pygame.draw.circle(surf, (150, 100, 30), (cx - 7, cy - 4), 2)
                pygame.draw.circle(surf, (150, 100, 30), (cx + 7, cy - 4), 2)
            
            elif fruit_type == 'grapes':
                # Bunch of grapes
                grape_color = (160, 100, 220)
                highlight = (200, 150, 255)
                offsets = [(0, 0), (-6, -6), (6, -6), (-9, 0), (9, 0), (-6, 6), (6, 6), (0, 9)]
                for dx, dy in offsets:
                    pygame.draw.circle(surf, grape_color, (cx + dx, cy + dy), 5)
                    pygame.draw.circle(surf, highlight, (cx + dx - 1, cy + dy - 1), 2)
                # Stem
                pygame.draw.line(surf, (50, 150, 50), (cx, cy - 9), (cx, cy - 13), 3)
            
            elif fruit_type == 'orange':
                # Orange with texture
                pygame.draw.circle(surf, (255, 160, 0), (cx, cy), radius)
                pygame.draw.circle(surf, (255, 200, 50), (cx - 3, cy - 3), radius // 2)
                # Dimples
                for pos in [(cx - 4, cy - 4), (cx + 5, cy), (cx, cy + 5), (cx - 3, cy + 3)]:
                    pygame.draw.circle(surf, (255, 220, 100), pos, 2)
            
            elif fruit_type == 'strawberry':
                # Strawberry shape
                points = [(cx, cy + 7), (cx + 7, cy - 3), (cx, cy - 9), (cx - 7, cy - 3)]
                pygame.draw.polygon(surf, (255, 40, 40), points)
                # Seeds
                seeds = [(cx + 2, cy - 2), (cx - 2, cy), (cx + 3, cy + 2), (cx - 3, cy + 3), (cx, cy - 5)]
                for seed in seeds:
                    pygame.draw.circle(surf, (255, 255, 100), seed, 2)
                # Leaves
                leaf_points = [(cx - 5, cy - 9), (cx, cy - 13), (cx + 5, cy - 9)]
                pygame.draw.polygon(surf, (50, 180, 50), leaf_points)
            
            self.fruit_surfaces[fruit_type] = surf
    
    def _create_heart_surface(self):
        w, h = 24, 24
        self.heart_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        # Heart shape with gradient
        pygame.draw.circle(self.heart_surface, COLORS['heart'], (w // 4, h // 4), w // 4)
        pygame.draw.circle(self.heart_surface, COLORS['heart'], (3 * w // 4, h // 4), w // 4)
        pts = [(0, h // 4), (w, h // 4), (w // 2, h)]
        pygame.draw.polygon(self.heart_surface, COLORS['heart'], pts)
        # Highlight
        pygame.draw.circle(self.heart_surface, (255, 100, 100), (w // 4, h // 4), w // 6)
    
    def _create_snake_surfaces(self):
        # Head with gradient
        self.snake_head_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.snake_head_surf, COLORS['snake_head'], (0, 0, GRID_SIZE, GRID_SIZE), border_radius=4)
        pygame.draw.rect(self.snake_head_surf, (255, 100, 100), (2, 2, GRID_SIZE - 4, GRID_SIZE - 4), border_radius=2)
        # Eyes
        off = GRID_SIZE // 4
        pygame.draw.circle(self.snake_head_surf, COLORS['text'], (off, off), 4)
        pygame.draw.circle(self.snake_head_surf, COLORS['text'], (GRID_SIZE - off - 3, off), 4)
        pygame.draw.circle(self.snake_head_surf, (0, 0, 0), (off, off), 2)
        pygame.draw.circle(self.snake_head_surf, (0, 0, 0), (GRID_SIZE - off - 3, off), 2)
        
        # Body segments (alternating)
        self.snake_body_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.snake_body_surf, COLORS['snake_body'], (0, 0, GRID_SIZE, GRID_SIZE), border_radius=3)
        pygame.draw.rect(self.snake_body_surf, (220, 60, 60), (2, 2, GRID_SIZE - 4, GRID_SIZE - 4), border_radius=1)
        
        self.snake_body_alt_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.snake_body_alt_surf, COLORS['snake_body_alt'], (0, 0, GRID_SIZE, GRID_SIZE), border_radius=3)
        pygame.draw.rect(self.snake_body_alt_surf, (200, 50, 50), (2, 2, GRID_SIZE - 4, GRID_SIZE - 4), border_radius=1)


class QuestionManager:
    """Loads and manages questions for all difficulties and languages."""
    
    def __init__(self):
        self._questions: Dict[str, Dict[str, List[dict]]] = {}
        self._indices: Dict[str, Dict[str, int]] = {}
        self._load_all_questions()
    
    def _load_all_questions(self):
        for difficulty in DIFFICULTY_SETTINGS.keys():
            self._questions[difficulty] = {}
            self._indices[difficulty] = {}
            for lang_code in ["en", "ar"]:
                file_name = QUESTION_FILES[difficulty][lang_code]
                file_path = os.path.join(QUESTIONS_DIR, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        questions = json.load(f)
                        random.shuffle(questions)
                        self._questions[difficulty][lang_code] = questions
                        self._indices[difficulty][lang_code] = 0
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")
                    fallback = self._get_fallback_questions(lang_code)
                    self._questions[difficulty][lang_code] = fallback
                    self._indices[difficulty][lang_code] = 0
    
    def _get_fallback_questions(self, lang_code: str) -> List[dict]:
        if lang_code == "ar":
            return [
                {"question": "ما هو أقوى كلمة مرور؟", "options": ["123456", "password", "Tr0ub4dor&3", "admin"], "answer": 2},
                {"question": "ماذا تفعل عند تلقي بريد مشبوه؟", "options": ["افتح المرفقات", "احذفه فوراً", "أرسله لأصدقاء", "رد للتحقق"], "answer": 1},
                {"question": "ما هو التصيد الاحتيالي؟", "options": ["رياضة صيد", "احتيال عبر البريد", "لغة برمجة", "بروتوكول أمان"], "answer": 1},
            ]
        else:
            return [
                {"question": "What is a strong password?", "options": ["Password123", "pet name", "Tr0ub4dor&3", "12345678"], "answer": 2},
                {"question": "What to do with suspicious email?", "options": ["Open attachments", "Delete immediately", "Forward to friends", "Reply to verify"], "answer": 1},
                {"question": "What is phishing?", "options": ["Fishing sport", "Email scam", "Programming language", "Security protocol"], "answer": 1},
            ]
    
    def get_question(self, difficulty: str, lang_code: str) -> dict:
        questions = self._questions[difficulty][lang_code]
        idx = self._indices[difficulty][lang_code]
        if idx >= len(questions):
            random.shuffle(questions)
            self._indices[difficulty][lang_code] = 0
            idx = 0
        question = questions[idx]
        self._indices[difficulty][lang_code] = idx + 1
        return question


# ============================================================
# PARTICLE SYSTEM FOR EFFECTS
# ============================================================

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 200 * dt  # gravity
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface, game_left: int, game_top: int):
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(self.size * (self.life / self.max_life)))
        color = (*self.color, alpha)
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (size, size), size)
        surface.blit(surf, (game_left + int(self.x) - size, game_top + int(self.y) - size))


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
    
    def add_explosion(self, x: int, y: int, color: Tuple[int, int, int], count: int = 15):
        for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(50, 150)
                self.particles.append(Particle(
                x=x, y=y,
                    vx=speed * math.cos(angle),
                    vy=speed * math.sin(angle),
                life=random.uniform(0.5, 1.0),
                max_life=1.0,
                color=color,
                size=random.uniform(3, 6)
            ))
    
    def add_collect(self, x: int, y: int, color: Tuple[int, int, int], count: int = 8):
        for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(30, 80)
                self.particles.append(Particle(
                x=x, y=y,
                    vx=speed * math.cos(angle),
                    vy=speed * math.sin(angle) - 50,
                life=random.uniform(0.3, 0.6),
                max_life=0.6,
                color=color,
                size=random.uniform(2, 4)
            ))
    
    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, surface: pygame.Surface, game_left: int, game_top: int):
        for p in self.particles:
            p.draw(surface, game_left, game_top)


# ============================================================
# GAME ENTITIES
# ============================================================

class Snake:
    def __init__(self, difficulty: str):
        self.difficulty = difficulty
        self.config = DIFFICULTY_SETTINGS[difficulty]
        self.base_speed = self.config["base_speed"]
        self.speed = float(self.base_speed)
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
        self.history: List[List[Tuple[int, int]]] = [list(self.positions)]
    
    def move(self) -> bool:
        head_x, head_y = self.positions[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        
        self.history.append(list(self.positions))
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
        
        wrap_walls = self.config["wrap_walls"]
        self_collision = self.config["self_collision"]
        
        if wrap_walls:
            new_head = (new_head[0] % GAME_WIDTH, new_head[1] % GAME_HEIGHT)
        else:
            if (new_head[0] < 0 or new_head[0] >= GAME_WIDTH or
                new_head[1] < 0 or new_head[1] >= GAME_HEIGHT):
                return False
        
        if self_collision and new_head in self.positions:
            return False
        
        self.positions = [new_head] + self.positions[:-1]
        return True
    
    def rewind(self, steps: int = 3):
        if len(self.history) >= steps:
            self.positions = self.history[steps - 1]
        self.history.clear()
        self.history.append(list(self.positions))
    
    def grow(self):
        self.positions.append(self.positions[-1])
        self.length += 1
    
    def set_direction(self, new_dir: Tuple[int, int]):
        if (new_dir[0] + self.direction[0], new_dir[1] + self.direction[1]) != (0, 0):
            self.direction = new_dir
    
    def increase_speed(self):
        inc = self.config["speed_increment"]
        self.speed = min(self.speed + inc, MAX_SNAKE_SPEED)
    
    def draw(self, surface: pygame.Surface, assets: AssetManager, game_left: int, game_top: int):
        for i, (x, y) in enumerate(self.positions):
            if i == 0:
                seg_surf = assets.snake_head_surf
            elif i % 2 == 0:
                seg_surf = assets.snake_body_surf
            else:
                seg_surf = assets.snake_body_alt_surf
            surface.blit(seg_surf, (game_left + x, game_top + y))


class Fruit:
    def __init__(self, snake_positions: List[Tuple[int, int]], 
                 existing_fruits: List['Fruit'], 
                 difficulty: str, 
                 lang_code: str,
                 question_manager: QuestionManager):
        self.difficulty = difficulty
        self.lang_code = lang_code
        self.question_manager = question_manager
        self.question_data = question_manager.get_question(difficulty, lang_code)
        self.position = self._random_pos(snake_positions, existing_fruits)
        self.type = random.choice(FRUIT_TYPES)
        self.pulse_time = 0
    
    def _random_pos(self, snake_pos: List[Tuple[int, int]], 
                    fruits: List['Fruit']) -> Tuple[int, int]:
        occupied = set(snake_pos) | {f.position for f in fruits}
        for _ in range(100):
            x = random.randrange(0, GAME_WIDTH, GRID_SIZE)
            y = random.randrange(0, GAME_HEIGHT, GRID_SIZE)
            if (x, y) not in occupied:
                return (x, y)
        return (GAME_WIDTH // 2, GAME_HEIGHT // 2)
    
    def update(self, dt: float):
        self.pulse_time += dt
    
    def draw(self, surface: pygame.Surface, assets: AssetManager, game_left: int, game_top: int):
        fruit_surf = assets.fruit_surfaces[self.type]
        x, y = self.position
        # Pulsing animation
        pulse = 1.0 + 0.05 * abs(pygame.math.Vector2(1, 0).rotate(self.pulse_time * 180).x)
        scaled = pygame.transform.scale(fruit_surf, 
            (int(GRID_SIZE * pulse), int(GRID_SIZE * pulse)))
        offset = (GRID_SIZE * (pulse - 1)) // 2
        surface.blit(scaled, (game_left + x - offset, game_top + y - offset))


# ============================================================
# UI COMPONENTS
# ============================================================

class UIManager:
    def __init__(self, font_manager: FontManager, assets: AssetManager):
        self.font_manager = font_manager
        self.assets = assets
        self._hud_cache: Dict[str, pygame.Surface] = {}
        self._last_hud_values: Dict[str, Any] = {}
    
    def draw_text(self, surface: pygame.Surface, text: str, pos: Tuple[int, int],
                  color: Tuple[int, int, int], lang_code: str, 
                  size: str = "normal", center: bool = True):
        rendered = self.font_manager.render(text, lang_code, color, size)
        px, py = pos
        if center:
            px -= rendered.get_width() // 2
            py -= rendered.get_height() // 2
        surface.blit(rendered, (px, py))
    
    def draw_hearts(self, surface: pygame.Surface, lives: int):
        if self.assets.heart_surface:
            for i in range(lives):
                hx = surface.get_width() - 40 - 30 * i
                hy = 30
                surface.blit(self.assets.heart_surface, (hx, hy))
    
    def draw_hud(self, surface: pygame.Surface, score: int, speed: float, 
                 difficulty: str, lives: int, lang_code: str):
        hud_key = f"{score}_{int(speed)}_{difficulty}_{lives}_{lang_code}"
        if hud_key != self._last_hud_values.get('key'):
            self._rebuild_hud_cache(score, speed, difficulty, lang_code)
            self._last_hud_values['key'] = hud_key
        
        y = 30
        for text_surf in self._hud_cache.values():
            surface.blit(text_surf, (50, y))
            y += 30
        
        self.draw_hearts(surface, lives)
    
    def _rebuild_hud_cache(self, score: int, speed: float, difficulty: str, lang_code: str):
        t = TRANSLATIONS[lang_code]
        self._hud_cache = {
            'score': self.font_manager.render(f"{t['score']}{score}", lang_code, COLORS['text']),
            'speed': self.font_manager.render(f"{t['speed']}{int(speed)}", lang_code, COLORS['text']),
            'difficulty': self.font_manager.render(f"{t['difficulty']}{difficulty}", lang_code, COLORS['text']),
        }


class GameState(Enum):
    MAIN_MENU = "main_menu"
    SETTINGS = "settings"
    CONTROLS = "controls"
    PLAYING = "playing"
    PAUSED = "paused"
    QUIZ = "quiz"
    QUIZ_RESULT = "quiz_result"
    GAME_OVER = "game_over"


class Menu:
    def __init__(self, font_manager: FontManager, ui_manager: UIManager):
        self.font_manager = font_manager
        self.ui_manager = ui_manager
        self.selected = 0
    
    def handle_event(self, event: pygame.event.Event) -> Optional[int]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.selected
            elif event.key == pygame.K_ESCAPE:
                return -1
        return None
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        raise NotImplementedError


class MainMenu(Menu):
    def __init__(self, font_manager: FontManager, ui_manager: UIManager):
        super().__init__(font_manager, ui_manager)
        self.options = ["start", "settings", "quit"]
        self.title_pulse = 0
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        t = TRANSLATIONS[lang_code]
        surface.fill(COLORS['background'])
        
        # Animated title
        self.title_pulse += 0.05
        title_color = (
            int(COLORS['menu'][0] + 30 * abs(pygame.math.Vector2(1, 0).rotate(self.title_pulse * 100).x)),
            int(COLORS['menu'][1] + 30 * abs(pygame.math.Vector2(1, 0).rotate(self.title_pulse * 100).x)),
            int(COLORS['menu'][2] + 30 * abs(pygame.math.Vector2(1, 0).rotate(self.title_pulse * 100).x)),
        )
        
        self.ui_manager.draw_text(surface, t["title"], 
                                  (surface.get_width() // 2, surface.get_height() // 4),
                                  title_color, lang_code, size="title")
        for i, opt_key in enumerate(self.options):
            color = COLORS['menu_selected'] if i == self.selected else COLORS['text']
            self.ui_manager.draw_text(surface, t[opt_key],
                                      (surface.get_width() // 2, surface.get_height() // 2 + i * 60),
                                      color, lang_code, size="large")


class SettingsMenu(Menu):
    def __init__(self, font_manager: FontManager, ui_manager: UIManager, 
                 settings: GameSettings, on_language_change: callable):
        super().__init__(font_manager, ui_manager)
        self.settings = settings
        self.on_language_change = on_language_change
        self.options = ["language", "difficulty", "controls", "back"]
    
    @property
    def option_labels(self) -> List[str]:
        t = TRANSLATIONS[self.settings.lang_code]
        return [
            f"{t['language']}: {self.settings.current_language}",
            f"{t['difficulty']}: {self.settings.current_difficulty}",
            t['controls_help'],
            t['back']
        ]
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        t = TRANSLATIONS[lang_code]
        surface.fill(COLORS['background'])
        self.ui_manager.draw_text(surface, t["settings"],
                                  (surface.get_width() // 2, 100),
                                  COLORS['menu'], lang_code, size="large")
        for i, label in enumerate(self.option_labels):
            color = COLORS['menu_selected'] if i == self.selected else COLORS['text']
            self.ui_manager.draw_text(surface, label,
                                      (surface.get_width() // 2, 200 + i * 60),
                                      color, lang_code)
    
    def handle_selection(self) -> Optional[str]:
        if self.selected == 0:
            idx = LANGUAGES.index(self.settings.current_language)
            self.settings.current_language = LANGUAGES[(idx + 1) % len(LANGUAGES)]
            self.on_language_change()
        elif self.selected == 1:
            diffs = list(DIFFICULTY_SETTINGS.keys())
            idx = diffs.index(self.settings.current_difficulty)
            self.settings.current_difficulty = diffs[(idx + 1) % len(diffs)]
        elif self.selected == 2:
            return "controls"
        elif self.selected == 3:
            return "back"
        return None


class ControlsMenu(Menu):
    def __init__(self, font_manager: FontManager, ui_manager: UIManager):
        super().__init__(font_manager, ui_manager)
        self.options = []
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        t = TRANSLATIONS[lang_code]
        surface.fill(COLORS['background'])
        self.ui_manager.draw_text(surface, t["controls_help"],
                                  (surface.get_width() // 2, 80),
                                  COLORS['menu'], lang_code, size="large")
        for i, line in enumerate(t["controls"]):
            self.ui_manager.draw_text(surface, line,
                                      (surface.get_width() // 2, 180 + i * 45),
                                      COLORS['text'], lang_code)
        self.ui_manager.draw_text(surface, t["press_enter"],
                                  (surface.get_width() // 2, surface.get_height() - 80),
                                  COLORS['text'], lang_code)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[int]:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return -1
        return None


class PauseMenu(Menu):
    def __init__(self, font_manager: FontManager, ui_manager: UIManager):
        super().__init__(font_manager, ui_manager)
        self.options = ["resume", "retry", "settings", "main_menu"]
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        t = TRANSLATIONS[lang_code]
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill(COLORS['overlay'])
        surface.blit(overlay, (0, 0))
        
        self.ui_manager.draw_text(surface, t["paused"],
                                  (surface.get_width() // 2, surface.get_height() // 2 - 160),
                                  COLORS['menu'], lang_code, size="large")
        for i, opt_key in enumerate(self.options):
            color = COLORS['menu_selected'] if i == self.selected else COLORS['text']
            self.ui_manager.draw_text(surface, t[opt_key],
                                      (surface.get_width() // 2, surface.get_height() // 2 - 60 + i * 60),
                                      color, lang_code, size="large")


class GameOverMenu(Menu):
    def __init__(self, font_manager: FontManager, ui_manager: UIManager):
        super().__init__(font_manager, ui_manager)
        self.options = ["retry", "main_menu"]
        self.score = 0
        self.difficulty = "Easy"
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        t = TRANSLATIONS[lang_code]
        surface.fill(COLORS['background'])
        self.ui_manager.draw_text(surface, t["game_over"],
                                  (surface.get_width() // 2, surface.get_height() // 3),
                                  COLORS['text'], lang_code, size="large")
        self.ui_manager.draw_text(surface, f"{t['score']}{self.score}",
                                  (surface.get_width() // 2, surface.get_height() // 2 - 40),
                                  COLORS['text'], lang_code, size="large")
        for i, opt_key in enumerate(self.options):
            color = COLORS['menu_selected'] if i == self.selected else COLORS['text']
            self.ui_manager.draw_text(surface, t[opt_key],
                                      (surface.get_width() // 2, surface.get_height() // 2 + 40 + i * 60),
                                      color, lang_code, size="large")


class QuizUI:
    """Quiz with timer, unpauseable, visual feedback."""
    
    def __init__(self, font_manager: FontManager, ui_manager: UIManager):
        self.font_manager = font_manager
        self.ui_manager = ui_manager
        self.selected = 0
        self.question_data: Optional[dict] = None
        self.show_result = False
        self.result_correct = False
        self.result_timer = 0.0
        self.time_limit = 15.0
        self.time_remaining = 15.0
        self.timer_warning = False
    
    def set_question(self, question_data: dict, time_limit: float):
        self.question_data = question_data
        self.selected = 0
        self.show_result = False
        self.time_limit = time_limit
        self.time_remaining = time_limit
        self.timer_warning = False
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if not self.question_data or event.type != pygame.KEYDOWN:
            return None
        
        if self.show_result:
            self.show_result = False
            return 'continue'
        
        # ESC does NOT pause during quiz - unpauseable
        if event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.question_data['options'])
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.question_data['options'])
        elif event.key == pygame.K_RETURN:
            is_correct = (self.selected == self.question_data['answer'])
            self.show_result = True
            self.result_correct = is_correct
            self.result_timer = 1.0  # 1 second to show result
            return 'correct' if is_correct else 'wrong'
        return None
    
    def update(self, dt: float):
        if self.show_result:
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.show_result = False
        else:
            self.time_remaining -= dt
            if self.time_remaining <= 0:
                # Time's up - auto select wrong
                self.show_result = True
                self.result_correct = False
                self.result_timer = 1.0
            elif self.time_remaining <= 3.0:
                self.timer_warning = True
    
    def draw(self, surface: pygame.Surface, lang_code: str):
        if not self.question_data:
            return
        
        t = TRANSLATIONS[lang_code]
        surface.fill(COLORS['quiz_bg'])
        
        # Timer bar at top
        bar_width = surface.get_width() - 100
        bar_height = 12
        bar_x = 50
        bar_y = 40
        
        # Background
        pygame.draw.rect(surface, COLORS['timer_bg'], (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        # Foreground
        progress = max(0, self.time_remaining / self.time_limit)
        fg_color = COLORS['timer_fg'] if self.timer_warning else COLORS['correct_green']
        fg_width = int(bar_width * progress)
        if fg_width > 0:
            pygame.draw.rect(surface, fg_color, (bar_x, bar_y, fg_width, bar_height), border_radius=6)
        # Border
        pygame.draw.rect(surface, COLORS['text'], (bar_x, bar_y, bar_width, bar_height), 2, border_radius=6)
        
        # Timer text
        timer_text = f"{self.time_remaining:.1f}s"
        timer_surf = self.font_manager.render(timer_text, lang_code, COLORS['text'], size="timer")
        surface.blit(timer_surf, (surface.get_width() - 100, 30))
        
        # Question
        self.ui_manager.draw_text(surface, self.question_data['question'],
                                  (surface.get_width() // 2, 120),
                                  COLORS['text'], lang_code, size="large")
        
        # Options
        for i, opt in enumerate(self.question_data['options']):
            if self.show_result:
                if i == self.question_data['answer']:
                    color = COLORS['correct_green']
                elif i == self.selected and not self.result_correct:
                    color = COLORS['wrong_red']
                else:
                    color = COLORS['text']
            else:
                color = COLORS['menu_selected'] if i == self.selected else COLORS['text']
            
            self.ui_manager.draw_text(surface, opt,
                                      (surface.get_width() // 2, 240 + i * 55),
                                      color, lang_code)
        
        # Result feedback
        if self.show_result:
            result_text = t["correct"] if self.result_correct else t["wrong"]
            if self.time_remaining <= 0 and not self.result_correct:
                result_text = t["time_up"]
            result_color = COLORS['correct_green'] if self.result_correct else COLORS['wrong_red']
            self.ui_manager.draw_text(surface, result_text,
                                      (surface.get_width() // 2, surface.get_height() - 100),
                                      result_color, lang_code, size="large")


# ============================================================
# MAIN GAME CLASS
# ============================================================

class CyberSnakeGame:
    def __init__(self):
        info = pygame.display.Info()
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("CyberSnake - Cybersecurity Quiz Snake")
        
        self.GAME_LEFT = (self.SCREEN_WIDTH - GAME_WIDTH) // 2
        self.GAME_TOP = (self.SCREEN_HEIGHT - GAME_HEIGHT) // 2
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MAIN_MENU
        self.last_time = time.time()
        
        # Core managers
        self.settings = GameSettings()
        self.font_manager = FontManager()
        self.assets = AssetManager()
        self.question_manager = QuestionManager()
        self.ui_manager = UIManager(self.font_manager, self.assets)
        self.particles = ParticleSystem()
        
        # Menus
        self.main_menu = MainMenu(self.font_manager, self.ui_manager)
        self.settings_menu = SettingsMenu(self.font_manager, self.ui_manager, 
                                          self.settings, self._on_language_change)
        self.controls_menu = ControlsMenu(self.font_manager, self.ui_manager)
        self.pause_menu = PauseMenu(self.font_manager, self.ui_manager)
        self.game_over_menu = GameOverMenu(self.font_manager, self.ui_manager)
        self.quiz_ui = QuizUI(self.font_manager, self.ui_manager)
        
        # Game entities
        self.snake: Optional[Snake] = None
        self.fruits: List[Fruit] = []
        self.score = 0
        self.spawn_counter = 0
        self.current_fruit: Optional[Fruit] = None
        self.quiz_result_pending = None
    
    def _on_language_change(self):
        self.font_manager.clear_cache()
        self.ui_manager._hud_cache.clear()
        self.ui_manager._last_hud_values.clear()
    
    def _start_game(self):
        self.snake = Snake(self.settings.current_difficulty)
        self.fruits = [Fruit(self.snake.positions, [], 
                            self.settings.current_difficulty, 
                            self.settings.lang_code,
                            self.question_manager)]
        self.score = 0
        self.spawn_counter = 0
        self.settings.lives = MAX_LIVES
        self.current_fruit = None
        self.quiz_result_pending = None
        self.particles = ParticleSystem()
        self.state = GameState.PLAYING
    
    def _handle_quiz_result(self, result: str):
        if result == 'correct':
            self.score += 1
            self.snake.grow()
            self.snake.increase_speed()
            # Particles for correct answer
            head_x, head_y = self.snake.positions[0]
            self.particles.add_collect(head_x, head_y, COLORS['correct_green'])
        else:
            self.settings.lives -= 1
            if self.settings.lives <= 0:
                self._game_over()
                return
            # Particles for wrong answer
            head_x, head_y = self.snake.positions[0]
            self.particles.add_explosion(head_x, head_y, COLORS['wrong_red'])
        
        if self.current_fruit in self.fruits:
            self.fruits.remove(self.current_fruit)
        self.fruits.append(Fruit(self.snake.positions, self.fruits,
                                self.settings.current_difficulty,
                                self.settings.lang_code,
                                self.question_manager))
        self.current_fruit = None
        self.state = GameState.PLAYING
    
    def _game_over(self):
        self.game_over_menu.score = self.score
        self.game_over_menu.difficulty = self.settings.current_difficulty
        self.game_over_menu.selected = 0
        self.state = GameState.GAME_OVER
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if self.state == GameState.MAIN_MENU:
                result = self.main_menu.handle_event(event)
                if result is not None:
                    if result == 0:
                        self._start_game()
                    elif result == 1:
                        self.state = GameState.SETTINGS
                        self.settings_menu.selected = 0
                    elif result == 2:
                        self.running = False
            
            elif self.state == GameState.SETTINGS:
                result = self.settings_menu.handle_event(event)
                if result is not None:
                    if result == -1:
                        self.state = GameState.MAIN_MENU
                    else:
                        action = self.settings_menu.handle_selection()
                        if action == "controls":
                            self.state = GameState.CONTROLS
                        elif action == "back":
                            self.state = GameState.MAIN_MENU
            
            elif self.state == GameState.CONTROLS:
                result = self.controls_menu.handle_event(event)
                if result == -1:
                    self.state = GameState.SETTINGS
            
            elif self.state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.pause_menu.selected = 0
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_UP:
                        self.snake.set_direction((0, -GRID_SIZE))
                    elif event.key == pygame.K_DOWN:
                        self.snake.set_direction((0, GRID_SIZE))
                    elif event.key == pygame.K_LEFT:
                        self.snake.set_direction((-GRID_SIZE, 0))
                    elif event.key == pygame.K_RIGHT:
                        self.snake.set_direction((GRID_SIZE, 0))
            
            elif self.state == GameState.PAUSED:
                result = self.pause_menu.handle_event(event)
                if result is not None:
                    if result == 0:
                        self.state = GameState.PLAYING
                    elif result == 1:
                        self._start_game()
                    elif result == 2:
                        self.state = GameState.SETTINGS
                        self.settings_menu.selected = 0
                    elif result == 3:
                        self.state = GameState.MAIN_MENU
            
            elif self.state == GameState.QUIZ:
                result = self.quiz_ui.handle_event(event)
                if result is not None:
                    if result in ('correct', 'wrong'):
                        self.quiz_result_pending = result
                        self.state = GameState.QUIZ_RESULT
            
            elif self.state == GameState.QUIZ_RESULT:
                result = self.quiz_ui.handle_event(event)
                if result == 'continue' and self.quiz_result_pending:
                    self._handle_quiz_result(self.quiz_result_pending)
                    self.quiz_result_pending = None
                            # Also handle auto-continue when timer expires
                            elif self.quiz_ui.show_result and self.quiz_ui.result_timer <= 0:
                                if self.quiz_result_pending:
                                    self._handle_quiz_result(self.quiz_result_pending)
                                    self.quiz_result_pending = None
            
            elif self.state == GameState.GAME_OVER:
                result = self.game_over_menu.handle_event(event)
                if result is not None:
                    if result == 0:
                        self._start_game()
                    elif result == 1:
                        self.state = GameState.MAIN_MENU
    
    def update(self, dt: float):
            # Update quiz timer in QUIZ and QUIZ_RESULT states
            if self.state in (GameState.QUIZ, GameState.QUIZ_RESULT):
                self.quiz_ui.update(dt)
                # Handle quiz result transition
                if self.state == GameState.QUIZ_RESULT:
                    result = self.quiz_ui.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UNKNOWN))
                    if result == 'continue' and self.quiz_result_pending:
                        self._handle_quiz_result(self.quiz_result_pending)
                        self.quiz_result_pending = None
                return
        
        if self.state != GameState.PLAYING:
            return
        
        # Move snake
        alive = self.snake.move()
        if not alive:
            self.settings.lives -= 1
            if self.settings.lives <= 0:
                self._game_over()
                return
            else:
                self.snake.rewind()
        
        # Check fruit collision
        head = self.snake.positions[0]
        for fruit in self.fruits[:]:
            if head == fruit.position:
                self.current_fruit = fruit
                time_limit = self.settings.difficulty_config["question_time"]
                self.quiz_ui.set_question(fruit.question_data, time_limit)
                self.state = GameState.QUIZ
                break
        
        # Spawn new fruits
        if self.state == GameState.PLAYING:
            config = self.settings.difficulty_config
            self.spawn_counter += 1
            if self.spawn_counter >= config["spawn_rate"]:
                self.spawn_counter = 0
                if len(self.fruits) < MAX_FRUITS:
                    self.fruits.append(Fruit(self.snake.positions, self.fruits,
                                            self.settings.current_difficulty,
                                            self.settings.lang_code,
                                            self.question_manager))
        
        # Update fruits animation
        for fruit in self.fruits:
            fruit.update(dt)
        
        # Update particles
        self.particles.update(dt)
    
    def draw(self):
        lang_code = self.settings.lang_code
        
        if self.state == GameState.MAIN_MENU:
            self.main_menu.draw(self.screen, lang_code)
        
        elif self.state == GameState.SETTINGS:
            self.settings_menu.draw(self.screen, lang_code)
        
        elif self.state == GameState.CONTROLS:
            self.controls_menu.draw(self.screen, lang_code)
        
        elif self.state in (GameState.PLAYING, GameState.QUIZ, GameState.QUIZ_RESULT, GameState.PAUSED):
            self.screen.fill(COLORS['background'])
            
            # Grass background
            self.screen.blit(self.assets.grass_surface, (self.GAME_LEFT, self.GAME_TOP))
            
            # Fruits
            for fruit in self.fruits:
                fruit.draw(self.screen, self.assets, self.GAME_LEFT, self.GAME_TOP)
            
            # Snake
            if self.snake:
                self.snake.draw(self.screen, self.assets, self.GAME_LEFT, self.GAME_TOP)
            
            # Particles
            self.particles.draw(self.screen, self.GAME_LEFT, self.GAME_TOP)
            
            # HUD
            if self.snake:
                self.ui_manager.draw_hud(self.screen, self.score, self.snake.speed,
                                        self.settings.current_difficulty,
                                        self.settings.lives, lang_code)
            
            # Pause overlay
            if self.state == GameState.PAUSED:
                self.pause_menu.draw(self.screen, lang_code)
            
            # Quiz overlay
            if self.state in (GameState.QUIZ, GameState.QUIZ_RESULT):
                self.quiz_ui.draw(self.screen, lang_code)
        
        elif self.state == GameState.GAME_OVER:
            self.game_over_menu.draw(self.screen, lang_code)
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time
            dt = min(dt, 1.0 / 30.0)  # Cap dt
            
            self.handle_events()
            self.update(dt)
            self.draw()
            
            if self.state == GameState.PLAYING and self.snake:
                self.clock.tick(self.snake.speed)
            else:
                self.clock.tick(60)
        
        pygame.quit()
        sys.exit()


def main():
    pygame.init()
    game = CyberSnakeGame()
    game.run()


if __name__ == "__main__":
    main()