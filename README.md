# ⚡ Sub Extractor

A high-performance Windows automation tool designed to **extract embedded subtitle files from videos in bulk using PotPlayer**.

---

> [!IMPORTANT]
> **Prerequisites**: You must have **[PotPlayer](https://potplayer.daum.net/)** (64-bit or 32-bit) installed on your computer to use this application.

---

## 📖 Overview & Purpose

**Sub Extractor** is built specifically to automate and accelerate extracting embedded subtitles from video files (such as anime, movies, or TV series) in bulk.

Instead of opening each video manually, unmuting, waiting, and navigating menus, this application automates the complete extraction workflow:
1. Organizing video files into isolated dedicated folders.
2. Opening multiple player instances simultaneously in PotPlayer (up to **20 videos per batch**) with **H/W Built-in DXVA Decoder & Hardware Acceleration** active on every video.
3. Auto-tiling all windows in a **10 Rows × 2 Columns table matrix** with zero overlapping.
4. Automatically silencing audio tracks (mute).
5. Accelerating playback up to **12.0x** so subtitle streams load instantaneously.
6. Automating the **`Alt + S`** subtitle save command and dialog confirmation.

---

## 🛠️ Step-by-Step User Guide (How to Use)

### 📌 Step 0: Prepare Your Videos (Up to 20 Videos per Folder)
Place the video files from which you want to extract embedded subtitles into a folder (e.g., `C:\MyVideos`).

> [!CAUTION]
> **20 Videos Batch Limit & System Processing Power Notice**: 
> Running more than **20 videos simultaneously at 12.0x speed** requires intense CPU/GPU decoding power. To prevent computer overload, severe lag, or media decoder crashes:
> - Sub Extractor processes a **maximum of 20 videos per batch** (arranged in a clean 10 Rows × 2 Columns table grid).
> - If a selected folder contains **21 or more videos**, a themed warning dialog will appear giving you the option to **Stop Process & Exit** or continue with the first 20 videos.
> - For large collections, **manually organize videos into separate folders of up to 20 videos each**, and run each folder separately at different times.

---

### 📁 Step 1: Click `1. Organize Videos into Dedicated Folders (1 Video -> 1 Folder)`
- **What this does**: Automatically scans your folder, creates a dedicated subfolder for each video matching its filename (e.g. `Episode_01.mkv` ➔ `Episode_01/`), and moves the video (along with any accompanying files) inside.
- **Why this is important**: When multiple video files reside in the same folder, PotPlayer automatically loads and plays the next episode in the series when a video finishes. Isolating each video in its own folder **prevents PotPlayer from auto-playing adjacent videos**, ensuring a clean and controlled subtitle extraction environment.

---

### 📂 Step 2: Click `2. Select Folder & Launch All Videos (12.0x)`
- **What this does**:
  1. Scans your selected folder and subfolders in natural alphanumeric order (`ep1`, `ep2`, `ep10`...).
  2. If 21+ videos are detected, displays the custom glassmorphic warning modal with a **`Stop Process & Exit Warning`** button.
  3. Enforces **H/W Built-in DXVA Hardware Decoding** on every instance to offload video decoding to your GPU.
  4. Opens each video in its own separate PotPlayer instance (`/new`).
  5. **Auto-Mutes** audio playback so multiple video tracks do not play sound simultaneously.
  6. **Auto-Tiles in 10-Row × 2-Column Table Grid**: Column 1 (Videos 1 to 10), Column 2 (Videos 11 to 20) with zero overlapping.
  7. **Boosts playback speed to 12.0x** so subtitle streams initialize instantly.
  8. An active background **Layout Watchdog** continuously keeps all windows clamped into their exact grid slots throughout playback.

---

### 💾 Step 3: Extract & Save Subtitles (`Alt + S`)

> [!WARNING]
> **Playback Completion Required**: 
> You must **confirm that all videos have finished playing completely (played to the end at 12.0x)** before clicking the Save Subtitles button. If a video is still playing when saving subtitles, PotPlayer will **only save the subtitles up to the current playback timestamp** of that video rather than the complete full-length subtitle track.

You have two flexible ways to save your subtitles:

1. **One-Click Automated Batch Save**:
   - Click **`💾 3. Save Subtitles (Alt + S)`**.
   - The app will rapidly loop through every open video window one by one, trigger the **`Alt + S`** command, capture the Windows Save Dialog, and automatically confirm (`Enter`) the save.
2. **Manual Individual Save (Custom Subtitle Formats)**:
   - Click on any specific PotPlayer window.
   - Press **`Alt + S`** on your keyboard to open the PotPlayer "Save Subtitle As" dialog.
   - Choose your preferred subtitle format/encoding (e.g. `.srt`, `.ass`, `.vtt`, `.sub`), pick a destination, and save.

---

### ⏸️ Step 4: Click `4. Pause All Players` / `▶️ 4. Resume All Players`
- **What this does**: Synchronously pauses or resumes playback across all open PotPlayer instances at once using state-aware Win32 IPC messaging (`10014`), keeping all videos in sync.

---

### 🛑 Step 5: Click `5. Close All Players`
- **What this does**: Closes all active PotPlayer instances and terminates any orphaned background video playback processes with a single click, leaving Sub Extractor open and ready for your next batch.

---

## 🎛️ Additional Features & Controls

### 1. Live Status Card & Metric Badges
- **Status Indicator Pill**: Displays real-time operational state:
  - `● READY` (Idle and waiting for input)
  - `● RUNNING` (Batch launching, organizing folders, or extracting subtitles)
  - `● PLAYING` (Active player instances running)
  - `● PAUSED` (All player instances frozen in sync)
- **Active Players Badge (`🎬 N Players`)**: Live counter of running PotPlayer windows.
- **Speed Multiplier Badge (`⚡ 12.0x Speed`)**: Displays the active speed boost factor.

### 2. Live Activity Log & Terminal
- Provides a timestamped console feed tracking every action, file movement, auto-tiling position `(x, y)`, and subtitle extraction confirmation.
- Includes a **Clear** button to reset the terminal output.

### 3. Advanced Settings Drawer (`⚙️ Advanced Settings & PotPlayer Path [ ▼ ]`)
- **Target Speed Multiplier Slider**: Adjust playback speed acceleration anywhere from `1.0x` (normal) up to `12.0x` (maximum speed).
- **Scan Subfolders Recursively Checkbox**: Toggle whether to scan nested subdirectories when loading videos.
- **PotPlayer Path Locator**: Auto-detects standard PotPlayer 64-bit and 32-bit installations, with a **Browse** button to select a custom `PotPlayerMini64.exe` or `PotPlayer.exe` path.

---

## 🚀 Installation & Running

### Option A: Windows Setup Wizard Installer (Recommended)
Download and run **`SubExtractor_Setup.exe`** from the `dist/` folder.
- Default Installation Path: `C:\Program Files\Sub Extractor`
- Creates **Desktop** and **Start Menu** shortcuts with the high-resolution app icon.
- Registers in **Windows Settings > Installed Apps (Add or remove programs)** with a dedicated GUI Uninstaller.

### Option B: Standalone Portable Binary
Run **`dist/SubExtractor.exe`** directly without installation.

### Option C: Run from Python Source Code
```bash
git clone https://github.com/Sandika-2003/Sub-Extractor.git
cd Sub-Extractor
pip install -r requirements.txt
python main.py
```

### Build Executables & Installer from Source:
```bash
# Build standalone portable .exe (SubExtractor.exe)
python build_exe.py

# Build complete Windows Setup Wizard + Uninstaller suite (SubExtractor_Setup.exe)
python build_installer.py
```

---

## 📄 License

This project is open-source and licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.