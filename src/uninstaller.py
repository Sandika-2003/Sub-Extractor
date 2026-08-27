"""
Sub Extractor - Dedicated Windows Uninstaller
Safely removes all installed files, shortcuts, and Windows Add/Remove Programs registry entries.
"""

import os
import sys
import time
import winreg
import shutil
import subprocess
import threading
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_BG_DARK = "#0d1117"
COLOR_CARD_BG = "#161b22"
COLOR_ACCENT_RED = "#ff1744"
COLOR_ACCENT_CYAN = "#00d2ff"
COLOR_TEXT_MAIN = "#f0f6fc"
COLOR_TEXT_MUTED = "#8b949e"

APP_NAME = "Sub Extractor"
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SubExtractor"


def get_install_dir():
    """Get the directory where this uninstaller is located."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def remove_registry_entry():
    """Remove Windows Add/Remove Programs registry key."""
    for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            winreg.DeleteKey(root_key, REG_KEY_PATH)
        except Exception:
            pass


def remove_shortcuts():
    """Remove Desktop and Start Menu shortcuts."""
    # Desktop shortcut
    try:
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        s1 = os.path.join(desktop, "Sub Extractor.lnk")
        if os.path.isfile(s1):
            os.remove(s1)
        # Also clean up old name if present
        s1_old = os.path.join(desktop, "PotPlayer Sub Extractor.lnk")
        if os.path.isfile(s1_old):
            os.remove(s1_old)
    except Exception:
        pass

    # Start Menu shortcut
    try:
        appdata = os.environ.get("APPDATA", "")
        start_menu = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")
        s2 = os.path.join(start_menu, "Sub Extractor.lnk")
        if os.path.isfile(s2):
            os.remove(s2)
        s2_folder = os.path.join(start_menu, "Sub Extractor")
        if os.path.isdir(s2_folder):
            shutil.rmtree(s2_folder, ignore_errors=True)
        # Old folder cleanup
        s2_old = os.path.join(start_menu, "PotPlayer Sub Extractor")
        if os.path.isdir(s2_old):
            shutil.rmtree(s2_old, ignore_errors=True)
    except Exception:
        pass


class UninstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Uninstall - Sub Extractor")
        self.geometry("520x350")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG_DARK)

        self.install_dir = get_install_dir()
        self._setup_icon()
        self._create_widgets()

    def _setup_icon(self):
        ico_path = os.path.join(self.install_dir, "assets", "app_icon.ico")
        if not os.path.isfile(ico_path):
            ico_path = os.path.join(self.install_dir, "app_icon.ico")
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _create_widgets(self):
        frame = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG, corner_radius=16, border_width=1, border_color="#30363d")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            frame,
            text="Uninstall Sub Extractor",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#fda4af",
        )
        title.pack(pady=(20, 8), padx=20, anchor="w")

        desc = ctk.CTkLabel(
            frame,
            text="Are you sure you want to completely remove Sub Extractor and all of its components from:\n" + self.install_dir + "?",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            wraplength=440,
        )
        desc.pack(pady=(0, 15), padx=20, anchor="w")

        self.progress_bar = ctk.CTkProgressBar(frame, height=8, corner_radius=4, fg_color="#21262d", progress_color="#ff1744")
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 5))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            frame,
            text="Ready to uninstall",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED,
        )
        self.status_label.pack(pady=(2, 15), padx=20, anchor="w")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 15), side="bottom")

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.destroy,
            width=100,
            height=36,
        )
        self.btn_cancel.pack(side="right", padx=(10, 0))

        self.btn_uninstall = ctk.CTkButton(
            btn_row,
            text="Uninstall",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#4d1524",
            hover_color="#701a31",
            text_color="#fda4af",
            border_color="#e11d48",
            border_width=1,
            command=self.start_uninstall,
            width=110,
            height=36,
        )
        self.btn_uninstall.pack(side="right")

    def start_uninstall(self):
        self.btn_uninstall.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")

        def worker():
            self.status_label.configure(text="Removing registry keys...")
            self.progress_bar.set(0.3)
            remove_registry_entry()
            time.sleep(0.4)

            self.status_label.configure(text="Removing Desktop and Start Menu shortcuts...")
            self.progress_bar.set(0.6)
            remove_shortcuts()
            time.sleep(0.4)

            self.status_label.configure(text="Removing application files...")
            self.progress_bar.set(0.9)
            time.sleep(0.4)

            self.progress_bar.set(1.0)
            self.status_label.configure(text="Uninstallation complete!")

            # Schedule self-deletion of directory
            cleanup_bat = os.path.join(os.environ.get("TEMP", "C:\Temp"), "cleanup_subextractor.bat")
            cur_pid = os.getpid()
            with open(cleanup_bat, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("timeout /t 2 /nobreak > nul\n")
                f.write(f"taskkill /F /PID {cur_pid} > nul 2>&1\n")
                f.write(f'rd /s /q "{self.install_dir}" > nul 2>&1\n')
                f.write('del "%~f0" > nul 2>&1\n')

            subprocess.Popen(["cmd.exe", "/c", cleanup_bat], creationflags=0x08000000)

            def finish_ui():
                messagebox.showinfo(
                    "Uninstall Complete",
                    "Sub Extractor was successfully removed from your computer.",
                )
                self.destroy()

            self.after(0, finish_ui)

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = UninstallerApp()
    app.mainloop()