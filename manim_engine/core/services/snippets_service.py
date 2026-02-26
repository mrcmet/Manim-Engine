"""Service for persisting and managing code snippets."""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from app.constants import SNIPPETS_FILE
from core.models.snippet import Snippet

logger = logging.getLogger(__name__)


class SnippetsService:
    """Manages CRUD operations for code snippets stored as JSON.

    The list is loaded lazily on first access and cached in memory.
    Subsequent calls to :meth:`load` return the cached list without
    re-reading from disk.  :meth:`save` always writes the current
    in-memory state back to disk.

    Args:
        snippets_file: Path to the JSON file.  Defaults to
            ``~/.manim_engine/snippets.json``.  Pass a different path in
            tests to avoid touching the real file.
    """

    def __init__(self, snippets_file: Path = SNIPPETS_FILE) -> None:
        self._snippets_file = snippets_file
        self._snippets: Optional[list[Snippet]] = None

    # ------------------------------------------------------------------
    # Core persistence
    # ------------------------------------------------------------------

    def load(self) -> list[Snippet]:
        """Return the current list of snippets, loading from disk if needed.

        Returns:
            List of :class:`Snippet` objects (may be empty).
        """
        if self._snippets is not None:
            return self._snippets

        if self._snippets_file.exists():
            try:
                with open(self._snippets_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    self._snippets = [Snippet.from_dict(item) for item in data]
                else:
                    logger.warning(
                        "snippets.json has unexpected structure; starting fresh."
                    )
                    self._snippets = []
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                logger.warning("Failed to load snippets: %s. Starting fresh.", exc)
                self._snippets = []
        else:
            self._snippets = []

        return self._snippets

    def save(self) -> None:
        """Write the current in-memory snippet list to disk."""
        snippets = self.load()  # ensure _snippets is populated
        self._snippets_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._snippets_file, "w", encoding="utf-8") as fh:
            json.dump([s.to_dict() for s in snippets], fh, indent=2)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def add(
        self,
        name: str,
        code: str,
        description: Optional[str] = None,
    ) -> Snippet:
        """Create a new snippet, persist it, and return it.

        Args:
            name: Display name (must be non-empty).
            code: Manim Python source code (must be non-empty).
            description: Optional freeform description.

        Returns:
            The newly created :class:`Snippet`.

        Raises:
            ValueError: If *name* or *code* is empty.
        """
        if not name.strip():
            raise ValueError("Snippet name must not be empty.")
        if not code.strip():
            raise ValueError("Snippet code must not be empty.")

        snippet = Snippet(
            id=str(uuid.uuid4()),
            name=name.strip(),
            code=code,
            description=description.strip() if description else None,
        )
        self.load().append(snippet)
        self.save()
        return snippet

    def update(
        self,
        snippet_id: str,
        name: str,
        code: str,
        description: Optional[str] = None,
    ) -> Optional[Snippet]:
        """Update an existing snippet in place.

        Args:
            snippet_id: UUID of the snippet to update.
            name: New display name.
            code: New source code.
            description: New description (pass ``None`` to clear).

        Returns:
            The updated :class:`Snippet`, or ``None`` if not found.
        """
        snippets = self.load()
        for snippet in snippets:
            if snippet.id == snippet_id:
                snippet.name = name.strip()
                snippet.code = code
                snippet.description = description.strip() if description else None
                self.save()
                return snippet
        return None

    def delete(self, snippet_id: str) -> bool:
        """Remove a snippet by ID.

        Args:
            snippet_id: UUID of the snippet to remove.

        Returns:
            ``True`` if the snippet was found and deleted, ``False`` otherwise.
        """
        snippets = self.load()
        original_count = len(snippets)
        self._snippets = [s for s in snippets if s.id != snippet_id]
        if len(self._snippets) < original_count:
            self.save()
            return True
        return False

    def get(self, snippet_id: str) -> Optional[Snippet]:
        """Return a single snippet by ID.

        Args:
            snippet_id: UUID of the snippet to retrieve.

        Returns:
            The matching :class:`Snippet`, or ``None`` if not found.
        """
        return next((s for s in self.load() if s.id == snippet_id), None)
