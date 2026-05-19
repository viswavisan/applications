import sys
import os

# Add the project root directory to the Python path to allow pytest to find the 'fit_mafia' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
