"""
Sub Extractor - Windows Setup Installer
Modern GUI Setup Wizard that installs Sub Extractor to C:\Program Files\Sub Extractor.
"""

import os
import sys
import time
import winreg
import shutil
import subprocess
import threading
import win32com.client
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_BG_DARK = "#0d1117"
COLOR_CARD_BG = "#161b22"
COLOR_CARD_BORDER = "#30363d"
COLOR_ACCENT_CYAN = "#00d2ff"
COLOR_ACCENT_BLUE = "#0078d4"
COLOR_ACCENT_GREEN = "#00e676"
COLOR_TEXT_MAIN = "#f0f6fc"
COLOR_TEXT_MUTED = "#8b949e"

APP_NAME = "Sub Extractor"
APP_VERSION = "1.0.0"
PUBLISHER = "Sandika"
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SubExtractor"


def get_default_install_dir():
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    return os.path.join(program_files, "Sub Extractor")


def get_bundle_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_shortcut(target_exe, shortcut_path, icon_path=None, description=""):
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target_exe
        shortcut.WorkingDirectory = os.path.dirname(target_exe)
        shortcut.Description = description
        if icon_path and os.path.isfile(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.Save()
    except Exception as e:
        print(f"Error creating shortcut {shortcut_path}: {e}")


def register_uninstall(install_dir, exe_path, uninstaller_path, icon_path):
    for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.CreateKey(root_key, REG_KEY_PATH) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f"{icon_path},0")
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            break
        except Exception:
            continue


class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Setup - Sub Extractor")
        self.geometry("560x520")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG_DARK)

        self.install_dir_var = ctk.StringVar(value=get_default_install_dir())
        self.create_desktop_sc = ctk.BooleanVar(value=True)
        self.create_start_sc = ctk.BooleanVar(value=True)
        self.launch_after = ctk.BooleanVar(value=True)

        self.bundle_dir = get_bundle_dir()
        self._setup_icon()
        self._create_widgets()

    def _setup_icon(self):
        ico_path = os.path.join(self.bundle_dir, "assets", "app_icon.ico")
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG, corner_radius=16, border_width=1, border_color=COLOR_CARD_BORDER)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="⚡ Sub Extractor Setup",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_ACCENT_CYAN,
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Welcome to the Sub Extractor Setup Wizard.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Install Directory Frame
        dir_frame = ctk.CTkFrame(main_frame, fg_color="#121820", corner_radius=10, border_width=1, border_color="#1f2937")
        dir_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            dir_frame,
            text="Destination Location:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
        ).pack(anchor="w", padx=14, pady=(10, 4))

        path_inner = ctk.CTkFrame(dir_frame, fg_color="transparent")
        path_inner.pack(fill="x", padx=14, pady=(0, 10))

        path_entry = ctk.CTkEntry(
            path_inner,
            textvariable=self.install_dir_var,
            font=ctk.CTkFont(size=11),
            fg_color="#0d1117",
            border_color=COLOR_CARD_BORDER,
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            path_inner,
            text="Browse...",
            width=75,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.browse_dest,
        ).pack(side="right")

        # Options
        opt_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        opt_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            opt_frame,
            text="Select Additional Tasks:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkCheckBox(
            opt_frame,
            text="Create a Desktop shortcut",
            variable=self.create_desktop_sc,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
        ).pack(anchor="w", pady=3)

        ctk.CTkCheckBox(
            opt_frame,
            text="Create a Start Menu shortcut",
            variable=self.create_start_sc,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
        ).pack(anchor="w", pady=3)

        ctk.CTkCheckBox(
            opt_frame,
            text="Launch Sub Extractor after install",
            variable=self.launch_after,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
        ).pack(anchor="w", pady=3)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            height=8,
            corner_radius=4,
            fg_color="#21262d",
            progress_color=COLOR_ACCENT_CYAN,
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(15, 4))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready to install",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 10))

        # Buttons
        btn_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 15), side="bottom")

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.destroy,
            width=90,
            height=36,
        )
        self.btn_cancel.pack(side="right", padx=(10, 0))

        self.btn_install = ctk.CTkButton(
            btn_row,
            text="Install",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#0f263d",
            hover_color="#183b5e",
            text_color="#7dd3fc",
            border_color="#0284c7",
            border_width=2,
            corner_radius=10,
            command=self.start_installation,
            width=110,
            height=36,
        )
        self.btn_install.pack(side="right")

    def browse_dest(self):
        chosen = filedialog.askdirectory(title="Select Destination Folder")
        if chosen:
            self.install_dir_var.set(os.path.join(chosen, "Sub Extractor"))

    def start_installation(self):
        target_dir = self.install_dir_var.get().strip()
        if not target_dir:
            messagebox.showerror("Error", "Please specify a valid destination folder.")
            return

        self.btn_install.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")

        def worker():
            try:
                self.status_label.configure(text="Creating destination folder...")
                self.progress_bar.set(0.1)
                os.makedirs(target_dir, exist_ok=True)
                time.sleep(0.3)

                # Copy payload files
                self.status_label.configure(text="Extracting application files...")
                self.progress_bar.set(0.3)

                assets_target = os.path.join(target_dir, "assets")
                os.makedirs(assets_target, exist_ok=True)

                # Find source files
                files_to_copy = [
                    ("SubExtractor.exe", target_dir),
                    ("Uninstall.exe", target_dir),
                    (os.path.join("assets", "app_icon.ico"), assets_target),
                    (os.path.join("assets", "app_icon.png"), assets_target),
                ]

                for src_rel, dest_folder in files_to_copy:
                    src_full = os.path.join(self.bundle_dir, src_rel)
                    if os.path.isfile(src_full):
                        shutil.copy2(src_full, dest_folder)

                self.progress_bar.set(0.6)
                time.sleep(0.3)

                main_exe = os.path.join(target_dir, "SubExtractor.exe")
                uninstaller_exe = os.path.join(target_dir, "Uninstall.exe")
                icon_file = os.path.join(assets_target, "app_icon.ico")

                # Shortcuts
                self.status_label.configure(text="Creating shortcuts...")
                self.progress_bar.set(0.8)

                if self.create_desktop_sc.get():
                    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
                    sc_path = os.path.join(desktop, "Sub Extractor.lnk")
                    create_shortcut(main_exe, sc_path, icon_file, "Sub Extractor - Embedded Subtitle Extractor")

                if self.create_start_sc.get():
                    appdata = os.environ.get("APPDATA", "")
                    start_menu = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs", "Sub Extractor")
                    os.makedirs(start_menu, exist_ok=True)
                    sc_path = os.path.join(start_menu, "Sub Extractor.lnk")
                    create_shortcut(main_exe, sc_path, icon_file, "Sub Extractor - Embedded Subtitle Extractor")
                    uninst_sc = os.path.join(start_menu, "Uninstall Sub Extractor.lnk")
                    create_shortcut(uninstaller_exe, uninst_sc, icon_file, "Uninstall Sub Extractor")

                # Register in Windows Add/Remove Programs
                self.status_label.configure(text="Registering Windows uninstaller...")
                self.progress_bar.set(0.95)
                register_uninstall(target_dir, main_exe, uninstaller_exe, icon_file)
                time.sleep(0.3)

                self.progress_bar.set(1.0)
                self.status_label.configure(text="Installation completed successfully!")

                def on_done():
                    messagebox.showinfo("Installation Complete", "Sub Extractor has been successfully installed!")
                    if self.launch_after.get() and os.path.isfile(main_exe):
                        subprocess.Popen([main_exe])
                    self.destroy()

                self.after(0, on_done)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Installation Error", f"Failed to install: {e}"))
                self.after(0, lambda: self.btn_cancel.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()