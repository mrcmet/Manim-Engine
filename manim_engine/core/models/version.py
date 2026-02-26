from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Version:
    id: str
    project_id: str
    code: str
    prompt: str | None
    source: str  # "ai" | "manual_edit" | "snippet"
    parent_version_id: str | None
    created_at: datetime
    video_path: Path | None
    thumbnail_path: Path | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "code": self.code,
            "prompt": self.prompt,
            "source": self.source,
            "parent_version_id": self.parent_version_id,
            "created_at": self.created_at.isoformat(),
            "video_path": str(self.video_path) if self.video_path else None,
            "thumbnail_path": str(self.thumbnail_path) if self.thumbnail_path else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Version":
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            code=data.get("code", ""),
            prompt=data.get("prompt"),
            source=data.get("source", "manual_edit"),
            parent_version_id=data.get("parent_version_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            video_path=Path(data["video_path"]) if data.get("video_path") else None,
            thumbnail_path=Path(data["thumbnail_path"]) if data.get("thumbnail_path") else None,
        )
