"""
Application Entry Point for PotPlayer Subtitle Extractor & Multi-Player Manager.
"""

import os
import sys
import ctypes

# Enable high-DPI awareness on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Ensure correct paths for both normal run and PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

src_dir = os.path.join(base_dir, "src")
if os.path.isdir(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from src.gui import run_app
except ImportError:
    from gui import run_app

if __name__ == "__main__":
    run_app()