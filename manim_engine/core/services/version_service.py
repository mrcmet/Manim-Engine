import json
import uuid
from datetime import datetime
from pathlib import Path

from app.constants import PROJECTS_DIR
from core.models.version import Version


class VersionService:
    def __init__(self, projects_dir: Path = PROJECTS_DIR):
        self._projects_dir = projects_dir

    def create_version(
        self,
        project_id: str,
        code: str,
        prompt: str | None = None,
        source: str = "manual_edit",
        parent_version_id: str | None = None,
    ) -> Version:
        version_id = str(uuid.uuid4())
        now = datetime.now()
        version_dir = self._projects_dir / project_id / "versions" / version_id
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "output").mkdir(exist_ok=True)

        version = Version(
            id=version_id,
            project_id=project_id,
            code=code,
            prompt=prompt,
            source=source,
            parent_version_id=parent_version_id,
            created_at=now,
            video_path=None,
            thumbnail_path=None,
        )

        # Write scene file
        scene_file = version_dir / "scene.py"
        scene_file.write_text(code, encoding="utf-8")

        # Write version metadata
        self._save_version(version)
        return version

    def get_version(self, project_id: str, version_id: str) -> Version:
        version_file = (
            self._projects_dir / project_id / "versions" / version_id / "version.json"
        )
        with open(version_file, "r") as f:
            data = json.load(f)
        # Also read the scene code from file
        scene_file = (
            self._projects_dir / project_id / "versions" / version_id / "scene.py"
        )
        if scene_file.exists():
            data["code"] = scene_file.read_text(encoding="utf-8")
        return Version.from_dict(data)

    def list_versions(self, project_id: str) -> list[Version]:
        versions_dir = self._projects_dir / project_id / "versions"
        versions = []
        if not versions_dir.exists():
            return versions
        for version_dir in versions_dir.iterdir():
            if not version_dir.is_dir():
                continue
            version_file = version_dir / "version.json"
            if version_file.exists():
                with open(version_file, "r") as f:
                    data = json.load(f)
                scene_file = version_dir / "scene.py"
                if scene_file.exists():
                    data["code"] = scene_file.read_text(encoding="utf-8")
                versions.append(Version.from_dict(data))
        versions.sort(key=lambda v: v.created_at)
        return versions

    def set_video_path(
        self, project_id: str, version_id: str, video_path: Path
    ) -> None:
        version = self.get_version(project_id, version_id)
        version.video_path = video_path
        self._save_version(version)

    def _save_version(self, version: Version) -> None:
        version_dir = (
            self._projects_dir
            / version.project_id
            / "versions"
            / version.id
        )
        version_file = version_dir / "version.json"
        with open(version_file, "w") as f:
            json.dump(version.to_dict(), f, indent=2)
