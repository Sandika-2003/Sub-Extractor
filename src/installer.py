"""
Sub Extractor - Windows Setup Installer
Modern GUI Setup Wizard that installs Sub Extractor to C:\Program Files\Sub Extractor with UAC Admin privileges.
"""

import os
import sys
import time
import winreg
import shutil
import subprocess
import threading
import ctypes
import pythoncom
import win32com.client
import customtkinter as ctk
from tkinter import filedialog, messagebox


def is_admin() -> bool:
    """Check if the current process has administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_if_needed():
    """Relaunches the installer with Administrator rights if not already elevated."""
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


def create_windows_shortcut(target_exe: str, shortcut_path: str, icon_path: str = None, description: str = "") -> bool:
    """
    Creates a Windows .lnk shortcut using COM Dispatch (with CoInitialize)
    and falls back to PowerShell to guarantee 100% reliability.
    """
    os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
    success = False

    # Method 1: COM WScript.Shell with pythoncom apartment initialization
    try:
        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(shortcut_path)
            sc.TargetPath = target_exe
            sc.WorkingDirectory = os.path.dirname(target_exe)
            sc.Description = description
            if icon_path and os.path.isfile(icon_path):
                sc.IconLocation = f"{icon_path},0"
            sc.Save()
            success = os.path.isfile(shortcut_path)
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        pass

    # Method 2: PowerShell script fallback
    if not success or not os.path.isfile(shortcut_path):
        try:
            target_dir = os.path.dirname(target_exe)
            ps_script = (
                '$w = New-Object -ComObject WScript.Shell; '
                f'$s = $w.CreateShortcut("{shortcut_path}"); '
                f'$s.TargetPath = "{target_exe}"; '
                f'$s.WorkingDirectory = "{target_dir}"; '
                f'$s.Description = "{description}"; '
            )
            if icon_path and os.path.isfile(icon_path):
                ps_script += f'$s.IconLocation = "{icon_path},0"; '
            ps_script += '$s.Save()'

            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script], capture_output=True, timeout=5)
            success = os.path.isfile(shortcut_path)
        except Exception:
            pass

    return success


def get_desktop_directories():
    """Returns all potential desktop folder paths (User and Public)."""
    dirs = []
    u_prof = os.environ.get("USERPROFILE", "")
    if u_prof:
        dirs.append(os.path.join(u_prof, "Desktop"))
    
    p_desktop = r"C:\Users\Public\Desktop"
    if os.path.isdir(p_desktop) and p_desktop not in dirs:
        dirs.append(p_desktop)

    try:
        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            d1 = shell.SpecialFolders("Desktop")
            d2 = shell.SpecialFolders("AllUsersDesktop")
            if d1 and d1 not in dirs:
                dirs.append(d1)
            if d2 and d2 not in dirs:
                dirs.append(d2)
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        pass

    return [d for d in dirs if os.path.isdir(d)]


def get_start_menu_programs_directories():
    """Returns all Start Menu Programs folder paths (User and AllUsers)."""
    dirs = []
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        dirs.append(os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"))

    progdata = os.environ.get("ProgramData", r"C:\ProgramData")
    p_programs = os.path.join(progdata, r"Microsoft\Windows\Start Menu\Programs")
    if os.path.isdir(p_programs) and p_programs not in dirs:
        dirs.append(p_programs)

    try:
        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            p1 = shell.SpecialFolders("Programs")
            p2 = shell.SpecialFolders("AllUsersPrograms")
            if p1 and p1 not in dirs:
                dirs.append(p1)
            if p2 and p2 not in dirs:
                dirs.append(p2)
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        pass

    return [d for d in dirs if os.path.isdir(d)]


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


def center_window_on_screen(window, width: int = 560, height: int = 520):
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


class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Setup - Sub Extractor")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG_DARK)

        # Center window on screen
        center_window_on_screen(self, 560, 520)

        self.install_dir_var = ctk.StringVar(value=get_default_install_dir())
        self.create_desktop_sc = ctk.BooleanVar(value=True)
        self.create_start_sc = ctk.BooleanVar(value=True)
        self.launch_after = ctk.BooleanVar(value=True)

        self.bundle_dir = get_bundle_dir()
        self._setup_icon()
        self._create_widgets()

        # Re-assert centered geometry once widgets and DPI scaling are fully realized
        self.after(10, lambda: center_window_on_screen(self, 560, 520))
        self.after(60, lambda: center_window_on_screen(self, 560, 520))

    def _setup_icon(self):
        ico_path = os.path.join(self.bundle_dir, "assets", "app_icon.ico")
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _create_widgets(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=24, pady=20)

        # Header Card
        header_card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD_BG, corner_radius=14, border_width=1, border_color=COLOR_CARD_BORDER)
        header_card.pack(fill="x", pady=(0, 16))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=14)

        icon_lbl = ctk.CTkLabel(header_inner, text="⚡", font=ctk.CTkFont(size=26, weight="bold"), text_color=COLOR_ACCENT_CYAN)
        icon_lbl.pack(side="left", padx=(0, 12))

        title_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=f"Install {APP_NAME}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="High-speed PotPlayer embedded subtitle extraction studio",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED
        ).pack(anchor="w")

        # Destination Folder Card
        dest_card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD_BG, corner_radius=14, border_width=1, border_color=COLOR_CARD_BORDER)
        dest_card.pack(fill="x", pady=(0, 16))

        dest_inner = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            dest_inner,
            text="📁 Destination Location:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        ).pack(anchor="w", pady=(0, 8))

        path_row = ctk.CTkFrame(dest_inner, fg_color="transparent")
        path_row.pack(fill="x")

        self.path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.install_dir_var,
            font=ctk.CTkFont(size=12),
            height=36,
            fg_color="#0d1117",
            border_color=COLOR_CARD_BORDER,
            text_color=COLOR_TEXT_MAIN
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            path_row,
            text="Browse...",
            width=80,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.browse_dir
        )
        browse_btn.pack(side="right")

        # Options Card
        opt_card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD_BG, corner_radius=14, border_width=1, border_color=COLOR_CARD_BORDER)
        opt_card.pack(fill="x", pady=(0, 16))

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            opt_inner,
            text="⚙️ Additional Options:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkCheckBox(
            opt_inner,
            text="Create Desktop Shortcut",
            variable=self.create_desktop_sc,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_ACCENT_BLUE
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkCheckBox(
            opt_inner,
            text="Create Start Menu Shortcut",
            variable=self.create_start_sc,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_ACCENT_BLUE
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkCheckBox(
            opt_inner,
            text="Launch Sub Extractor after installation",
            variable=self.launch_after,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_ACCENT_BLUE
        ).pack(anchor="w")

        # Progress / Status Section
        self.progress_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=8, corner_radius=4, progress_color=COLOR_ACCENT_CYAN, fg_color="#21262d")
        self.status_lbl = ctk.CTkLabel(self.progress_frame, text="", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED)

        # Bottom Buttons
        self.btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.btn_frame.pack(fill="x", side="bottom")

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            height=40,
            width=90,
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.destroy
        )
        self.cancel_btn.pack(side="left")

        self.install_btn = ctk.CTkButton(
            self.btn_frame,
            text="Install Now",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            fg_color=COLOR_ACCENT_BLUE,
            hover_color="#0062b3",
            text_color="#ffffff",
            command=self.start_installation
        )
        self.install_btn.pack(side="right", fill="x", expand=True, padx=(12, 0))

    def browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir_var.get(), title="Select Destination Folder")
        if chosen:
            self.install_dir_var.set(chosen)

    def start_installation(self):
        install_dir = self.install_dir_var.get().strip()
        if not install_dir:
            messagebox.showerror("Error", "Please specify a valid installation directory.")
            return

        self.install_btn.configure(state="disabled", text="Installing...")
        self.cancel_btn.configure(state="disabled")
        self.path_entry.configure(state="disabled")

        self.progress_frame.pack(fill="x", side="bottom", pady=(0, 16))
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.status_lbl.pack(anchor="w")
        self.progress_bar.set(0.1)
        self.status_lbl.configure(text="Preparing installation directory...")

        threading.Thread(target=self._install_worker, args=(install_dir,), daemon=True).start()

    def _install_worker(self, install_dir):
        try:
            time.sleep(0.2)
            # 1. Create installation directory
            self.after(0, lambda: self.status_lbl.configure(text=f"Creating {install_dir}..."))
            os.makedirs(install_dir, exist_ok=True)
            self.after(0, lambda: self.progress_bar.set(0.3))

            # 2. Extract payload files
            self.after(0, lambda: self.status_lbl.configure(text="Extracting application files..."))
            
            src_exe = os.path.join(self.bundle_dir, "SubExtractor.exe")
            src_uninst = os.path.join(self.bundle_dir, "Uninstall.exe")
            src_assets = os.path.join(self.bundle_dir, "assets")

            dst_exe = os.path.join(install_dir, "SubExtractor.exe")
            dst_uninst = os.path.join(install_dir, "Uninstall.exe")
            dst_assets = os.path.join(install_dir, "assets")

            if os.path.isfile(src_exe):
                shutil.copy2(src_exe, dst_exe)
            if os.path.isfile(src_uninst):
                shutil.copy2(src_uninst, dst_uninst)
            if os.path.isdir(src_assets):
                if os.path.exists(dst_assets):
                    shutil.rmtree(dst_assets, ignore_errors=True)
                shutil.copytree(src_assets, dst_assets)

            self.after(0, lambda: self.progress_bar.set(0.6))
            time.sleep(0.2)

            # 3. Create Shortcuts (with COM apartment init & multi-location support)
            self.after(0, lambda: self.status_lbl.configure(text="Creating desktop and start menu shortcuts..."))
            icon_file = os.path.join(dst_assets, "app_icon.ico") if os.path.isdir(dst_assets) else None

            # Desktop Shortcuts
            if self.create_desktop_sc.get():
                desktop_dirs = get_desktop_directories()
                for d_dir in desktop_dirs:
                    sc_path = os.path.join(d_dir, f"{APP_NAME}.lnk")
                    create_windows_shortcut(dst_exe, sc_path, icon_file, f"{APP_NAME} - PotPlayer Subtitle Extractor")

            # Start Menu Shortcuts
            if self.create_start_sc.get():
                start_dirs = get_start_menu_programs_directories()
                for s_dir in start_dirs:
                    sub_folder = os.path.join(s_dir, APP_NAME)
                    os.makedirs(sub_folder, exist_ok=True)
                    
                    sc_app = os.path.join(sub_folder, f"{APP_NAME}.lnk")
                    create_windows_shortcut(dst_exe, sc_app, icon_file, f"{APP_NAME}")
                    
                    sc_uninst = os.path.join(sub_folder, f"Uninstall {APP_NAME}.lnk")
                    create_windows_shortcut(dst_uninst, sc_uninst, icon_file, f"Uninstall {APP_NAME}")

            self.after(0, lambda: self.progress_bar.set(0.85))
            time.sleep(0.2)

            # 4. Register Uninstallation in Windows Registry
            self.after(0, lambda: self.status_lbl.configure(text="Registering application in Windows..."))
            register_uninstall(install_dir, dst_exe, dst_uninst, icon_file or dst_exe)

            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.status_lbl.configure(text="Installation completed successfully!"))
            time.sleep(0.3)

            def finish():
                self._show_completed_view(dst_exe)

            self.after(0, finish)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Installation Error", f"Failed to install: {e}"))
            self.after(0, self._restore_buttons)

    def _restore_buttons(self):
        self.install_btn.configure(state="normal", text="Install Now")
        self.cancel_btn.configure(state="normal")
        self.path_entry.configure(state="normal")

    def _show_completed_view(self, dst_exe):
        for widget in self.container.winfo_children():
            widget.destroy()

        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD_BG, corner_radius=16, border_width=1, border_color=COLOR_CARD_BORDER)
        card.pack(fill="both", expand=True, pady=10)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=24)

        icon_lbl = ctk.CTkLabel(inner, text="🎉", font=ctk.CTkFont(size=48))
        icon_lbl.pack(pady=(16, 12))

        ctk.CTkLabel(
            inner,
            text="Installation Completed!",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_ACCENT_GREEN
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text=f"{APP_NAME} has been successfully installed on your computer.\n\nYou can launch it anytime from your Desktop or Start Menu.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 24))

        close_btn = ctk.CTkButton(
            inner,
            text="Finish",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            width=200,
            fg_color=COLOR_ACCENT_BLUE,
            hover_color="#0062b3",
            command=lambda: self._finish_and_launch(dst_exe)
        )
        close_btn.pack(side="bottom", pady=(0, 8))

    def _finish_and_launch(self, dst_exe):
        if self.launch_after.get() and os.path.isfile(dst_exe):
            try:
                subprocess.Popen([dst_exe], cwd=os.path.dirname(dst_exe))
            except Exception:
                pass
        self.destroy()


def run_installer():
    app = InstallerApp()
    app.mainloop()


if __name__ == "__main__":
    run_installer()