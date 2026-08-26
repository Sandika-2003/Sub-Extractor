"""
PotPlayer Multi-Instance Automation & Subtitle Extractor GUI
Modern Glassmorphism UI built with CustomTkinter.
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, List

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    from src.potplayer_controller import (
        PotPlayerController,
        scan_video_files,
        organize_videos_into_folders,
        find_potplayer_path,
        get_all_potplayer_hwnds,
        calculate_window_positions,
        get_screen_work_area,
    )
except ImportError:
    from potplayer_controller import (
        PotPlayerController,
        scan_video_files,
        organize_videos_into_folders,
        find_potplayer_path,
        get_all_potplayer_hwnds,
        calculate_window_positions,
        get_screen_work_area,
    )

# Appearance setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Theme Colors
COLOR_BG_DARK = "#0d1117"
COLOR_CARD_BG = "#161b22"
COLOR_CARD_BORDER = "#30363d"
COLOR_ACCENT_CYAN = "#00d2ff"
COLOR_ACCENT_BLUE = "#0078d4"
COLOR_ACCENT_GREEN = "#00e676"
COLOR_ACCENT_TEAL = "#0d9488"
COLOR_ACCENT_AMBER = "#ff9100"
COLOR_ACCENT_PURPLE = "#a855f7"
COLOR_ACCENT_RED = "#ff1744"
COLOR_TEXT_MAIN = "#f0f6fc"
COLOR_TEXT_MUTED = "#8b949e"

# Glassmorphic Badge / Button Styles
STYLE_BTN_TEAL = {
    "fg_color": "#0a2628",
    "hover_color": "#113d40",
    "text_color": "#5eead4",
    "border_color": "#0d9488",
    "border_width": 2,
    "corner_radius": 14,
}

STYLE_BTN_CYAN = {
    "fg_color": "#0f263d",
    "hover_color": "#183b5e",
    "text_color": "#7dd3fc",
    "border_color": "#0284c7",
    "border_width": 2,
    "corner_radius": 14,
}

STYLE_BTN_PURPLE = {
    "fg_color": "#231138",
    "hover_color": "#3b1c5c",
    "text_color": "#e9d5ff",
    "border_color": "#a855f7",
    "border_width": 2,
    "corner_radius": 14,
}

STYLE_BTN_AMBER = {
    "fg_color": "#2b1a08",
    "hover_color": "#452a0d",
    "text_color": "#fde047",
    "border_color": "#d97706",
    "border_width": 2,
    "corner_radius": 14,
}

STYLE_BTN_EMERALD = {
    "fg_color": "#092d19",
    "hover_color": "#124828",
    "text_color": "#86efac",
    "border_color": "#10b981",
    "border_width": 2,
    "corner_radius": 14,
}

STYLE_BTN_CRIMSON = {
    "fg_color": "#300d16",
    "hover_color": "#4d1524",
    "text_color": "#fda4af",
    "border_color": "#e11d48",
    "border_width": 2,
    "corner_radius": 14,
}


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class ModernSubExtractorApp(ctk.CTk):
    """Main Glassmorphic GUI Application."""

    def __init__(self):
        super().__init__()

        self.title("PotPlayer Subtitle Extractor Studio")
        self.geometry("620x820")
        self.minsize(560, 720)

        # Controller instance
        self.controller = PotPlayerController()

        # State variables
        self.selected_folder = ctk.StringVar(value="")
        self.target_speed = ctk.DoubleVar(value=12.0)
        self.scan_recursive = ctk.BooleanVar(value=True)
        self.tile_min_w = ctk.IntVar(value=320)
        self.tile_min_h = ctk.IntVar(value=100)
        self.pot_path_var = ctk.StringVar(value=self.controller.potplayer_exe or "Not Found")
        
        self.is_paused_state = False
        self.batch_thread: Optional[threading.Thread] = None
        self.sub_thread: Optional[threading.Thread] = None
        self.org_thread: Optional[threading.Thread] = None

        # Setup icon
        self._setup_window_icon()

        # Build UI layout
        self.configure(fg_color=COLOR_BG_DARK)
        self._create_widgets()

        # Initial checks
        self._update_system_status()

    def _setup_window_icon(self):
        """Set application icon if available."""
        ico_path = get_resource_path(os.path.join("assets", "app_icon.ico"))
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _create_widgets(self):
        """Build modern glassmorphic dashboard."""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=16)

        # --- 1. HEADER SECTION ---
        header_frame = ctk.CTkFrame(main_container, fg_color=COLOR_CARD_BG, corner_radius=16, border_width=1, border_color=COLOR_CARD_BORDER)
        header_frame.pack(fill="x", pady=(0, 10), padx=2)

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=10)

        title_label = ctk.CTkLabel(
            header_inner,
            text="⚡ PotPlayer Sub Extractor Studio",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_ACCENT_CYAN,
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_inner,
            text="Video folder organizer, multi-launcher, auto-tiling, 12x speed & subtitle extractor",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED,
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # --- 2. STATUS CARD ---
        self.status_card = ctk.CTkFrame(main_container, fg_color="#121820", corner_radius=12, border_width=1, border_color="#1f2937")
        self.status_card.pack(fill="x", pady=(0, 10), padx=2)

        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=14, pady=8)

        # Left side: Status badge
        status_left = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_left.pack(side="left")

        self.status_pill = ctk.CTkLabel(
            status_left,
            text="● READY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_ACCENT_GREEN,
            fg_color="#003820",
            corner_radius=8,
            padx=10,
            pady=4,
        )
        self.status_pill.pack(side="left")

        self.status_detail_label = ctk.CTkLabel(
            status_left,
            text="No videos loaded",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
        )
        self.status_detail_label.pack(side="left", padx=12)

        # Right side: Metric tags
        status_right = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_right.pack(side="right")

        self.speed_badge = ctk.CTkLabel(
            status_right,
            text="⚡ 12.0x Speed",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ff79c6",
            fg_color="#381026",
            corner_radius=8,
            padx=8,
            pady=4,
        )
        self.speed_badge.pack(side="right", padx=(6, 0))

        self.active_badge = ctk.CTkLabel(
            status_right,
            text="🎬 0 Players",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8be9fd",
            fg_color="#102838",
            corner_radius=8,
            padx=8,
            pady=4,
        )
        self.active_badge.pack(side="right")

        # --- 3. HERO ACTION BUTTONS (1 to 5) ---
        actions_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 10))

        # BUTTON 1: ORGANIZE VIDEOS INTO FOLDERS
        self.btn_organize_videos = ctk.CTkButton(
            actions_frame,
            text="📁  1. Organize Videos into Dedicated Folders (1 Video -> 1 Folder)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=48,
            command=self.on_organize_videos_clicked,
            **STYLE_BTN_TEAL
        )
        self.btn_organize_videos.pack(fill="x", pady=(0, 8))

        # BUTTON 2: SELECT VIDEOS & LAUNCH
        self.btn_select_launch = ctk.CTkButton(
            actions_frame,
            text="📂  2. Select Folder & Launch All Videos (12.0x)",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            command=self.on_select_folder_clicked,
            **STYLE_BTN_CYAN
        )
        self.btn_select_launch.pack(fill="x", pady=(0, 8))

        # BUTTON 3: SAVE SUBTITLES (Alt + S)
        self.btn_save_subtitles = ctk.CTkButton(
            actions_frame,
            text="💾  3. Save Subtitles (Alt + S)",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            command=self.on_save_subtitles_clicked,
            **STYLE_BTN_PURPLE
        )
        self.btn_save_subtitles.pack(fill="x", pady=(0, 8))

        # BUTTON 4: PAUSE / PLAY TOGGLE
        self.btn_toggle_play = ctk.CTkButton(
            actions_frame,
            text="⏸️  4. Pause All Players",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            command=self.on_toggle_play_pause_clicked,
            **STYLE_BTN_AMBER
        )
        self.btn_toggle_play.pack(fill="x", pady=(0, 8))

        # BUTTON 5: CLOSE ALL PLAYERS
        self.btn_close_all = ctk.CTkButton(
            actions_frame,
            text="🛑  5. Close All Players",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self.on_close_all_clicked,
            **STYLE_BTN_CRIMSON
        )
        self.btn_close_all.pack(fill="x", pady=(0, 2))

        # --- 4. PROGRESS BAR ---
        self.progress_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(2, 6))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=8,
            corner_radius=4,
            fg_color="#21262d",
            progress_color=COLOR_ACCENT_CYAN,
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        # --- 5. LOG / ACTIVITY TERMINAL ---
        log_header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        log_header_frame.pack(fill="x", pady=(2, 2))

        ctk.CTkLabel(
            log_header_frame,
            text="📋 Activity Log",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
        ).pack(side="left")

        self.btn_clear_log = ctk.CTkButton(
            log_header_frame,
            text="Clear",
            font=ctk.CTkFont(size=10),
            width=50,
            height=20,
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.clear_log,
        )
        self.btn_clear_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            main_container,
            height=125,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#090d13",
            text_color="#c9d1d9",
            border_width=1,
            border_color=COLOR_CARD_BORDER,
            corner_radius=10,
        )
        self.log_textbox.pack(fill="both", expand=True, pady=(0, 6))

        # --- 6. COLLAPSIBLE SETTINGS ACCORDION ---
        self.settings_frame = ctk.CTkFrame(main_container, fg_color=COLOR_CARD_BG, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        self.settings_frame.pack(fill="x", pady=(0, 2))

        self.settings_toggle_btn = ctk.CTkButton(
            self.settings_frame,
            text="⚙️ Advanced Settings & PotPlayer Path  [ ▼ ]",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            hover_color="#21262d",
            text_color=COLOR_TEXT_MAIN,
            anchor="w",
            height=30,
            command=self.toggle_settings_panel,
        )
        self.settings_toggle_btn.pack(fill="x", padx=6, pady=4)

        self.settings_content = ctk.CTkFrame(self.settings_frame, fg_color="transparent")

        # Speed slider row
        speed_row = ctk.CTkFrame(self.settings_content, fg_color="transparent")
        speed_row.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(speed_row, text="Target Speed Multiplier:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MAIN, width=160, anchor="w").pack(side="left")
        
        self.speed_slider = ctk.CTkSlider(
            speed_row,
            from_=1.0,
            to=12.0,
            number_of_steps=110,
            variable=self.target_speed,
            command=self._on_speed_slider_change,
            button_color=COLOR_ACCENT_CYAN,
            progress_color=COLOR_ACCENT_BLUE,
        )
        self.speed_slider.pack(side="left", fill="x", expand=True, padx=8)

        self.speed_val_label = ctk.CTkLabel(
            speed_row,
            text="12.0x",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_ACCENT_CYAN,
            width=50,
        )
        self.speed_val_label.pack(side="right")

        # Recursive scan checkbox
        opt_row = ctk.CTkFrame(self.settings_content, fg_color="transparent")
        opt_row.pack(fill="x", padx=10, pady=4)

        ctk.CTkCheckBox(
            opt_row,
            text="Scan Subfolders Recursively",
            variable=self.scan_recursive,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
        ).pack(side="left")

        # PotPlayer path row
        path_row = ctk.CTkFrame(self.settings_content, fg_color="transparent")
        path_row.pack(fill="x", padx=10, pady=(4, 8))

        ctk.CTkLabel(path_row, text="PotPlayer Path:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MAIN, width=100, anchor="w").pack(side="left")

        self.path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.pot_path_var,
            font=ctk.CTkFont(size=11),
            fg_color="#0d1117",
            border_color=COLOR_CARD_BORDER,
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkButton(
            path_row,
            text="Browse",
            width=65,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#21262d",
            hover_color="#30363d",
            command=self.browse_potplayer_exe,
        ).pack(side="right")

        # Initial Log Message
        self.log("🚀 PotPlayer Sub Extractor Studio initialized.")
        if self.controller.is_available():
            self.log(f"✅ PotPlayer detected at: {self.controller.potplayer_exe}")
        else:
            self.log("⚠️ PotPlayer executable not found in default paths! Please locate it in Settings.")

    def log(self, message: str):
        """Append timestamped message to activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.log_textbox.insert("end", formatted)
        self.log_textbox.see("end")

    def clear_log(self):
        """Clear log textbox."""
        self.log_textbox.delete("1.0", "end")

    def _on_speed_slider_change(self, val):
        """Update speed display and badge."""
        speed = round(float(val), 1)
        self.target_speed.set(speed)
        self.speed_val_label.configure(text=f"{speed:.1f}x")
        self.speed_badge.configure(text=f"⚡ {speed:.1f}x Speed")

    def toggle_settings_panel(self):
        """Expand / collapse settings drawer."""
        if self.settings_content.winfo_ismapped():
            self.settings_content.pack_forget()
            self.settings_toggle_btn.configure(text="⚙️ Advanced Settings & PotPlayer Path  [ ▼ ]")
        else:
            self.settings_content.pack(fill="x", pady=(0, 8))
            self.settings_toggle_btn.configure(text="⚙️ Advanced Settings & PotPlayer Path  [ ▲ ]")

    def browse_potplayer_exe(self):
        """Allow user to select custom PotPlayer executable."""
        chosen = filedialog.askopenfilename(
            title="Select PotPlayer Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
        )
        if chosen and os.path.isfile(chosen):
            self.pot_path_var.set(chosen)
            self.controller.set_executable_path(chosen)
            self.log(f"✅ PotPlayer path updated: {chosen}")
            self._update_system_status()

    def _update_system_status(self, is_running=False, status_text=None):
        """Update status pill and metric cards."""
        active_count = len(self.controller.get_active_hwnds())
        self.active_badge.configure(text=f"🎬 {active_count} Players")

        if is_running:
            self.status_pill.configure(text="● RUNNING", text_color="#00e5ff", fg_color="#002d33")
            self.status_detail_label.configure(text=status_text or "Processing videos...")
        elif active_count > 0:
            if self.is_paused_state:
                self.status_pill.configure(text="● PAUSED", text_color=COLOR_ACCENT_AMBER, fg_color="#332000")
                self.status_detail_label.configure(text=f"{active_count} videos paused")
            else:
                self.status_pill.configure(text="● PLAYING", text_color=COLOR_ACCENT_GREEN, fg_color="#003820")
                self.status_detail_label.configure(text=f"{active_count} videos playing @ {self.target_speed.get():.1f}x")
        else:
            self.status_pill.configure(text="● READY", text_color=COLOR_ACCENT_GREEN, fg_color="#003820")
            self.status_detail_label.configure(text=status_text or "Ready to select folder")

    # --- BUTTON 1: ORGANIZE VIDEOS INTO DEDICATED FOLDERS ---
    def on_organize_videos_clicked(self):
        folder = filedialog.askdirectory(title="Select Folder with Videos to Organize into Folders")
        if not folder:
            return

        self.log(f"📁 Organizing videos in: {folder}")
        self._update_system_status(is_running=True, status_text=f"Organizing videos in {os.path.basename(folder)}...")

        def progress_cb(current, total, msg):
            fraction = current / max(1, total)
            self.after(0, lambda: self.progress_bar.set(fraction))
            self.after(0, lambda: self.log(f"📁 {msg}"))

        def worker():
            try:
                results = organize_videos_into_folders(folder, on_progress=progress_cb)
                def done():
                    self.progress_bar.set(1.0)
                    if results:
                        self.log(f"🎉 Successfully organized {len(results)} videos into their own dedicated folders!")
                        self._update_system_status(is_running=False, status_text=f"Organized {len(results)} videos into dedicated folders")
                    else:
                        self.log("ℹ️ All videos in this folder are already in their own dedicated folders.")
                        self._update_system_status(is_running=False, status_text="All videos already organized")
                self.after(0, done)
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Error organizing videos: {e}"))
                self.after(0, lambda: self._update_system_status())

        self.org_thread = threading.Thread(target=worker, daemon=True)
        self.org_thread.start()

    # --- BUTTON 2: SELECT FOLDER & LAUNCH ---
    def on_select_folder_clicked(self):
        if not self.controller.is_available():
            messagebox.showerror(
                "PotPlayer Not Found",
                "Could not find PotPlayer executable.\nPlease click 'Advanced Settings' and select PotPlayer.exe manually.",
            )
            return

        if self.controller.is_running_batch:
            self.controller.cancel_batch()
            self.btn_select_launch.configure(
                text="📂  2. Select Folder & Launch All Videos (12.0x)",
                **STYLE_BTN_CYAN
            )
            self.log("🛑 Batch launch cancellation requested...")
            return

        folder = filedialog.askdirectory(title="Select Folder Containing Videos")
        if not folder:
            return

        self.selected_folder.set(folder)
        self.log(f"📂 Selected Folder: {folder}")

        videos = scan_video_files(folder, recursive=self.scan_recursive.get())
        if not videos:
            self.log(f"⚠️ No video files found in {folder}")
            self._update_system_status(status_text="No video files found")
            return

        self.log(f"🔍 Found {len(videos)} video files across folder & subfolders (Naturally sorted).")
        for i, v in enumerate(videos[:8]):
            rel_name = os.path.relpath(v, folder)
            self.log(f"   [{i+1}] {rel_name}")
        if len(videos) > 8:
            self.log(f"   ... and {len(videos) - 8} more files across subfolders.")

        left, top, right, bottom = get_screen_work_area()
        screen_h = bottom - top
        max_rows = max(1, screen_h // self.tile_min_h.get())
        cols = (len(videos) + max_rows - 1) // max_rows
        self.log(f"📐 Auto-Tiling Layout: {cols} Column(s) × Up to {max_rows} Rows per column")

        # Switch Button 2 to Crimson Cancel Style while running
        self.btn_select_launch.configure(
            text="⏹️  Cancel Launch Operation",
            **STYLE_BTN_CRIMSON
        )
        self._update_system_status(is_running=True, status_text=f"Launching {len(videos)} videos...")

        target_spd = self.target_speed.get()
        min_w = self.tile_min_w.get()
        min_h = self.tile_min_h.get()

        def progress_cb(current, total, msg):
            self.after(0, lambda: self._on_batch_progress(current, total, msg))

        def finish_cb(total_launched):
            self.after(0, lambda: self._on_batch_finished(total_launched))

        def worker():
            try:
                self.controller.launch_and_arrange_batch(
                    video_files=videos,
                    target_speed=target_spd,
                    min_w=min_w,
                    min_h=min_h,
                    on_progress=progress_cb,
                    on_finished=finish_cb,
                )
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Error during batch launch: {e}"))
                self.after(0, lambda: self._on_batch_finished(0))

        self.batch_thread = threading.Thread(target=worker, daemon=True)
        self.batch_thread.start()

    def _on_batch_progress(self, current, total, msg):
        fraction = current / max(1, total)
        self.progress_bar.set(fraction)
        self.log(f"⚙️ {msg}")
        self._update_system_status(is_running=True, status_text=f"Processed {current}/{total} videos")

    def _on_batch_finished(self, total_launched):
        self.progress_bar.set(1.0)
        # Restore Button 2 to Cyan Glass Style
        self.btn_select_launch.configure(
            text="📂  2. Select Folder & Launch All Videos (12.0x)",
            **STYLE_BTN_CYAN
        )
        self.is_paused_state = False
        # Restore Button 4 to Amber Glass Style
        self.btn_toggle_play.configure(
            text="⏸️  4. Pause All Players",
            **STYLE_BTN_AMBER
        )
        self.log(f"🎉 Batch setup completed! {total_launched} PotPlayer instances running at {self.target_speed.get():.1f}x.")
        self._update_system_status()

    # --- BUTTON 3: SAVE SUBTITLES (Alt + S) ---
    def on_save_subtitles_clicked(self):
        active_hwnds = self.controller.get_active_hwnds()
        if not active_hwnds:
            self.log("⚠️ No active PotPlayer windows found to save subtitles.")
            self._update_system_status(status_text="No active players to save subtitles")
            return

        self.log(f"💾 Triggering Save Subtitles (Alt + S) across {len(active_hwnds)} players...")
        self._update_system_status(is_running=True, status_text=f"Saving subtitles on {len(active_hwnds)} players...")

        def progress_cb(current, total, msg):
            fraction = current / max(1, total)
            self.after(0, lambda: self.progress_bar.set(fraction))
            self.after(0, lambda: self.log(f"💾 {msg}"))

        def finish_cb(saved_count):
            def done():
                self.progress_bar.set(1.0)
                self.log(f"✅ Alt + S Subtitle save completed for {saved_count} players!")
                self._update_system_status(status_text=f"Subtitles saved on {saved_count} players")
            self.after(0, done)

        def worker():
            try:
                self.controller.save_subtitles_all(
                    on_progress=progress_cb,
                    on_finished=finish_cb,
                )
            except Exception as e:
                self.after(0, lambda: self.log(f"❌ Error saving subtitles: {e}"))
                self.after(0, lambda: self._update_system_status())

        self.sub_thread = threading.Thread(target=worker, daemon=True)
        self.sub_thread.start()

    # --- BUTTON 4: PAUSE / PLAY TOGGLE ---
    def on_toggle_play_pause_clicked(self):
        active_hwnds = self.controller.get_active_hwnds()
        if not active_hwnds:
            self.log("⚠️ No active PotPlayer windows found to pause/play.")
            self._update_system_status(status_text="No active players to pause/resume")
            return

        new_is_paused = self.controller.toggle_play_pause()
        self.is_paused_state = new_is_paused

        if new_is_paused:
            # Switch to Emerald Resume Style
            self.btn_toggle_play.configure(
                text="▶️  4. Resume All Players",
                **STYLE_BTN_EMERALD
            )
            self.log(f"⏸️ PAUSED all {len(active_hwnds)} PotPlayer instances.")
        else:
            # Switch to Amber Pause Style
            self.btn_toggle_play.configure(
                text="⏸️  4. Pause All Players",
                **STYLE_BTN_AMBER
            )
            self.log(f"▶️ RESUMED playback on all {len(active_hwnds)} PotPlayer instances.")

        self._update_system_status()

    # --- BUTTON 5: CLOSE ALL PLAYERS ---
    def on_close_all_clicked(self):
        active_count = len(self.controller.get_active_hwnds())
        if active_count == 0:
            self.log("ℹ️ No active PotPlayer windows to close.")
            return

        self.log(f"🛑 Closing all {active_count} PotPlayer instances...")
        closed = self.controller.close_all()
        self.progress_bar.set(0)
        self.is_paused_state = False
        # Ensure buttons keep their styles
        self.btn_organize_videos.configure(
            text="📁  1. Organize Videos into Dedicated Folders (1 Video -> 1 Folder)",
            **STYLE_BTN_TEAL
        )
        self.btn_select_launch.configure(
            text="📂  2. Select Folder & Launch All Videos (12.0x)",
            **STYLE_BTN_CYAN
        )
        self.btn_save_subtitles.configure(
            text="💾  3. Save Subtitles (Alt + S)",
            **STYLE_BTN_PURPLE
        )
        self.btn_toggle_play.configure(
            text="⏸️  4. Pause All Players",
            **STYLE_BTN_AMBER
        )
        self.btn_close_all.configure(
            text="🛑  5. Close All Players",
            **STYLE_BTN_CRIMSON
        )
        self.log(f"✅ Closed {closed} PotPlayer windows/processes.")
        self._update_system_status(status_text=f"Closed {closed} players")


def run_app():
    """Launch the main GUI application loop."""
    app = ModernSubExtractorApp()
    app.mainloop()