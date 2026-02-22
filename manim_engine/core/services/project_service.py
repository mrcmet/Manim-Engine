import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.constants import PROJECTS_DIR
from core.models.project import Project


class ProjectService:
    def __init__(self, projects_dir: Path = PROJECTS_DIR):
        self._projects_dir = projects_dir

    def create_project(self, name: str, description: str = "") -> Project:
        project_id = str(uuid.uuid4())
        now = datetime.now()
        project_dir = self._projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "versions").mkdir(exist_ok=True)

        project = Project(
            id=project_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            current_version_id=None,
            directory_path=project_dir,
        )
        self._save_project(project)
        return project

    def open_project(self, project_id: str) -> Project:
        project_file = self._projects_dir / project_id / "project.json"
        with open(project_file, "r") as f:
            data = json.load(f)
        return Project.from_dict(data)

    def list_projects(self) -> list[Project]:
        projects = []
        if not self._projects_dir.exists():
            return projects
        for project_dir in self._projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            project_file = project_dir / "project.json"
            if project_file.exists():
                with open(project_file, "r") as f:
                    data = json.load(f)
                projects.append(Project.from_dict(data))
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        return projects

    def delete_project(self, project_id: str) -> None:
        project_dir = self._projects_dir / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)

    def update_project(self, project: Project) -> None:
        project.updated_at = datetime.now()
        self._save_project(project)

    def _save_project(self, project: Project) -> None:
        project_file = project.directory_path / "project.json"
        with open(project_file, "w") as f:
            json.dump(project.to_dict(), f, indent=2)
