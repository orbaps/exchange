import os
import sys

print("CONFTEST LOADED", sys.path, "cwd:", os.getcwd())

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

