import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importing app will execute the Streamlit app since it runs at top-level
import app  # noqa: F401

if __name__ == "__main__":
    # Nothing needed; Streamlit runs on import
    pass
