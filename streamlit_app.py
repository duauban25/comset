import os
import sys
from pathlib import Path

# Add the current directory to the path so local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main app
from app import main

if __name__ == "__main__":
    main()
