"""
Sub Extractor - Dedicated Windows Uninstaller
Safely removes all installed files, shortcuts, and Windows Add/Remove Programs registry entries with UAC Admin privileges.
"""

import os
import sys
import time
import winreg
import shutil
import subprocess
import threading
import ctypes
import customtkinter as ctk
from tkinter import messagebox


def is_admin() -> bool:
    """Check if the current process has administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_if_needed():
    """Relaunches the uninstaller with Administrator rights if not already elevated."""
    if not is_admin():
        try:
            if getattr(sys, "frozen", False):
                exe = sys.executable
                params = " ".join([f'"{a}"' for a in sys.argv[1:]])
            else:
                exe = sys.executable
                params = f'"{os.path.abspath(__file__)}" ' + " ".join([f'"{a}"' for a in sys.argv[1:]])

            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
            if ret > 32:
                sys.exit(0)
        except Exception:
            pass


elevate_if_needed()

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
    """Remove Desktop and Start Menu shortcuts across all user and system profiles."""
    # 1. Desktop shortcuts (User and Public)
    desktop_dirs = [
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
        r"C:\Users\Public\Desktop",
    ]
    for d in desktop_dirs:
        if not d or not os.path.isdir(d):
            continue
        for name in ("Sub Extractor.lnk", "PotPlayer Sub Extractor.lnk"):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    # 2. Start Menu Program shortcuts (User and AllUsers/ProgramData)
    start_menu_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]
    for sm in start_menu_dirs:
        if not sm or not os.path.isdir(sm):
            continue
        # Check standalone lnk files
        for name in ("Sub Extractor.lnk", "PotPlayer Sub Extractor.lnk"):
            p = os.path.join(sm, name)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        # Check folders
        for folder_name in ("Sub Extractor", "PotPlayer Sub Extractor"):
            fp = os.path.join(sm, folder_name)
            if os.path.isdir(fp):
                try:
                    shutil.rmtree(fp, ignore_errors=True)
                except Exception:
                    pass


def center_window_on_screen(window, width: int = 520, height: int = 350):
    """Calculates and applies exact center coordinates based on current monitor work area."""
    try:
        import win32api
        mon_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
        left, top, right, bottom = mon_info.get("Work", (0, 0, 1920, 1080))
        screen_w = right - left
        screen_h = bottom - top
        x = left + max(0, (screen_w - width) // 2)
        y = top + max(0, (screen_h - height) // 2)
    except Exception:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


class UninstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Uninstall - Sub Extractor")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG_DARK)

        # Center window on screen
        center_window_on_screen(self, 520, 350)

        self.install_dir = get_install_dir()
        self._setup_icon()
        self._create_widgets()

        # Re-assert centered geometry once widgets and DPI scaling are fully realized
        self.after(10, lambda: center_window_on_screen(self, 520, 350))
        self.after(60, lambda: center_window_on_screen(self, 520, 350))

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
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=24, pady=20)

        # Card
        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD_BG, corner_radius=14, border_width=1, border_color="#30363d")
        card.pack(fill="both", expand=True, pady=(0, 16))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        icon_lbl = ctk.CTkLabel(inner, text="🗑️", font=ctk.CTkFont(size=32))
        icon_lbl.pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text=f"Uninstall {APP_NAME}?",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        ).pack(pady=(0, 6))

        desc = (
            f"Are you sure you want to completely remove {APP_NAME} and all of its components "
            f"from your computer?\n\nInstallation Directory:\n{self.install_dir}"
        )
        ctk.CTkLabel(
            inner,
            text=desc,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED,
            justify="center",
            wraplength=440
        ).pack(pady=(0, 12))

        # Progress Section
        self.progress_bar = ctk.CTkProgressBar(inner, height=8, corner_radius=4, progress_color=COLOR_ACCENT_RED, fg_color="#21262d")
        self.status_lbl = ctk.CTkLabel(inner, text="", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED)

        # Buttons
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            height=40,
            width=90,
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.destroy
        )
        self.cancel_btn.pack(side="left")

        self.uninst_btn = ctk.CTkButton(
            btn_frame,
            text="Uninstall Now",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            fg_color=COLOR_ACCENT_RED,
            hover_color="#c40e34",
            text_color="#ffffff",
            command=self.start_uninstall
        )
        self.uninst_btn.pack(side="right", fill="x", expand=True, padx=(12, 0))

    def start_uninstall(self):
        self.uninst_btn.configure(state="disabled", text="Uninstalling...")
        self.cancel_btn.configure(state="disabled")

        self.progress_bar.pack(fill="x", pady=(8, 4))
        self.status_lbl.pack(anchor="center")
        self.progress_bar.set(0.2)
        self.status_lbl.configure(text="Removing shortcuts and registry entries...")

        threading.Thread(target=self._uninstall_worker, daemon=True).start()

    def _uninstall_worker(self):
        try:
            time.sleep(0.3)
            remove_registry_entry()
            remove_shortcuts()
            self.after(0, lambda: self.progress_bar.set(0.6))
            self.after(0, lambda: self.status_lbl.configure(text="Cleaning up files..."))
            time.sleep(0.3)

            target_dir = self.install_dir
            if os.path.isdir(target_dir):
                temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
                bat_path = os.path.join(temp_dir, "subextractor_cleanup.bat")
                bat_content = "@echo off\r\ntimeout /t 2 /nobreak > NUL\r\nrd /s /q \"" + target_dir + "\"\r\ndel \"%~f0\"\r\n"
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)

            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.status_lbl.configure(text="Uninstallation completed!"))
            time.sleep(0.4)

            def done():
                messagebox.showinfo("Uninstalled", f"{APP_NAME} was successfully removed from your computer.")
                self.destroy()

            self.after(0, done)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Uninstall Error", f"Failed to uninstall: {e}"))
            self.after(0, self.destroy)


def run_uninstaller():
    app = UninstallerApp()
    app.mainloop()


if __name__ == "__main__":
    run_uninstaller()