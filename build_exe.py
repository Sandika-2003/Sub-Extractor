import os
import sys
import subprocess

project_root = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(project_root, "assets")
icon_ico = os.path.join(assets_dir, "app_icon.ico")
main_script = os.path.join(project_root, "main.py")

python_exe = sys.executable

cmd = [
    python_exe, "-m", "PyInstaller",
    "--name=SubExtractor",
    "--noconsole",
    "--onefile",
    f"--icon={icon_ico}",
    f"--paths={project_root}",
    f"--paths={os.path.join(project_root, 'src')}",
    f"--add-data={assets_dir};assets/",
    f"--add-data={os.path.join(project_root, 'src')};src/",
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

print("Running PyInstaller build command for SubExtractor:")
subprocess.run(cmd, cwd=project_root, check=True)
print("[OK] Build completed successfully! Standalone executable is in the 'dist/' folder as SubExtractor.exe.")