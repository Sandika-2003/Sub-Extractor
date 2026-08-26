"""
Build standalone executable using PyInstaller.
"""

import os
import sys
import subprocess
import customtkinter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "assets", "app_icon.ico")
main_script = os.path.join(current_dir, "main.py")
src_path = os.path.join(current_dir, "src")
ctk_path = os.path.dirname(customtkinter.__file__)

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--name=PotPlayerSubExtractor",
    "--noconsole",
    "--onefile",
    f"--icon={icon_path}",
    f"--paths={current_dir}",
    f"--paths={src_path}",
    f"--add-data={ctk_path};customtkinter/",
    f"--add-data={os.path.join(current_dir, 'assets')};assets/",
    f"--add-data={src_path};src/",
    "--collect-all=customtkinter",
    "--hidden-import=src",
    "--hidden-import=src.gui",
    "--hidden-import=src.potplayer_controller",
    "--hidden-import=gui",
    "--hidden-import=potplayer_controller",
    "--hidden-import=pycaw",
    "--hidden-import=comtypes",
    "--hidden-import=psutil",
    "--hidden-import=PIL",
    "--hidden-import=win32gui",
    "--hidden-import=win32con",
    "--hidden-import=win32api",
    "--hidden-import=win32process",
    "--hidden-import=win32com",
    "--hidden-import=win32com.client",
    main_script
]

print("Running PyInstaller build command:")
print(" ".join(cmd))
res = subprocess.run(cmd, cwd=current_dir)
if res.returncode == 0:
    print("\n[OK] Build completed successfully! Standalone executable is in the 'dist/' folder.")
else:
    print(f"\n[ERROR] Build failed with return code {res.returncode}")