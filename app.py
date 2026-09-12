import sys
import os

# Auto-resolve project root directory in sys.path for Hugging Face Spaces & Streamlit
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import and execute Streamlit dashboard application
import dashboard.app
