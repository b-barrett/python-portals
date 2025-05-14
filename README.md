# Python Portals

**A fast-paced, feature-rich Snake game written in Python using Pygame**

---

## 🎮 How to Play

* Use arrow keys to move your snake
* Eat food to grow and score points
* 4 foods per level unlocks a portal
* Enter portals to advance to the next level
* Snake speed increases each level
* Food value increases each level
* Click blue squares for bonus points
* Press `P` to pause anytime
* Game ends when:

  * Snake hits the wall
  * Snake runs into its own tail
* Reach the final portal to win the game!

---

## 🚀 Getting Started

### Option 1: Local Play (No Git, no sync)

#### ✅ Requirements

* Python 3.10 or 3.11 (Python 3.12 works too, but slightly newer)
* Pygame 2.6.1+

#### 🎯 Pip Users

```bash
# Set up virtual environment (one-time)
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install requirements
pip install -r requirements.txt

# Run the game
python snake.py
```

#### 🎯 Conda Users

```bash
# Create and activate conda env
conda create -n portals python=3.10
conda activate portals

# Install requirements
pip install -r requirements.txt

# Run the game
python snake.py
```

---

## 🧰 Setup (Developers Only)

### ✅ 1. Clone the Repo

```bash
git clone https://github.com/YOUR_USERNAME/python-portals.git
cd python-portals
```

### 🔁 2. Leaderboard Sync

If you're inside a cloned Git repo, the game will:

* Pull the latest `leaderboard.json` at game start
* Push your updated score at game end

If you're running the zipped version or have no `.git` folder:

* Scores will save *locally* only

---

## 🗃️ Project Structure

```
python-portals/
├── assets/
│   ├── backgrounds/
│   ├── fonts/
│   ├── food/
│   ├── leaderboard/
│   ├── music/
│   ├── portals/
│   ├── snakeskins/
│   └── sounds/
├── requirements.txt
├── snake.py
├── README.md
└── .gitignore
```

---

## 🚫 .gitignore Example

```
__pycache__/
*.pyc
*.pyo
*.save
.DS_Store
```

---

## 📦 Packaging (Coming Soon)

* [ ] Convert to `.exe` (Windows) or `.app` (Mac) using `pyinstaller` or `py2app`
* [ ] Distribute zipped game folder for non-dev testers

---

## ❤️ Credits

* Built with Python + Pygame
* Font: VT323
* Music & sound credits listed in README\_audio.md
* Developed by Thomas Christol with love, testing, and portals 🌀

---

## 🐍 Python Portals

**A game of reflex, precision, and bonus snacks. Good luck.**
