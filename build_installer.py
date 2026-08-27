import os
import sys
import subprocess
import shutil

project_root = r"c:\Users\Sandika\Downloads\Sub_Extractor"
dist_dir = os.path.join(project_root, "dist")
build_dir = os.path.join(project_root, "build")
assets_dir = os.path.join(project_root, "assets")
icon_ico = os.path.join(assets_dir, "app_icon.ico")
icon_png = os.path.join(assets_dir, "app_icon.png")

python_exe = sys.executable

# 1. Build Uninstall.exe
print("\n--- 1/3: Building Uninstall.exe ---")
uninst_cmd = [
    python_exe, "-m", "PyInstaller",
    "--name=Uninstall",
    "--noconsole",
    "--onefile",
    "--uac-admin",
    f"--icon={icon_ico}",
    f"--paths={project_root}",
    f"--paths={os.path.join(project_root, 'src')}",
    f"--add-data={assets_dir};assets/",
    "--collect-all=customtkinter",
    "--hidden-import=customtkinter",
    "--hidden-import=PIL",
    "--hidden-import=winreg",
    os.path.join(project_root, "src", "uninstaller.py")
]
subprocess.run(uninst_cmd, cwd=project_root, check=True)

# 2. Build SubExtractor.exe
print("\n--- 2/3: Building SubExtractor.exe ---")
main_cmd = [
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
    os.path.join(project_root, "main.py")
]
subprocess.run(main_cmd, cwd=project_root, check=True)

# Verify dist binaries
main_exe = os.path.join(dist_dir, "SubExtractor.exe")
uninst_exe = os.path.join(dist_dir, "Uninstall.exe")

if not os.path.isfile(main_exe) or not os.path.isfile(uninst_exe):
    raise FileNotFoundError("Binaries were not compiled properly!")

# 3. Build Setup Installer: SubExtractor_Setup.exe
print("\n--- 3/3: Building SubExtractor_Setup.exe ---")
setup_cmd = [
    python_exe, "-m", "PyInstaller",
    "--name=SubExtractor_Setup",
    "--noconsole",
    "--onefile",
    "--uac-admin",
    f"--icon={icon_ico}",
    f"--paths={project_root}",
    f"--paths={os.path.join(project_root, 'src')}",
    f"--add-data={main_exe};.",
    f"--add-data={uninst_exe};.",
    f"--add-data={assets_dir};assets/",
    "--collect-all=customtkinter",
    "--hidden-import=customtkinter",
    "--hidden-import=PIL",
    "--hidden-import=win32com",
    "--hidden-import=win32com.client",
    "--hidden-import=winreg",
    os.path.join(project_root, "src", "installer.py")
]
subprocess.run(setup_cmd, cwd=project_root, check=True)

print("\n========================================================")
print("[OK] ALL PACKAGES COMPILED SUCCESSFULLY!")
print(f"1. Main App:        {main_exe}")
print(f"2. Uninstaller:     {uninst_exe}")
print(f"3. Windows Setup:   {os.path.join(dist_dir, 'SubExtractor_Setup.exe')}")
print("========================================================")