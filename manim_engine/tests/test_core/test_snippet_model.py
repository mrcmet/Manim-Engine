"""Tests for the Snippet data model."""

import pytest
from core.models.snippet import Snippet


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_to_dict_all_fields():
    snippet = Snippet(
        id="abc-123",
        name="Circle",
        code="class MyScene(Scene): pass",
        description="A circle scene",
        preview_image="/tmp/preview.png",
    )
    result = snippet.to_dict()
    assert result == {
        "id": "abc-123",
        "name": "Circle",
        "code": "class MyScene(Scene): pass",
        "description": "A circle scene",
        "preview_image": "/tmp/preview.png",
    }


def test_to_dict_optional_fields_none():
    snippet = Snippet(id="x", name="Bare", code="pass")
    result = snippet.to_dict()
    assert result["description"] is None
    assert result["preview_image"] is None


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------

def test_from_dict_all_fields():
    data = {
        "id": "uuid-1",
        "name": "Square",
        "code": "class S(Scene): pass",
        "description": "A square",
        "preview_image": "/img/sq.png",
    }
    snippet = Snippet.from_dict(data)
    assert snippet.id == "uuid-1"
    assert snippet.name == "Square"
    assert snippet.code == "class S(Scene): pass"
    assert snippet.description == "A square"
    assert snippet.preview_image == "/img/sq.png"


def test_from_dict_optional_fields_missing():
    data = {"id": "uuid-2", "name": "Minimal", "code": "pass"}
    snippet = Snippet.from_dict(data)
    assert snippet.description is None
    assert snippet.preview_image is None


def test_from_dict_raises_on_missing_required_fields():
    with pytest.raises(KeyError):
        Snippet.from_dict({"name": "No ID", "code": "pass"})

    with pytest.raises(KeyError):
        Snippet.from_dict({"id": "x", "code": "pass"})

    with pytest.raises(KeyError):
        Snippet.from_dict({"id": "x", "name": "No code"})


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_roundtrip():
    original = Snippet(
        id="round-trip-id",
        name="Roundtrip",
        code="x = 1",
        description="test",
        preview_image=None,
    )
    reconstructed = Snippet.from_dict(original.to_dict())
    assert reconstructed.id == original.id
    assert reconstructed.name == original.name
    assert reconstructed.code == original.code
    assert reconstructed.description == original.description
    assert reconstructed.preview_image == original.preview_image
