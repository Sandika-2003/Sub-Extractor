"""
Unit and Integration Tests for PotPlayer Sub Extractor.
"""

import os
import sys
import unittest

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.potplayer_controller import (
    natural_sort_key,
    scan_video_files,
    find_potplayer_path,
    calculate_window_positions,
    get_screen_work_area,
    ensure_hardware_dxva_enabled,
    PotPlayerController,
    POT_CMD_PLAY_PAUSE,
    POT_CMD_PAUSE,
    POT_CMD_PLAY,
    POT_CMD_MUTE,
    POT_CMD_SPEED_UP,
    MAX_GRID_ROWS,
    MAX_GRID_COLS,
    MAX_VIDEOS_PER_BATCH,
)


class TestPotPlayerController(unittest.TestCase):

    def test_natural_sorting(self):
        """Verify natural sorting order for filenames like video 1, video 2, video 10."""
        unsorted = ["video 10.mp4", "video 1.mp4", "video 2.mp4", "video 20.mp4", "video 3.mp4", "video 11.mp4"]
        expected = ["video 1.mp4", "video 2.mp4", "video 3.mp4", "video 10.mp4", "video 11.mp4", "video 20.mp4"]
        sorted_list = sorted(unsorted, key=natural_sort_key)
        self.assertEqual(sorted_list, expected)

    def test_calculate_window_positions_10x2_columns(self):
        """Verify 10-rows x 2-columns table grid stacking calculation (up to 20 videos)."""
        positions = calculate_window_positions(20)
        self.assertEqual(len(positions), 20)
        
        # Items in Column 1 (0 to 9) should share same X coordinate
        for r in range(1, 10):
            self.assertEqual(positions[r][0], positions[0][0])
            self.assertTrue(positions[r][1] > positions[r-1][1])

        # Item 10 should begin Column 2 (x shifted by column width, y reset to top)
        col_w = positions[0][2]
        self.assertEqual(positions[10][0], positions[0][0] + col_w)
        self.assertEqual(positions[10][1], positions[0][1])

        # Items in Column 2 (10 to 19) should share same X coordinate
        for r in range(11, 20):
            self.assertEqual(positions[r][0], positions[10][0])
            self.assertTrue(positions[r][1] > positions[r-1][1])

    def test_ensure_hardware_dxva_enabled(self):
        """Check that DXVA hardware decoding registry settings are applied cleanly."""
        res = ensure_hardware_dxva_enabled()
        self.assertTrue(res)

    def test_potplayer_detection(self):
        """Check that PotPlayer executable is detected or can be manually passed."""
        path = find_potplayer_path()
        self.assertTrue(path is not None, "PotPlayer executable should be found on this system.")
        ctrl = PotPlayerController(path)
        self.assertTrue(ctrl.is_available())

    def test_recursive_subfolder_scanning(self):
        """Verify scanning of videos in nested subfolders."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            sub1 = os.path.join(temp_dir, "Season 01")
            sub2 = os.path.join(temp_dir, "Season 02")
            os.makedirs(sub1)
            os.makedirs(sub2)
            
            with open(os.path.join(temp_dir, "root_video.mp4"), "w") as f: f.write("0")
            with open(os.path.join(sub1, "ep02.mp4"), "w") as f: f.write("0")
            with open(os.path.join(sub1, "ep01.mp4"), "w") as f: f.write("0")
            with open(os.path.join(sub2, "ep01.mkv"), "w") as f: f.write("0")
            
            found = scan_video_files(temp_dir, recursive=True)
            self.assertEqual(len(found), 4)
            
            rel_paths = [os.path.relpath(p, temp_dir).replace(os.sep, "/") for p in found]
            expected = ["root_video.mp4", "Season 01/ep01.mp4", "Season 01/ep02.mp4", "Season 02/ep01.mkv"]
            self.assertEqual(rel_paths, expected)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_organize_videos_into_folders(self):
        """Verify creating dedicated folders and moving videos inside."""
        import tempfile
        import shutil
        from src.potplayer_controller import organize_videos_into_folders

        temp_dir = tempfile.mkdtemp()
        try:
            v1 = os.path.join(temp_dir, "MyMovie.mp4")
            v2 = os.path.join(temp_dir, "Show_S01E01.mkv")
            with open(v1, "w") as f: f.write("0")
            with open(v2, "w") as f: f.write("0")

            results = organize_videos_into_folders(temp_dir)
            self.assertEqual(len(results), 2)
            self.assertTrue(os.path.isdir(os.path.join(temp_dir, "MyMovie")))
            self.assertTrue(os.path.isfile(os.path.join(temp_dir, "MyMovie", "MyMovie.mp4")))
            self.assertTrue(os.path.isdir(os.path.join(temp_dir, "Show_S01E01")))
            self.assertTrue(os.path.isfile(os.path.join(temp_dir, "Show_S01E01", "Show_S01E01.mkv")))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()