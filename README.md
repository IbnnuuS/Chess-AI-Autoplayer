# ♟️ Chess AI Autoplayer

A powerful, robust Python-based chess bot that plays autonomously directly from your screen! 
It uses **Computer Vision (OpenCV)** to detect the board state and pieces, queries the **Stockfish Engine** to calculate the best moves, and uses **PyAutoGUI** to execute the moves automatically.

## ✨ Features

- **Auto Color Detection**: Automatically detects whether you are playing as White or Black at the start of the game by analyzing the board layout in real-time.
- **Smart Move Tracking**: Instead of heavy, slow piece recognition every turn, the bot uses fast HSV color filtering to detect the exact highlighted squares of your opponent's move.
- **Dynamic Board Flipping**: Seamlessly flips the virtual board logic when playing as Black without relying on error-prone image rotation.
- **Resignation & Game Over Detection**: Automatically detects sudden visual changes (like dimming screens or game-over popups) to stop the engine immediately without waiting for a timeout.
- **Highly Configurable**: Adjust engine depth, move delays, mouse speeds, and click delays directly from one easy `config.py` file.

## 🛠️ Requirements & Installation

1. **Python 3.x** installed on your system.
2. Clone this repository:
   ```bash
   git clone
   cd chess-ai-autoplayer
   ```
3. Install required Python packages:
   ```bash
   pip install opencv-python numpy chess pyautogui mss
   ```
4. **Stockfish Engine**:
   - Download the Stockfish engine executable from the [official website](https://stockfishchess.org/download/).
   - Note the path where you saved it.

## ⚙️ Configuration

Open `config.py` to configure your setup:

1. **Stockfish Path**:
   Set `STOCKFISH_PATH` to the absolute path of your downloaded Stockfish executable.
   ```python
   STOCKFISH_PATH = r"C:\stockfish\stockfish-windows-x86-64-avx2.exe"
   ```

2. **Board Coordinates (Crucial Step)**:
   You **must** calibrate `BOARD_REGION` to match the exact coordinates of the chessboard on your screen `(left, top, width, height)`.
   ```python
   BOARD_REGION = (410, 233, 700, 700) 
   ```

3. **Speed & Delays**:
   You can easily tweak how fast or how "human-like" the bot plays.
   ```python
   ENGINE_DEPTH = 10         # Stockfish depth (higher = significantly stronger but slower)
   MOVE_DELAY = (0.0, 0.2)   # Random delay before moving to seem more human
   MOUSE_DURATION = 0.1      # Mouse travel speed
   CLICK_DELAY = 0.05        # Delay between clicking source and target square
   ```

## 🚀 How to Use

1. Open your browser and start a chess game (e.g., against bots or unrated games locally).
2. Ensure the board is fully visible and not blocked by any other window.
3. Run the bot:
   ```bash
   python main.py
   ```
4. Sit back and watch the AI play! 
5. To stop it mid-game, press `Ctrl + C` in the terminal.

## 🤖 How it Works

1. **Initialization Map (`build_initial_board`)**: Employs heavily tuned template-matching against a pre-loaded `assets` folder of chess pieces to translate the screen to an exact FEN string.
2. **Move Generation (`get_best_move`)**: Feeds the current FEN to Stockfish.
3. **Execution (`move_piece`)**: Clicks the corresponding coordinates on the screen.
4. **Opponent Tracking (`wait_for_opponent_move`)**: Listens to UI highlight color changes (from previous move highlights to new move highlights) to efficiently update the internal board without heavy scanning.

## ⚠️ Disclaimer

This project is built for **educational purposes, learning computer vision, and local AI experimentation**. Please do not use this script to cheat in rated multiplayer games on platforms!
