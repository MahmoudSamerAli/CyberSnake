# CyberSnake - Cybersecurity Quiz Snake Game

A modern, educational snake game that teaches cybersecurity concepts through interactive quizzes. Built with Python and Pygame.

## Features

- **Classic Snake Gameplay** - Navigate the snake to eat fruits
- **Cybersecurity Quizzes** - Each fruit triggers a multiple-choice question
- **Three Difficulty Levels**:
  - **Easy** - Wall wrapping, no self-collision, 20s per question
  - **Medium** - Wall collision, self-collision enabled, 15s per question
  - **Hard** - Wall wrapping, self-collision enabled, 10s per question
- **Bilingual Support** - Full English and Arabic (RTL) support
- **Question Timer** - Unpauseable countdown per question
- **Visual Effects** - Particle explosions, pulsing fruits, smooth animations
- **Lives System** - 3 lives, lose one on wrong answer or collision
- **High Score Tracking** - Score increases with correct answers

## Screenshots

*Gameplay with quiz overlay and timer bar*

## Installation

### Prerequisites
- Python 3.8+
- pip

### Required Packages
```bash
pip install pygame arabic-reshaper python-bidi
```

### Run the Game
```bash
python CyberSnake_final.py
```

## Controls

| Key | Action |
|-----|--------|
| ↑ ↓ ← → | Move snake |
| ESC | Pause/Resume |
| ↑/↓ + Enter | Navigate menus/select answers |

## Game Rules

1. **Eat fruits** to trigger cybersecurity questions
2. **Answer correctly** → Snake grows, speed increases, score +1
3. **Answer incorrectly** → Lose a life
4. **Hit wall (Medium)** → Lose a life, snake rewinds
5. **Hit self (Medium/Hard)** → Lose a life, snake rewinds
6. **Time runs out** → Counts as wrong answer
7. **Lose all 3 lives** → Game Over

## Project Structure

```
CyberSnake/
├── CyberSnake_final.py    # Main game file
├── test_game.py           # Unit tests
├── Q/                     # Question files (English + Arabic)
│   ├── EasyQ.json
│   ├── EasyQ_ar.json
│   ├── MedQ.json
│   ├── MedQ_ar.json
│   ├── HardQ.json
│   └── HardQ_ar.json
└── README.md
```

## Question Format

Questions are stored in JSON format:
```json
{
  "question": "What is a strong password?",
  "options": ["Password123", "pet name", "Tr0ub4dor&3", "12345678"],
  "answer": 2
}
```

## Arabic Support

The game uses `arabic-reshaper` and `python-bidi` for proper RTL text rendering with connected letters (ligatures).

## Testing

Run unit tests:
```bash
python test_game.py
```

Or with pytest:
```bash
pytest test_game.py -v
```

## Architecture

- **State Machine** - Clean separation of game states (Menu, Playing, Quiz, Paused, Game Over)
- **Asset Pre-rendering** - Grass, fruits, snake segments cached as surfaces
- **Font Caching** - Rendered text cached for performance
- **Delta-time Updates** - Frame-independent timing for smooth animations
- **Particle System** - Visual feedback for correct/incorrect answers

## Difficulty Settings

| Setting | Easy | Medium | Hard |
|---------|------|--------|------|
| Base Speed | 6 FPS | 9 FPS | 12 FPS |
| Fruit Spawn Rate | 25 frames | 18 frames | 12 frames |
| Wall Wrapping | ✅ | ❌ | ✅ |
| Self Collision | ❌ | ✅ | ✅ |
| Speed Increment | +0.3 | +0.4 | +0.5 |
| Question Time | 20s | 15s | 10s |

## License

MIT License - Feel free to use for educational purposes.

## Credits

Developed as a cybersecurity education project at AASTMT.