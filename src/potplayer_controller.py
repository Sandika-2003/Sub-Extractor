"""
PotPlayer Controller Engine
Provides high-speed automation, real-time layout watchdog, audio inspection,
Alt+S subtitle extraction & auto-confirmation, folder video organization,
H/W Built-in DXVA Decoder enforcement, and Win32 message control for multi-instance PotPlayer playback.
"""

import os
import re
import sys
import time
import shutil
import subprocess
import threading
import ctypes
from typing import List, Tuple, Optional, Callable, Dict

import win32gui
import win32con
import win32process
import win32api
import psutil

try:
    from pycaw.pycaw import AudioUtilities
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False

user32 = ctypes.windll.user32

# PotPlayer Command & IPC Constants
WM_USER = 0x0400
POT_GET_PLAY_STATUS = 0x5006   # Returns 0=Stop, 1=Pause, 2=Playing
POT_SET_PLAY_STATUS = 0x5007   # lParam: 0=Stop, 1=Pause, 2=Play
POT_CMD_PLAY_PAUSE = 10014     # Official PotPlayer Play/Pause Toggle Command
POT_CMD_PAUSE = 10014          # Toggle play/pause
POT_CMD_PLAY = 10014           # Toggle play/pause
POT_CMD_PLAY_PAUSE_ALT = 1666  # Alt Play/Pause Command ID
POT_CMD_STOP = 10017
POT_CMD_MUTE = 10037
POT_CMD_SPEED_UP = 10283       # Increases speed by 0.1x (10%)
POT_CMD_SPEED_UP_ALT = 1673    # Alt command ID from language definitions
POT_CMD_SPEED_DOWN = 10284     # Decreases speed by 0.1x
POT_CMD_SPEED_NORMAL = 10285   # Resets speed to 1.0x

# Virtual Key Codes
VK_C = 0x43  # 'C' key (PotPlayer shortcut for speed up)
VK_S = 0x53  # 'S' key (Used with Alt for Save Subtitle)
VK_M = 0x4D  # 'M' key (PotPlayer shortcut for mute)
VK_SPACE = 0x20
VK_MENU = win32con.VK_MENU  # Alt key
VK_RETURN = win32con.VK_RETURN

SUPPORTED_VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".ts", ".m2ts", ".mts", ".vob", ".ogv", ".3gp", ".m4v",
    ".mpg", ".mpeg", ".asf", ".rmvb", ".divx", ".iso"
}

STANDARD_POTPLAYER_PATHS = [
    r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
    r"C:\Program Files\DAUM\PotPlayer\PotPlayer64.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayer.exe",
    r"C:\Program Files\PotPlayer\PotPlayerMini64.exe",
    r"C:\Program Files\PotPlayer\PotPlayer64.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\DAUM\PotPlayer\PotPlayerMini64.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\DAUM\PotPlayer\PotPlayerMini64.exe"),
]

MAX_GRID_ROWS = 10
MAX_GRID_COLS = 2
MAX_VIDEOS_PER_BATCH = 20


def ensure_hardware_dxva_enabled() -> bool:
    """
    Enforces H/W Built-in DXVA Decoder and Hardware Acceleration
    across all PotPlayer configurations in the Windows Registry.
    """
    try:
        import winreg
        reg_paths = [
            r"Software\Daum\PotPlayerMini64\Settings",
            r"Software\Daum\PotPlayer64\Settings",
            r"Software\Daum\PotPlayer\Settings",
        ]
        dxva_settings = {
            "IntDXVAUseMode": 1,        # Built-in DXVA Decoder ON
            "CudaDecoder": 1,           # NVIDIA CUDA Hardware Decoder ON
            "QuickSyncDecoder": 1,      # Intel QuickSync Hardware Decoder ON
            "MftDecoder": 1,            # Media Foundation Hardware Transform ON
            "DmoDecoder": 1,            # DirectShow Media Objects ON
            "SupportH264MVC": 1,        # Hardware MVC Decode ON
        }
        for path in reg_paths:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
                    for k, v in dxva_settings.items():
                        winreg.SetValueEx(key, k, 0, winreg.REG_DWORD, v)
            except Exception:
                pass
        return True
    except Exception:
        return False


def find_potplayer_path() -> Optional[str]:
    """Auto-detect the installation path of PotPlayer executable."""
    for path in STANDARD_POTPLAYER_PATHS:
        if os.path.isfile(path):
            return path

    # Check Windows Registry
    try:
        import winreg
        reg_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\Applications\PotPlayer64.exe\shell\open\command"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\PotPlayer64.file\shell\open\command"),
            (winreg.HKEY_CURRENT_USER, r"Software\DAUM\PotPlayer"),
            (winreg.HKEY_CURRENT_USER, r"Software\DAUM\PotPlayerMini64"),
        ]
        for hkey, subkey in reg_keys:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    match = re.search(r'"([^"]+PotPlayer[^"]*\.exe)"', val, re.IGNORECASE)
                    if match and os.path.isfile(match.group(1)):
                        return match.group(1)
            except Exception:
                continue
    except Exception:
        pass

    return None


def natural_sort_key(s: str):
    """Sort strings containing numbers in natural human order (video 1, video 2, ... video 10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def scan_video_files(folder_path: str, recursive: bool = True, custom_exts: Optional[set] = None) -> List[str]:
    """Scan folder and all nested subfolders for video files and return naturally sorted list of paths."""
    exts = custom_exts if custom_exts else SUPPORTED_VIDEO_EXTS
    video_files = []

    if not os.path.isdir(folder_path):
        return []

    if recursive:
        for root, _, files in os.walk(folder_path):
            for f in files:
                _, ext = os.path.splitext(f)
                if ext.lower() in exts:
                    video_files.append(os.path.join(root, f))
    else:
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path):
                _, ext = os.path.splitext(f)
                if ext.lower() in exts:
                    video_files.append(full_path)

    # Naturally sort by relative path so subfolder contents are organized cleanly in order
    video_files.sort(key=lambda p: natural_sort_key(os.path.relpath(p, folder_path)))
    return video_files


def organize_videos_into_folders(
    folder_path: str,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> List[Tuple[str, str]]:
    """
    Scans folder for videos, creates a dedicated folder named after each video,
    and moves the video (along with any matching subtitle files) into that new folder.
    Returns list of (video_filename, target_folder_name).
    """
    if not os.path.isdir(folder_path):
        return []

    # 1. Collect all video files
    video_candidates = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            name, ext = os.path.splitext(f)
            if ext.lower() in SUPPORTED_VIDEO_EXTS:
                full_video_path = os.path.join(root, f)
                parent_dir = root
                parent_name = os.path.basename(parent_dir)
                
                # If already in a folder with the same name, skip
                if parent_name.lower() == name.lower():
                    continue

                target_folder = os.path.join(parent_dir, name)
                target_video_path = os.path.join(target_folder, f)
                video_candidates.append((full_video_path, target_folder, target_video_path, f, name, parent_dir))

    total = len(video_candidates)
    if total == 0:
        return []

    results = []
    # 2. Execute moves
    for idx, (src_video, target_folder, dst_video, fname, stem, p_dir) in enumerate(video_candidates):
        if on_progress:
            on_progress(idx + 1, total, f"Organizing [{idx+1}/{total}]: {fname} -> {stem}/")

        try:
            os.makedirs(target_folder, exist_ok=True)
            if not os.path.exists(dst_video):
                shutil.move(src_video, dst_video)
                results.append((fname, stem))

                # Also move any matching subtitle/nfo files if present (e.g. video.srt, video.ass)
                for companion_file in os.listdir(p_dir):
                    c_name, c_ext = os.path.splitext(companion_file)
                    c_path = os.path.join(p_dir, companion_file)
                    if c_name == stem and os.path.isfile(c_path) and c_path != dst_video:
                        c_target = os.path.join(target_folder, companion_file)
                        if not os.path.exists(c_target):
                            try:
                                shutil.move(c_path, c_target)
                            except Exception:
                                pass
        except Exception:
            pass

        time.sleep(0.01)

    return results


def get_all_potplayer_hwnds() -> List[int]:
    """Get all visible PotPlayer window handles safely."""
    results = []

    def callback(hwnd, _):
        try:
            if win32gui.IsWindowVisible(hwnd):
                cls = win32gui.GetClassName(hwnd)
                if cls in ("PotPlayer64", "PotPlayer"):
                    results.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass
    return results


def get_play_status(hwnd: int) -> int:
    """Returns 0=Stop, 1=Pause, 2=Playing, -1=Unknown."""
    try:
        return win32gui.SendMessage(hwnd, WM_USER, POT_GET_PLAY_STATUS, 0)
    except Exception:
        return -1


def get_screen_work_area() -> Tuple[int, int, int, int]:
    """Get primary monitor work area (excluding taskbar): (left, top, right, bottom)."""
    try:
        mon_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
        return mon_info.get("Work", (0, 0, 1920, 1080))
    except Exception:
        return (0, 0, 1920, 1080)


def calculate_window_positions(
    num_items: int, min_w: int = 340, min_h: int = 100
) -> List[Tuple[int, int, int, int]]:
    """
    Calculates exact 10 Rows x 2 Columns grid table positions (Max 20 items):
    - Column 0: Videos 1 to 10 (stacked top to bottom)
    - Column 1: Videos 11 to 20 (stacked top to bottom)
    """
    left, top, right, bottom = get_screen_work_area()
    screen_w = right - left
    screen_h = bottom - top

    row_h = max(75, screen_h // MAX_GRID_ROWS)
    col_w = max(320, min(screen_w // MAX_GRID_COLS, 380))

    positions = []

    for i in range(num_items):
        col = (i // MAX_GRID_ROWS) % MAX_GRID_COLS
        row = i % MAX_GRID_ROWS

        x = left + (col * col_w)
        y = top + (row * row_h)

        positions.append((x, y, col_w, row_h))

    return positions


def check_if_audio_muted() -> bool:
    """Check if any active PotPlayer audio session is currently muted or volume is 0."""
    if not PYCAW_AVAILABLE:
        return False
    try:
        sessions = AudioUtilities.GetAllSessions()
        for s in sessions:
            if s.Process and "potplayer" in s.Process.name().lower():
                vol = s.SimpleAudioVolume
                if vol.GetMute() == 1 or vol.GetMasterVolume() <= 0.001:
                    return True
    except Exception:
        pass
    return False


def apply_speed_boost_fast(hwnd: int, steps: int = 110):
    """
    Playback speed boost: focuses window, attaches thread input,
    and rapidly dispatches hardware key pulses + command messages for 'C' (12.0x).
    """
    if steps <= 0:
        return

    cur_tid = win32api.GetCurrentThreadId()
    try:
        pot_tid, _ = win32process.GetWindowThreadProcessId(hwnd)
        if pot_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, pot_tid, True)

        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)

        scan_c = win32api.MapVirtualKey(VK_C, 0)

        for _ in range(steps):
            win32api.keybd_event(VK_C, scan_c, 0, 0)
            win32api.keybd_event(VK_C, scan_c, win32con.KEYEVENTF_KEYUP, 0)
            win32gui.PostMessage(hwnd, win32con.WM_COMMAND, POT_CMD_SPEED_UP, 0)
            win32gui.PostMessage(hwnd, win32con.WM_COMMAND, POT_CMD_SPEED_UP_ALT, 0)

        if pot_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, pot_tid, False)
    except Exception:
        for _ in range(steps):
            win32gui.PostMessage(hwnd, win32con.WM_COMMAND, POT_CMD_SPEED_UP, 0)


class PotPlayerController:
    """Core controller for multi-instance PotPlayer automation."""

    def __init__(self, potplayer_exe: Optional[str] = None):
        self.potplayer_exe = potplayer_exe or find_potplayer_path()
        self.launched_hwnds: List[int] = []
        self.grid_slots: Dict[int, Tuple[int, int, int, int]] = {}  # hwnd -> (x, y, w, h)
        self.is_paused: bool = False
        self.is_running_batch: bool = False
        self._stop_requested: bool = False
        self._watchdog_active: bool = False
        self._lock = threading.Lock()

        # Enforce H/W DXVA Hardware decoder on init
        ensure_hardware_dxva_enabled()

    def set_executable_path(self, path: str):
        """Update PotPlayer executable path."""
        if os.path.isfile(path):
            self.potplayer_exe = path
            return True
        return False

    def is_available(self) -> bool:
        """Check if PotPlayer executable is located."""
        return self.potplayer_exe is not None and os.path.isfile(self.potplayer_exe)

    def cancel_batch(self):
        """Request cancellation of ongoing batch launch."""
        self._stop_requested = True

    def _layout_watchdog_loop(self):
        """
        Continuous background daemon that enforces the exact 10-rows x 2-columns grid slot
        for every open PotPlayer window throughout the entire lifecycle.
        """
        while self._watchdog_active:
            with self._lock:
                slots = list(self.grid_slots.items())

            for h, (x, y, w, h_dim) in slots:
                try:
                    if win32gui.IsWindow(h) and win32gui.IsWindowVisible(h):
                        rect = win32gui.GetWindowRect(h)
                        cur_x = rect[0]
                        cur_y = rect[1]
                        cur_w = rect[2] - rect[0]
                        cur_h = rect[3] - rect[1]
                        # Snap back whenever window drifts, resizes, or resets aspect ratio
                        if abs(cur_x - x) > 2 or abs(cur_y - y) > 2 or abs(cur_w - w) > 4 or abs(cur_h - h_dim) > 4:
                            win32gui.SetWindowPos(
                                h, 0, x, y, w, h_dim,
                                win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
                            )
                except Exception:
                    pass
            time.sleep(0.1)

    def launch_and_arrange_batch(
        self,
        video_files: List[str],
        target_speed: float = 12.0,
        min_w: int = 340,
        min_h: int = 100,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_finished: Optional[Callable[[int], None]] = None,
    ):
        """
        Sequential launcher:
        Enforces H/W DXVA Hardware decoder, opens videos one by one into a 10-rows x 2-columns table grid (up to 20 videos max),
        mutes them, accelerates playback to 12.0x, and keeps layout watchdog running continuously.
        """
        if not self.is_available():
            raise FileNotFoundError("PotPlayer executable not found. Please specify the path in Settings.")

        if not video_files:
            if on_finished:
                on_finished(0)
            return

        # Enforce DXVA hardware decoder before launch
        ensure_hardware_dxva_enabled()

        self.is_running_batch = True
        self._stop_requested = False
        self.is_paused = False

        total_videos = len(video_files)
        positions = calculate_window_positions(total_videos, min_w=min_w, min_h=min_h)

        with self._lock:
            self.launched_hwnds.clear()
            self.grid_slots.clear()

        # Start continuous layout watchdog daemon if not already running
        if not self._watchdog_active:
            self._watchdog_active = True
            watchdog_thread = threading.Thread(target=self._layout_watchdog_loop, daemon=True)
            watchdog_thread.start()

        first_video_muted: Optional[bool] = None
        speed_steps = max(0, int(round((target_speed - 1.0) / 0.1)))

        for idx, video_path in enumerate(video_files):
            if self._stop_requested:
                if on_progress:
                    on_progress(idx, total_videos, "Operation cancelled by user.")
                break

            video_name = os.path.basename(video_path)
            x, y, w, h = positions[idx]
            col_num = (idx // MAX_GRID_ROWS) + 1
            row_num = (idx % MAX_GRID_ROWS) + 1

            if on_progress:
                on_progress(idx + 1, total_videos, f"[{idx+1}/{total_videos}] Tiling (Col {col_num}, Row {row_num}): {video_name}")

            existing_hwnds = set(get_all_potplayer_hwnds())

            # 1. Launch instance
            cmd = [self.potplayer_exe, "/new", "/volume=0", video_path]
            try:
                subprocess.Popen(cmd)
            except Exception as e:
                if on_progress:
                    on_progress(idx + 1, total_videos, f"Failed to launch {video_name}: {e}")
                continue

            # 2. Polling for window
            new_hwnd = None
            for _ in range(80):
                if self._stop_requested:
                    break
                time.sleep(0.03)
                curr_hwnds = get_all_potplayer_hwnds()
                candidates = [h_val for h_val in curr_hwnds if h_val not in existing_hwnds and h_val not in self.launched_hwnds]
                if candidates:
                    new_hwnd = candidates[0]
                    break

            if not new_hwnd:
                continue

            with self._lock:
                self.launched_hwnds.append(new_hwnd)
                self.grid_slots[new_hwnd] = (x, y, w, h)

            # 3. Position window immediately into assigned 10x2 grid cell
            try:
                win32gui.SetWindowPos(
                    new_hwnd,
                    0,
                    x,
                    y,
                    w,
                    h,
                    win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW,
                )
            except Exception:
                pass

            # 4. MUTE command
            if idx == 0:
                first_video_muted = check_if_audio_muted()
                if not first_video_muted:
                    try:
                        win32gui.PostMessage(new_hwnd, win32con.WM_COMMAND, POT_CMD_MUTE, 0)
                    except Exception:
                        pass
            else:
                if not first_video_muted:
                    try:
                        win32gui.PostMessage(new_hwnd, win32con.WM_COMMAND, POT_CMD_MUTE, 0)
                    except Exception:
                        pass

            # 5. Rapid Speed Boost (12.0x)
            if speed_steps > 0:
                apply_speed_boost_fast(new_hwnd, speed_steps)

            # Clamp window into slot again after speed pulses
            try:
                win32gui.SetWindowPos(
                    new_hwnd,
                    0,
                    x,
                    y,
                    w,
                    h,
                    win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW,
                )
            except Exception:
                pass

            if on_progress:
                on_progress(idx + 1, total_videos, f"[{idx+1}/{total_videos}] Ready: {video_name} (Col {col_num}, Row {row_num} @ {target_speed:.1f}x [H/W DXVA])")

            time.sleep(0.06)

        self.is_running_batch = False

        if on_progress:
            on_progress(len(self.launched_hwnds), total_videos, f"All {len(self.launched_hwnds)} videos tiled in 10x2 grid running at {target_speed:.1f}x (H/W DXVA Enabled)!")

        if on_finished:
            on_finished(len(self.launched_hwnds))

    def save_subtitles_all(
        self,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_finished: Optional[Callable[[int], None]] = None,
    ) -> int:
        """
        Rapidly iterates through all open PotPlayer instances one by one,
        triggers Alt + S, and automatically confirms the Save dialog.
        """
        hwnds = self.get_active_hwnds()
        if not hwnds:
            if on_finished:
                on_finished(0)
            return 0

        cur_tid = win32api.GetCurrentThreadId()
        scan_alt = win32api.MapVirtualKey(VK_MENU, 0)
        scan_s = win32api.MapVirtualKey(VK_S, 0)
        scan_ret = win32api.MapVirtualKey(VK_RETURN, 0)
        total = len(hwnds)
        success_count = 0

        for idx, h in enumerate(hwnds):
            try:
                title = win32gui.GetWindowText(h) or f"Player {idx+1}"
                clean_name = title.replace(" - PotPlayer", "").replace("PotPlayer", "").strip() or f"Instance {idx+1}"
                if on_progress:
                    on_progress(idx + 1, total, f"[{idx+1}/{total}] Saving subtitles: {clean_name}")

                pot_tid, pot_pid = win32process.GetWindowThreadProcessId(h)
                if pot_tid != cur_tid:
                    user32.AttachThreadInput(cur_tid, pot_tid, True)

                user32.SetForegroundWindow(h)
                user32.SetFocus(h)
                time.sleep(0.04)

                # 1. Send Alt + S keystroke to open Save Dialog
                win32api.keybd_event(VK_MENU, scan_alt, 0, 0)
                time.sleep(0.01)
                win32api.keybd_event(VK_S, scan_s, 0, 0)
                time.sleep(0.01)
                win32api.keybd_event(VK_S, scan_s, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.01)
                win32api.keybd_event(VK_MENU, scan_alt, win32con.KEYEVENTF_KEYUP, 0)

                if pot_tid != cur_tid:
                    user32.AttachThreadInput(cur_tid, pot_tid, False)

                # 2. Look for Save Dialog (#32770)
                dialog_hwnd = None
                for _ in range(12):
                    time.sleep(0.04)
                    dlg_candidates = []
                    def enum_dlg(dlg_h, _):
                        try:
                            if win32gui.IsWindowVisible(dlg_h):
                                cls = win32gui.GetClassName(dlg_h)
                                _, ppid = win32process.GetWindowThreadProcessId(dlg_h)
                                if ppid == pot_pid and cls == "#32770":
                                    dlg_candidates.append(dlg_h)
                        except Exception:
                            pass
                        return True

                    try:
                        win32gui.EnumWindows(enum_dlg, None)
                    except Exception:
                        pass

                    if dlg_candidates:
                        dialog_hwnd = dlg_candidates[0]
                        break

                # 3. If Save Dialog appeared, confirm Save with ENTER
                if dialog_hwnd:
                    dtid, _ = win32process.GetWindowThreadProcessId(dialog_hwnd)
                    if dtid != cur_tid:
                        user32.AttachThreadInput(cur_tid, dtid, True)

                    user32.SetForegroundWindow(dialog_hwnd)
                    user32.SetFocus(dialog_hwnd)
                    time.sleep(0.06)

                    win32api.keybd_event(VK_RETURN, scan_ret, 0, 0)
                    time.sleep(0.01)
                    win32api.keybd_event(VK_RETURN, scan_ret, win32con.KEYEVENTF_KEYUP, 0)

                    if dtid != cur_tid:
                        user32.AttachThreadInput(cur_tid, dtid, False)

                    # 4. Check for overwrite confirmation prompt
                    time.sleep(0.1)
                    confirm_candidates = []
                    def enum_confirm(c_h, _):
                        try:
                            if win32gui.IsWindowVisible(c_h) and win32gui.GetClassName(c_h) == "#32770":
                                _, ppid = win32process.GetWindowThreadProcessId(c_h)
                                if ppid == pot_pid and c_h != dialog_hwnd:
                                    confirm_candidates.append(c_h)
                        except Exception:
                            pass
                        return True

                    try:
                        win32gui.EnumWindows(enum_confirm, None)
                    except Exception:
                        pass

                    if confirm_candidates:
                        c_hwnd = confirm_candidates[0]
                        ctid, _ = win32process.GetWindowThreadProcessId(c_hwnd)
                        if ctid != cur_tid:
                            user32.AttachThreadInput(cur_tid, ctid, True)
                        user32.SetForegroundWindow(c_hwnd)
                        time.sleep(0.03)
                        win32api.keybd_event(VK_RETURN, scan_ret, 0, 0)
                        time.sleep(0.01)
                        win32api.keybd_event(VK_RETURN, scan_ret, win32con.KEYEVENTF_KEYUP, 0)
                        if ctid != cur_tid:
                            user32.AttachThreadInput(cur_tid, ctid, False)

                success_count += 1
                time.sleep(0.05)
            except Exception:
                pass

        if on_progress:
            on_progress(total, total, f"Subtitles saved on all {success_count}/{total} players!")

        if on_finished:
            on_finished(success_count)

        return success_count

    def pause_all(self):
        """Synchronously pause all open PotPlayer instances."""
        hwnds = self.get_active_hwnds()
        for h in hwnds:
            try:
                st = get_play_status(h)
                if st == 2 or st == -1:
                    win32gui.SendMessage(h, win32con.WM_COMMAND, POT_CMD_PLAY_PAUSE, 0)
            except Exception:
                pass
        self.is_paused = True

    def play_all(self):
        """Synchronously resume playback across all open PotPlayer instances."""
        hwnds = self.get_active_hwnds()
        for h in hwnds:
            try:
                st = get_play_status(h)
                if st == 1 or st == -1:
                    win32gui.SendMessage(h, win32con.WM_COMMAND, POT_CMD_PLAY_PAUSE, 0)
            except Exception:
                pass
        self.is_paused = False

    def toggle_play_pause(self) -> bool:
        """
        Toggles play/pause state across all open PotPlayer instances.
        Returns the new state (True = Paused, False = Playing).
        """
        hwnds = self.get_active_hwnds()
        if not hwnds:
            return False

        if not self.is_paused:
            self.pause_all()
        else:
            self.play_all()

        return self.is_paused

    def close_all(self) -> int:
        """
        Closes all running PotPlayer windows and terminates any orphaned PotPlayer processes.
        Explicitly guards against closing this application itself.
        """
        self._watchdog_active = False
        closed_count = 0
        hwnds = get_all_potplayer_hwnds()

        for h in hwnds:
            try:
                win32gui.PostMessage(h, win32con.WM_CLOSE, 0, 0)
                closed_count += 1
            except Exception:
                pass

        time.sleep(0.3)

        my_pid = os.getpid()
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if p.pid == my_pid:
                    continue
                pname = (p.info["name"] or "").lower()
                if ("potplayer" in pname or "potplayermini" in pname) and "subextractor" not in pname:
                    p.kill()
                    closed_count += 1
            except Exception:
                pass

        with self._lock:
            self.launched_hwnds.clear()
            self.grid_slots.clear()
        self.is_paused = False
        return closed_count

    def get_active_hwnds(self) -> List[int]:
        """Return valid active HWNDs from currently tracked list or active windows."""
        all_current = set(get_all_potplayer_hwnds())
        with self._lock:
            active = [h for h in self.launched_hwnds if h in all_current]
            if not active and all_current:
                active = list(all_current)
                self.launched_hwnds = list(all_current)
            else:
                self.launched_hwnds = active
            return list(self.launched_hwnds)