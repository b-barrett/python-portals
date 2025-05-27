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
│   ├── leaderboard/
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

### Credits

* Built with Python + Pygame
* Font: VT323
* Asset credits listed in README/licensing.md