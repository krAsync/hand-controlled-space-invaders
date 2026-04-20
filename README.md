# Hand-Controlled Retro Games

A gesture-controlled retro arcade game collection powered by MediaPipe hand tracking and machine learning. Control classic games like **Pac-Man**, **Brick Breaker**, and **Space Invaders** using hand gestures captured through your webcam.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.33-green.svg)
![Pygame](https://img.shields.io/badge/Pygame--CE-2.5.7-red.svg)

## Features

- **Real-time hand tracking** using MediaPipe's hand landmark detection
- **Gesture recognition** powered by a trained Random Forest classifier
- **Three classic arcade games** with retro CRT visual effects
- **Dual control support** - play with gestures or keyboard
- **Leaderboard system** to track high scores

## Games

| Game | Description | Controls |
|------|-------------|----------|
| **Pac-Man Maze** | Navigate the maze, collect pellets, avoid ghosts | UP/DOWN/LEFT/RIGHT gestures |
| **Brick Breaker** | Break bricks with bouncing balls, collect power-ups | LEFT/RIGHT gestures |
| **Space Invaders** | Defend Earth from descending alien forces | LEFT/RIGHT to move, gesture 4 to shoot |

## Prerequisites

- Python 3.10 or higher
- Webcam
- Linux/macOS/Windows

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/krAsync/hand-controlled-retro-games.git
   cd hand-controlled-space-invaders
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Game

```bash
python retro.py
```

This launches a fullscreen menu where you can select from three games.

### Controls

**Menu Navigation:**
- `1`, `2`, `3` - Select game directly
- `UP`/`DOWN` arrows + `ENTER` - Navigate and select
- `Q` or `ESC` - Quit

**In-Game:**
- `ESC` - Return to menu
- Hand gestures control movement/actions (displayed on screen)

### Gesture Mappings

| Gesture | Action |
|---------|--------|
| Gesture 1 | UP |
| Gesture 2 | LEFT |
| Gesture 3 | DOWN |
| Gesture 4 | RIGHT / SHOOT |

## Project Structure

```
hand-controlled-space-invaders/
├── retro.py                    # Main game application
├── leaderboard.json            # High scores
├── src/
│   └── MediPipeHandsModule/
│       ├── HandTrackingModule.py    # Hand detection & landmarks
│       ├── GestureEvaluator.py      # Gesture classification
│       └── GestureEvaluatorCNN.py   # Alternative CNN classifier
├── scripts/
│   ├── capture.py              # Record gesture training data
│   ├── train.py                # Train Random Forest model
│   ├── train_cnn.py            # Train CNN model
│   └── eval.py                 # Evaluate model live
├── models/
│   ├── hand_landmarker.task    # MediaPipe hand model
│   └── gesture_model.pkl       # Trained gesture classifier
├── data/
│   └── retro/
│       └── gestures.csv        # Gesture training data
└── assets/                     # Game sprites
```

## Training Custom Gestures

### 1. Capture Training Data

```bash
python scripts/capture.py
```

Press number keys (`0`-`9`) while showing the corresponding gesture to your webcam. The script records hand landmarks to `data/retro/gestures.csv`.

### 2. Train the Model

```bash
python scripts/train.py
```

This trains a Random Forest classifier and saves it to `models/gesture_model.pkl`.

### 3. Evaluate Performance

```bash
python scripts/eval.py
```

Test your trained model in real-time with webcam feedback.

## Technical Details

### Hand Tracking Pipeline

1. **Detection**: MediaPipe extracts 21 hand landmarks per frame
2. **Normalization**: Landmarks are normalized relative to wrist position and bounding box
3. **Classification**: 42 landmark features + handedness fed to Random Forest classifier
4. **Stabilization**: 5-frame majority voting reduces false positives

### Game Engine

- **Pygame-CE** for rendering and input handling
- **Delta-time scaling** for frame-rate independent movement
- **Retro effects**: Scanlines, colored borders, shadow text

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| mediapipe | 0.10.33 | Hand landmark detection |
| opencv-python | 4.13.0 | Video capture & processing |
| pygame-ce | 2.5.7 | Game rendering |
| scikit-learn | 1.8.0 | Gesture classification |
| numpy | 2.4.4 | Numerical operations |
| joblib | 1.5.3 | Model serialization |

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [MediaPipe](https://mediapipe.dev/) for hand tracking technology
- [Pygame-CE](https://pyga.me/) for game development framework
- Classic arcade games for inspiration
