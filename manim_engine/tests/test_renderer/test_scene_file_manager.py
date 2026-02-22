from pathlib import Path

from renderer.scene_file_manager import SceneFileManager


class TestSceneFileManager:
    def test_write_scene_file(self):
        mgr = SceneFileManager()
        try:
            code = "from manim import *\nclass S(Scene): pass"
            path = mgr.write_scene_file(code, "TestScene")
            assert path.exists()
            assert path.read_text() == code
            assert "TestScene" in path.name
        finally:
            mgr.cleanup()

    def test_find_output_video(self, tmp_path):
        mgr = SceneFileManager()
        scene_file = tmp_path / "TestScene.py"
        scene_file.write_text("pass")
        # Create mock Manim output structure
        video_dir = tmp_path / "media" / "videos" / "TestScene" / "480p15"
        video_dir.mkdir(parents=True)
        video_file = video_dir / "TestScene.mp4"
        video_file.write_text("fake video")

        result = mgr.find_output_video(scene_file, "TestScene", "l", tmp_path / "media")
        assert result is not None
        assert result.name == "TestScene.mp4"
        mgr.cleanup()

    def test_find_output_video_not_found(self, tmp_path):
        mgr = SceneFileManager()
        scene_file = tmp_path / "Test.py"
        scene_file.write_text("pass")
        result = mgr.find_output_video(scene_file, "Test", "l", tmp_path / "media")
        assert result is None
        mgr.cleanup()

    def test_copy_to_project(self, tmp_path):
        mgr = SceneFileManager()
        source = tmp_path / "source.mp4"
        source.write_text("video data")
        dest_dir = tmp_path / "output"
        result = mgr.copy_to_project(source, dest_dir)
        assert result.exists()
        assert result.read_text() == "video data"
        mgr.cleanup()

    def test_cleanup(self):
        mgr = SceneFileManager()
        temp_dir = mgr.temp_dir
        assert temp_dir.exists()
        mgr.cleanup()
        assert not temp_dir.exists()
