# PotPlayer Sub Extractor Studio

A high-performance Windows desktop automation tool and subtitle extraction companion for **PotPlayer**.

---

## ✨ Key Features

1. 📁 **1. Organize Videos into Dedicated Folders (1 Video -> 1 Folder)**: Automatically scans a chosen directory and organizes each video into its own dedicated folder matching the filename (along with matching subtitle files) with non-intrusive status logging.
2. 📂 **2. Select Folder & Launch All Videos (12.0x)**: Opens all videos in naturally sorted alphanumeric order, mutes audio, auto-tiles them vertically in columns (320x100 px), and boosts playback speed to 12.0x.
3. 💾 **3. Save Subtitles (Alt + S)**: Automated rapid Alt + S keystroke dispatch with automatic Save Dialog capture & Enter confirmation across all instances.
4. ⏸️/▶️ **4. Synchronized Pause & Resume**: State-aware Play/Pause toggle command (10014) keeping all video instances in sync.
5. 🛑 **5. One-Click Close All**: Safely closes all PotPlayer instances and background processes while protecting the application itself.

---

## 💎 Design & Automation Highlights
- **Real-Time Layout Watchdog**: Actively monitors player windows and prevents video decoder auto-fit events from breaking the column grid layout.
- **Glassmorphic UI**: Translucent dark glass badges with permanent color palettes built on CustomTkinter.
- **Natural Order Sorting**: Human-friendly alphanumeric sorting (ideo 1, ideo 2, ideo 10).

---

## 🚀 Installation & Running

### Requirements
- Windows 10 / 11 (64-bit)
- Python 3.10+ (or use the standalone .exe)
- PotPlayer (64-bit or 32-bit)

### Setup (Source Code)
`ash
git clone https://github.com/Sandika-2003/Sub-Extractor.git
cd Sub-Extractor
pip install -r requirements.txt
python main.py
`

### Build Standalone Executable
`ash
python build_exe.py
`
The compiled single-file binary will be generated inside dist/PotPlayerSubExtractor.exe.

---

## 🛠️ Tech Stack
- **UI Framework**: customtkinter, Pillow
- **Windows Automation**: pywin32, psutil, pycaw, ctypes
- **Packaging**: PyInstaller
