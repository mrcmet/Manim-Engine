from pathlib import Path

from core.services.project_service import ProjectService
from core.services.version_service import VersionService


class TestVersionService:
    def _setup_project(self, tmp_path):
        ps = ProjectService(projects_dir=tmp_path)
        project = ps.create_project("Test")
        vs = VersionService(projects_dir=tmp_path)
        return project, vs

    def test_create_version(self, tmp_path):
        project, vs = self._setup_project(tmp_path)
        code = "from manim import *\nclass S(Scene): pass"
        version = vs.create_version(project.id, code, source="ai", prompt="test")
        assert version.project_id == project.id
        assert version.code == code
        assert version.source == "ai"
        assert version.prompt == "test"

    def test_get_version(self, tmp_path):
        project, vs = self._setup_project(tmp_path)
        code = "x = 5"
        created = vs.create_version(project.id, code)
        loaded = vs.get_version(project.id, created.id)
        assert loaded.id == created.id
        assert loaded.code == code

    def test_list_versions(self, tmp_path):
        project, vs = self._setup_project(tmp_path)
        vs.create_version(project.id, "v1")
        vs.create_version(project.id, "v2")
        versions = vs.list_versions(project.id)
        assert len(versions) == 2

    def test_parent_chain(self, tmp_path):
        project, vs = self._setup_project(tmp_path)
        v1 = vs.create_version(project.id, "v1")
        v2 = vs.create_version(project.id, "v2", parent_version_id=v1.id)
        loaded = vs.get_version(project.id, v2.id)
        assert loaded.parent_version_id == v1.id

    def test_set_video_path(self, tmp_path):
        project, vs = self._setup_project(tmp_path)
        v = vs.create_version(project.id, "code")
        vs.set_video_path(project.id, v.id, Path("/tmp/video.mp4"))
        loaded = vs.get_version(project.id, v.id)
        assert loaded.video_path == Path("/tmp/video.mp4")
