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

_single_instance_mutex = None


def enforce_single_instance():
    """
    Guarantees that only a single instance of Sub Extractor runs at a time.
    If an existing instance is found, it brings that instance to the foreground
    and immediately terminates the new instance.
    """
    global _single_instance_mutex
    ERROR_ALREADY_EXISTS = 183
    mutex_name = "Global\\SubExtractor_SingleInstance_Mutex_v1"

    _single_instance_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == ERROR_ALREADY_EXISTS:
        try:
            import win32gui
            import win32con
            import win32process
            import win32api

            target_hwnd = None

            def enum_cb(hwnd, _):
                nonlocal target_hwnd
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "Sub Extractor Studio" in title or (title.startswith("Sub Extractor") and "Setup" not in title and "Uninstall" not in title):
                        target_hwnd = hwnd
                        return False
                return True

            win32gui.EnumWindows(enum_cb, None)

            if target_hwnd:
                if win32gui.IsIconic(target_hwnd):
                    win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
                else:
                    win32gui.ShowWindow(target_hwnd, win32con.SW_SHOW)

                cur_tid = win32api.GetCurrentThreadId()
                target_tid, _ = win32process.GetWindowThreadProcessId(target_hwnd)
                if cur_tid != target_tid:
                    ctypes.windll.user32.AttachThreadInput(cur_tid, target_tid, True)

                ctypes.windll.user32.SetForegroundWindow(target_hwnd)
                ctypes.windll.user32.SetFocus(target_hwnd)

                if cur_tid != target_tid:
                    ctypes.windll.user32.AttachThreadInput(cur_tid, target_tid, False)
        except Exception:
            pass

        sys.exit(0)


try:
    from src.gui import run_app
except ImportError:
    from gui import run_app

if __name__ == "__main__":
    enforce_single_instance()
    run_app()