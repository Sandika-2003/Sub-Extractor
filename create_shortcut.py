"""
Creates a direct Desktop shortcut and Launcher with custom icon for PotPlayer Sub Extractor.
"""

import os
import sys
import win32com.client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def create_shortcuts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "assets", "app_icon.ico")
    main_script = os.path.join(current_dir, "main.py")
    
    python_exe = sys.executable
    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if not os.path.isfile(pythonw_exe):
        pythonw_exe = python_exe

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "PotPlayer Sub Extractor.lnk")

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = pythonw_exe
        shortcut.Arguments = f'"{main_script}"'
        shortcut.WorkingDirectory = current_dir
        if os.path.isfile(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.Description = "PotPlayer Subtitle Extractor & Multi-Player Automation Studio"
        shortcut.Save()
        print(f"[OK] Desktop shortcut successfully created at: {shortcut_path}")
    except Exception as e:
        print(f"[WARN] Could not create shortcut via WScript.Shell: {e}")

    bat_path = os.path.join(current_dir, "Launch.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(f'@echo off\nstart "" "{pythonw_exe}" "{main_script}"\n')
    print(f"[OK] Created {bat_path}")

    vbs_path = os.path.join(current_dir, "Launch.vbs")
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run """{pythonw_exe}"" ""{main_script}""", 0, False\n')
    print(f"[OK] Created {vbs_path}")

if __name__ == "__main__":
    create_shortcuts()