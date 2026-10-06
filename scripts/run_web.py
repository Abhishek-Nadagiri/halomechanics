import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import run_web_app

if __name__ == "__main__":
    run_web_app()
