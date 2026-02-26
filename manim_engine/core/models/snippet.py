"""Data model for a code snippet."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Snippet:
    """Represents a saved code snippet.

    Attributes:
        id: UUID4 string uniquely identifying the snippet.
        name: Human-readable display name.
        code: The Manim Python source code.
        description: Optional freeform description.
        preview_image: Optional path to a preview image (reserved for future use).
    """

    id: str
    name: str
    code: str
    description: Optional[str] = None
    preview_image: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary for JSON persistence."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "preview_image": self.preview_image,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        """Deserialise from a plain dictionary loaded from JSON.

        Args:
            data: Dictionary with at least 'id', 'name', and 'code' keys.

        Returns:
            A new Snippet instance.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            code=data["code"],
            description=data.get("description"),
            preview_image=data.get("preview_image"),
        )
