"""Tests for SnippetsService CRUD and persistence."""

import json
import pytest

from core.services.snippets_service import SnippetsService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service(tmp_path):
    """Return a SnippetsService backed by a temp file (no disk side-effects)."""
    return SnippetsService(snippets_file=tmp_path / "snippets.json")


@pytest.fixture
def service_with_one(tmp_path):
    """Return a service that already has one snippet."""
    svc = SnippetsService(snippets_file=tmp_path / "snippets.json")
    svc.add("Circle", "class C(Scene): pass", "A circle")
    return svc


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

def test_load_empty(service):
    snippets = service.load()
    assert snippets == []


def test_load_returns_cached(tmp_path):
    """Second call to load() should not re-read disk."""
    path = tmp_path / "snippets.json"
    svc = SnippetsService(snippets_file=path)
    first = svc.load()
    # Corrupt the file on disk after first load
    path.write_text("INVALID JSON")
    second = svc.load()
    # Should still return the cached (empty) list, not raise
    assert second is first


def test_load_invalid_json(tmp_path):
    """Corrupted JSON produces an empty list (no crash)."""
    path = tmp_path / "snippets.json"
    path.write_text("not valid json at all")
    svc = SnippetsService(snippets_file=path)
    result = svc.load()
    assert result == []


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_add_snippet(service):
    snippet = service.add("My Snippet", "class X(Scene): pass")
    assert snippet.name == "My Snippet"
    assert snippet.code == "class X(Scene): pass"
    assert snippet.description is None
    assert len(snippet.id) > 0


def test_add_persists(tmp_path):
    """Snippet saved by one service instance is visible to a fresh instance."""
    path = tmp_path / "snippets.json"
    svc1 = SnippetsService(snippets_file=path)
    added = svc1.add("Persisted", "pass", "desc")

    svc2 = SnippetsService(snippets_file=path)
    loaded = svc2.load()
    assert len(loaded) == 1
    assert loaded[0].id == added.id
    assert loaded[0].name == "Persisted"


def test_add_raises_on_empty_name(service):
    with pytest.raises(ValueError, match="name"):
        service.add("", "pass")


def test_add_raises_on_empty_code(service):
    with pytest.raises(ValueError, match="code"):
        service.add("Valid name", "   ")


def test_description_optional(service):
    snippet = service.add("No desc", "pass")
    assert snippet.description is None

    snippet2 = service.add("With desc", "pass", "some description")
    assert snippet2.description == "some description"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_snippet(service_with_one):
    original = service_with_one.load()[0]
    updated = service_with_one.update(
        original.id, "New Name", "new_code()", "new desc"
    )
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.code == "new_code()"
    assert updated.description == "new desc"

    # Verify the in-memory list reflects the change
    reloaded = service_with_one.load()
    assert reloaded[0].name == "New Name"


def test_update_nonexistent(service):
    result = service.update("nonexistent-id", "Name", "code")
    assert result is None


def test_update_persists(tmp_path):
    path = tmp_path / "snippets.json"
    svc = SnippetsService(snippets_file=path)
    s = svc.add("Orig", "pass")

    svc.update(s.id, "Updated", "new_pass()")

    svc2 = SnippetsService(snippets_file=path)
    assert svc2.load()[0].name == "Updated"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_snippet(service_with_one):
    original = service_with_one.load()[0]
    deleted = service_with_one.delete(original.id)
    assert deleted is True
    assert service_with_one.load() == []


def test_delete_nonexistent(service):
    result = service.delete("ghost-id")
    assert result is False


def test_delete_persists(tmp_path):
    path = tmp_path / "snippets.json"
    svc = SnippetsService(snippets_file=path)
    s = svc.add("ToDelete", "pass")
    svc.delete(s.id)

    svc2 = SnippetsService(snippets_file=path)
    assert svc2.load() == []


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_snippet(service_with_one):
    existing = service_with_one.load()[0]
    found = service_with_one.get(existing.id)
    assert found is not None
    assert found.id == existing.id


def test_get_nonexistent(service):
    assert service.get("no-such-id") is None


# ---------------------------------------------------------------------------
# multiple snippets
# ---------------------------------------------------------------------------

def test_multiple_snippets(service):
    s1 = service.add("First", "code_1()")
    s2 = service.add("Second", "code_2()")
    s3 = service.add("Third", "code_3()")

    all_snippets = service.load()
    assert len(all_snippets) == 3

    ids = {s.id for s in all_snippets}
    assert s1.id in ids
    assert s2.id in ids
    assert s3.id in ids

    # Delete middle one
    service.delete(s2.id)
    remaining = service.load()
    assert len(remaining) == 2
    remaining_ids = {s.id for s in remaining}
    assert s2.id not in remaining_ids
