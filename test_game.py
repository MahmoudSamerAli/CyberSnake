"""
Unit tests and smoke tests for CyberSnake
Run with: py -m pytest test_game.py -v
Or: py test_game.py
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add game directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import game modules (without initializing pygame display)
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame
pygame.init()
pygame.display.set_mode((1, 1))  # Minimal display

from CyberSnake_final import (
    GameSettings, FontManager, AssetManager, QuestionManager,
    Snake, Fruit, Particle, ParticleSystem, UIManager,
    shape_arabic_text, is_arabic, DIFFICULTY_SETTINGS,
    TRANSLATIONS, LANGUAGES, LANG_CODES, GRID_SIZE,
    GAME_WIDTH, GAME_HEIGHT, MAX_LIVES
)


class TestGameSettings(unittest.TestCase):
    """Test GameSettings class"""
    
    def test_default_values(self):
        settings = GameSettings()
        self.assertEqual(settings.current_language, "English")
        self.assertEqual(settings.current_difficulty, "Easy")
        self.assertEqual(settings.lives, MAX_LIVES)
    
    def test_lang_code_property(self):
        settings = GameSettings()
        self.assertEqual(settings.lang_code, "en")
        settings.current_language = "Arabic"
        self.assertEqual(settings.lang_code, "ar")
    
    def test_difficulty_config_property(self):
        settings = GameSettings()
        config = settings.difficulty_config
        self.assertIn("base_speed", config)
        self.assertIn("spawn_rate", config)
        self.assertIn("wrap_walls", config)
        self.assertIn("self_collision", config)
        self.assertIn("speed_increment", config)
        self.assertIn("question_time", config)
    
    def test_is_arabic_property(self):
        settings = GameSettings()
        self.assertFalse(settings.is_arabic)
        settings.current_language = "Arabic"
        self.assertTrue(settings.is_arabic)


class TestArabicShaping(unittest.TestCase):
    """Test Arabic text shaping"""
    
    def test_is_arabic_detection(self):
        self.assertTrue(is_arabic("مرحبا"))
        self.assertTrue(is_arabic("Hello مرحبا"))
        self.assertFalse(is_arabic("Hello World"))
        self.assertFalse(is_arabic("123"))
    
    def test_shape_arabic_text(self):
        # Should not crash
        result = shape_arabic_text("مرحبا")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), len("مرحبا"))
        
        # English should pass through
        result = shape_arabic_text("Hello")
        self.assertEqual(result, "Hello")


class TestFontManager(unittest.TestCase):
    """Test FontManager"""
    
    def setUp(self):
        self.font_manager = FontManager()
    
    def test_fonts_loaded(self):
        self.assertIn("en", self.font_manager._fonts)
        self.assertIn("en_large", self.font_manager._fonts)
        self.assertIn("en_title", self.font_manager._fonts)
        self.assertIn("ar", self.font_manager._fonts)
    
    def test_render_english(self):
        surf = self.font_manager.render("Test", "en", (255, 255, 255))
        self.assertIsInstance(surf, pygame.Surface)
        self.assertGreater(surf.get_width(), 0)
    
    def test_render_arabic(self):
        surf = self.font_manager.render("اختبار", "ar", (255, 255, 255))
        self.assertIsInstance(surf, pygame.Surface)
        self.assertGreater(surf.get_width(), 0)
    
    def test_caching(self):
        # First render
        surf1 = self.font_manager.render("Test", "en", (255, 255, 255))
        # Second render should return cached
        surf2 = self.font_manager.render("Test", "en", (255, 255, 255))
        self.assertIs(surf1, surf2)
    
    def test_clear_cache(self):
        self.font_manager.render("Test", "en", (255, 255, 255))
        self.assertGreater(len(self.font_manager._text_cache), 0)
        self.font_manager.clear_cache()
        self.assertEqual(len(self.font_manager._text_cache), 0)


class TestAssetManager(unittest.TestCase):
    """Test AssetManager"""
    
    def setUp(self):
        self.assets = AssetManager()
    
    def test_grass_surface(self):
        self.assertIsNotNone(self.assets.grass_surface)
        self.assertEqual(self.assets.grass_surface.get_size(), (GAME_WIDTH, GAME_HEIGHT))
    
    def test_fruit_surfaces(self):
        for fruit_type in ['apple', 'banana', 'grapes', 'orange', 'strawberry']:
            self.assertIn(fruit_type, self.assets.fruit_surfaces)
            surf = self.assets.fruit_surfaces[fruit_type]
            self.assertEqual(surf.get_size(), (GRID_SIZE, GRID_SIZE))
    
    def test_heart_surface(self):
        self.assertIsNotNone(self.assets.heart_surface)
    
    def test_snake_surfaces(self):
        self.assertIsNotNone(self.assets.snake_head_surf)
        self.assertIsNotNone(self.assets.snake_body_surf)
        self.assertIsNotNone(self.assets.snake_body_alt_surf)


class TestQuestionManager(unittest.TestCase):
    """Test QuestionManager"""
    
    def setUp(self):
        self.qm = QuestionManager()
    
    def test_questions_loaded(self):
        for diff in DIFFICULTY_SETTINGS.keys():
            self.assertIn(diff, self.qm._questions)
            self.assertIn("en", self.qm._questions[diff])
            self.assertIn("ar", self.qm._questions[diff])
            self.assertGreater(len(self.qm._questions[diff]["en"]), 0)
            self.assertGreater(len(self.qm._questions[diff]["ar"]), 0)
    
    def test_get_question(self):
        q = self.qm.get_question("Easy", "en")
        self.assertIn("question", q)
        self.assertIn("options", q)
        self.assertIn("answer", q)
        self.assertIsInstance(q["options"], list)
        self.assertGreater(len(q["options"]), 0)
        self.assertGreaterEqual(q["answer"], 0)
        self.assertLess(q["answer"], len(q["options"]))
    
    def test_question_cycling(self):
        # Get all questions for a difficulty
        questions = []
        for _ in range(10):
            q = self.qm.get_question("Easy", "en")
            questions.append(q["question"])
        # Should have cycled or have unique questions
        self.assertGreater(len(set(questions)), 1)


class TestSnake(unittest.TestCase):
    """Test Snake entity"""
    
    def setUp(self):
        self.snake = Snake("Easy")
    
    def test_initial_state(self):
        self.assertEqual(len(self.snake.positions), 3)
        self.assertEqual(self.snake.direction, (0, -GRID_SIZE))
        self.assertEqual(self.snake.length, 3)
        self.assertEqual(self.snake.speed, 6.0)  # Easy base_speed
    
    def test_move_easy_wraps(self):
        # Move to edge
        self.snake.positions = [(0, 0), (0, GRID_SIZE), (0, 2 * GRID_SIZE)]
        self.snake.direction = (-GRID_SIZE, 0)
        alive = self.snake.move()
        self.assertTrue(alive)
        # Should wrap around
        self.assertEqual(self.snake.positions[0][0], GAME_WIDTH - GRID_SIZE)
    
    def test_move_medium_dies_on_wall(self):
        snake = Snake("Medium")
        snake.positions = [(0, 0), (0, GRID_SIZE), (0, 2 * GRID_SIZE)]
        snake.direction = (-GRID_SIZE, 0)
        alive = snake.move()
        self.assertFalse(alive)
    
    def test_self_collision_hard(self):
        snake = Snake("Hard")
            # Create a snake where moving down would hit its body
            snake.positions = [(100, 100), (100, 120), (120, 120), (120, 100)]
            snake.direction = (0, GRID_SIZE)  # Moving down into body at (100, 120)
        alive = snake.move()
        self.assertFalse(alive)
    
    def test_no_self_collision_easy(self):
        snake = Snake("Easy")
        snake.positions = [(100, 100), (120, 100), (120, 120), (100, 120), (100, 100)]
        snake.direction = (0, -GRID_SIZE)
        alive = snake.move()
        self.assertTrue(alive)  # Easy ignores self-collision
    
    def test_grow(self):
        initial_len = len(self.snake.positions)
        self.snake.grow()
        self.assertEqual(len(self.snake.positions), initial_len + 1)
    
    def test_set_direction_prevents_180(self):
        self.snake.set_direction((0, GRID_SIZE))  # Try to reverse
        self.assertEqual(self.snake.direction, (0, -GRID_SIZE))  # Should not change
        
        self.snake.set_direction((GRID_SIZE, 0))  # Valid turn
        self.assertEqual(self.snake.direction, (GRID_SIZE, 0))
    
    def test_increase_speed(self):
        initial_speed = self.snake.speed
        self.snake.increase_speed()
        self.assertGreater(self.snake.speed, initial_speed)
        # Cap at MAX_SNAKE_SPEED
        for _ in range(100):
            self.snake.increase_speed()
        self.assertLessEqual(self.snake.speed, 25)


class TestFruit(unittest.TestCase):
    """Test Fruit entity"""
    
    def setUp(self):
        self.qm = QuestionManager()
        self.fruit = Fruit([], [], "Easy", "en", self.qm)
    
    def test_initialization(self):
        self.assertIn(self.fruit.type, ['apple', 'banana', 'grapes', 'orange', 'strawberry'])
        self.assertIn("question", self.fruit.question_data)
        self.assertIn("options", self.fruit.question_data)
        self.assertIn("answer", self.fruit.question_data)
    
    def test_random_pos_avoids_snake(self):
        snake_pos = [(100, 100), (120, 100), (140, 100)]
        fruit = Fruit(snake_pos, [], "Easy", "en", self.qm)
        self.assertNotIn(fruit.position, snake_pos)
    
    def test_update(self):
        # Should not crash
        self.fruit.update(0.016)  # ~60 FPS
        self.fruit.update(0.1)


class TestParticleSystem(unittest.TestCase):
    """Test Particle system"""
    
    def setUp(self):
        self.ps = ParticleSystem()
    
    def test_add_explosion(self):
        self.ps.add_explosion(100, 100, (255, 0, 0), 10)
        self.assertEqual(len(self.ps.particles), 10)
    
    def test_add_collect(self):
        self.ps.add_collect(100, 100, (0, 255, 0), 5)
        self.assertEqual(len(self.ps.particles), 5)
    
    def test_update_removes_dead(self):
        self.ps.add_explosion(100, 100, (255, 0, 0), 10)
        # Update with large dt to kill particles
        self.ps.update(2.0)
        self.assertEqual(len(self.ps.particles), 0)
    
    def test_particle_lifecycle(self):
        p = Particle(100, 100, 10, 10, 1.0, 1.0, (255, 0, 0), 5)
        alive = p.update(0.5)
        self.assertTrue(alive)
        alive = p.update(0.6)
        self.assertFalse(alive)


class TestUIManager(unittest.TestCase):
    """Test UIManager"""
    
    def setUp(self):
        self.font_manager = FontManager()
        self.assets = AssetManager()
        self.ui = UIManager(self.font_manager, self.assets)
    
    def test_draw_text(self):
        surf = pygame.Surface((800, 600))
        self.ui.draw_text(surf, "Test", (400, 300), (255, 255, 255), "en")
        # Should not crash
    
    def test_hud_caching(self):
        surf = pygame.Surface((800, 600))
        self.ui.draw_hud(surf, 10, 6.0, "Easy", 3, "en")
        self.ui.draw_hud(surf, 10, 6.0, "Easy", 3, "en")  # Should use cache
        self.ui.draw_hud(surf, 11, 6.0, "Easy", 3, "en")  # Should rebuild


class TestDifficultySettings(unittest.TestCase):
    """Test difficulty configuration"""
    
    def test_all_difficulties_have_required_keys(self):
        required = ["base_speed", "spawn_rate", "wrap_walls", "self_collision", "speed_increment", "question_time"]
        for diff, config in DIFFICULTY_SETTINGS.items():
            for key in required:
                self.assertIn(key, config, f"{diff} missing {key}")
    
    def test_speed_progression(self):
        self.assertLess(DIFFICULTY_SETTINGS["Easy"]["base_speed"], 
                       DIFFICULTY_SETTINGS["Medium"]["base_speed"])
        self.assertLess(DIFFICULTY_SETTINGS["Medium"]["base_speed"], 
                       DIFFICULTY_SETTINGS["Hard"]["base_speed"])
    
    def test_question_time_decreases(self):
        self.assertGreater(DIFFICULTY_SETTINGS["Easy"]["question_time"],
                          DIFFICULTY_SETTINGS["Medium"]["question_time"])
        self.assertGreater(DIFFICULTY_SETTINGS["Medium"]["question_time"],
                          DIFFICULTY_SETTINGS["Hard"]["question_time"])


class TestTranslations(unittest.TestCase):
    """Test translations completeness"""
    
    def test_all_keys_present(self):
        en_keys = set(TRANSLATIONS["en"].keys())
        ar_keys = set(TRANSLATIONS["ar"].keys())
        self.assertEqual(en_keys, ar_keys, "Translation keys mismatch")
    
    def test_no_empty_values(self):
        for lang in ["en", "ar"]:
            for key, value in TRANSLATIONS[lang].items():
                if isinstance(value, list):
                    # Controls is a list of strings
                    self.assertGreater(len(value), 0, f"Empty list: {lang}.{key}")
                    for item in value:
                        self.assertIsInstance(item, str)
                        self.assertGreater(len(item), 0, f"Empty item in {lang}.{key}")
                else:
                    self.assertIsInstance(value, str)
                    self.assertGreater(len(value), 0, f"Empty translation: {lang}.{key}")


class SmokeTest(unittest.TestCase):
    """Smoke test - run game initialization"""
    
    def test_game_initialization(self):
        """Test that game can be created without errors"""
        from CyberSnake_final import CyberSnakeGame
        
        # This should not raise any exceptions
        game = CyberSnakeGame()
        
        # Check all components initialized
        self.assertIsNotNone(game.settings)
        self.assertIsNotNone(game.font_manager)
        self.assertIsNotNone(game.assets)
        self.assertIsNotNone(game.question_manager)
        self.assertIsNotNone(game.ui_manager)
        self.assertIsNotNone(game.particles)
        self.assertIsNotNone(game.main_menu)
        self.assertIsNotNone(game.settings_menu)
        self.assertIsNotNone(game.controls_menu)
        self.assertIsNotNone(game.pause_menu)
        self.assertIsNotNone(game.game_over_menu)
        self.assertIsNotNone(game.quiz_ui)
        
        # Clean up
        pygame.quit()


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestGameSettings,
        TestArabicShaping,
        TestFontManager,
        TestAssetManager,
        TestQuestionManager,
        TestSnake,
        TestFruit,
        TestParticleSystem,
        TestUIManager,
        TestDifficultySettings,
        TestTranslations,
        SmokeTest,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)