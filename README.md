# Python Portals

#### Pip Users

```bash
# Set up virtual environment (one-time)
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install requirements
pip install -r requirements.txt

# Run the game
python snake.py
```

#### Conda Users

```bash
# Create and activate conda env
conda create -n portals python=3.10
conda activate portals

# Install requirements
pip install -r requirements.txt

# Run the game
python snake.py
```

### Project Structure

```
python-portals/
├── assets/
│   ├── backgrounds/
│   ├── fonts/
│   ├── food/
│   ├── leaderboard/leaderboard.json, player1.json, player2.json, ...
│   ├── music/
│   ├── portals/
│   ├── snakeskins/
│   └── sounds/
│   └── sprite-sheets/
├── convertorAndExtractorScripts/
├── README.md
├── requirements.txt
├── snake.py
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
