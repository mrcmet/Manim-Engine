from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Project:
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    current_version_id: str | None
    directory_path: Path

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_version_id": self.current_version_id,
            "directory_path": str(self.directory_path),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            current_version_id=data.get("current_version_id"),
            directory_path=Path(data["directory_path"]),
        )
