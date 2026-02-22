import json
from pathlib import Path

from core.services.project_service import ProjectService


class TestProjectService:
    def test_create_project(self, tmp_path):
        service = ProjectService(projects_dir=tmp_path)
        project = service.create_project("Test Project", "A test")
        assert project.name == "Test Project"
        assert project.description == "A test"
        assert (tmp_path / project.id / "project.json").exists()
        assert (tmp_path / project.id / "versions").is_dir()

    def test_open_project(self, tmp_path):
        service = ProjectService(projects_dir=tmp_path)
        created = service.create_project("My Project")
        loaded = service.open_project(created.id)
        assert loaded.id == created.id
        assert loaded.name == "My Project"

    def test_list_projects(self, tmp_path):
        service = ProjectService(projects_dir=tmp_path)
        service.create_project("Project A")
        service.create_project("Project B")
        projects = service.list_projects()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"Project A", "Project B"}

    def test_delete_project(self, tmp_path):
        service = ProjectService(projects_dir=tmp_path)
        project = service.create_project("To Delete")
        service.delete_project(project.id)
        assert not (tmp_path / project.id).exists()
        assert len(service.list_projects()) == 0

    def test_update_project(self, tmp_path):
        service = ProjectService(projects_dir=tmp_path)
        project = service.create_project("Original")
        project.name = "Updated"
        service.update_project(project)
        loaded = service.open_project(project.id)
        assert loaded.name == "Updated"
