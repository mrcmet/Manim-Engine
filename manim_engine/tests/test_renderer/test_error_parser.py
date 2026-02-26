"""Tests for renderer.error_parser — no Qt required."""
import pytest

from renderer.error_parser import ManimErrorParser, ParsedError


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

REALISTIC_STDERR = (
    "\x1b[0;31mTraceback (most recent call last):\x1b[0m\n"
    '  File "/tmp/manim_scene_abc.py", line 8, in construct\n'
    "    self.play(Create(Circl()))\n"
    "NameError: name 'Circl' is not defined\n"
)

SITE_PACKAGES_STDERR = (
    "Traceback (most recent call last):\n"
    '  File "/usr/lib/python3/site-packages/manim/scene/scene.py", line 200, in run\n'
    "    self.construct()\n"
    '  File "/tmp/manim_user_scene.py", line 12, in construct\n'
    "    self.play(FadeIn(obj))\n"
    "AttributeError: 'NoneType' object has no attribute 'animate'\n"
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStripAnsi:
    def test_removes_ansi_codes(self):
        result = ManimErrorParser.parse("\x1b[0;31mError\x1b[0m", None)
        assert "\x1b" not in result.cleaned_stderr

    def test_clean_text_unchanged(self):
        plain = "SomeError: something went wrong\n"
        result = ManimErrorParser.parse(plain, None)
        assert "SomeError: something went wrong" in result.cleaned_stderr


class TestParseNameError:
    def test_error_type(self):
        result = ManimErrorParser.parse(REALISTIC_STDERR, "/tmp/manim_scene_abc.py")
        assert result.error_type == "NameError"

    def test_message(self):
        result = ManimErrorParser.parse(REALISTIC_STDERR, "/tmp/manim_scene_abc.py")
        assert result.message == "name 'Circl' is not defined"

    def test_line_number(self):
        result = ManimErrorParser.parse(REALISTIC_STDERR, "/tmp/manim_scene_abc.py")
        assert result.line_number == 8

    def test_summary_format(self):
        result = ManimErrorParser.parse(REALISTIC_STDERR, "/tmp/manim_scene_abc.py")
        assert result.summary == "NameError on line 8: name 'Circl' is not defined"


class TestParseNoTraceback:
    def test_returns_fallback_summary(self):
        result = ManimErrorParser.parse("something went wrong\n", None)
        assert result.summary == "something went wrong"

    def test_no_crash(self):
        result = ManimErrorParser.parse("no traceback here", None)
        assert isinstance(result, ParsedError)

    def test_error_type_is_none(self):
        result = ManimErrorParser.parse("no traceback here", None)
        assert result.error_type is None

    def test_line_number_is_none(self):
        result = ManimErrorParser.parse("no traceback here", None)
        assert result.line_number is None


class TestSkipsSitePackagesFrames:
    def test_prefers_user_frame(self):
        result = ManimErrorParser.parse(SITE_PACKAGES_STDERR, "/tmp/manim_user_scene.py")
        assert result.line_number == 12

    def test_skips_site_packages_when_no_scene_file(self):
        result = ManimErrorParser.parse(SITE_PACKAGES_STDERR, None)
        # Without a scene_file hint, non-site-packages frame is chosen
        assert result.line_number == 12


class TestParseEmptyStderr:
    def test_no_crash(self):
        result = ManimErrorParser.parse("", None)
        assert isinstance(result, ParsedError)

    def test_summary_fallback(self):
        result = ManimErrorParser.parse("", None)
        assert result.summary == "Unknown render error"

    def test_cleaned_stderr_is_empty_string(self):
        result = ManimErrorParser.parse("", None)
        assert result.cleaned_stderr == ""


class TestSummaryFormats:
    def test_summary_with_line_number(self):
        stderr = (
            "Traceback (most recent call last):\n"
            '  File "/tmp/scene.py", line 5, in construct\n'
            "    foo()\n"
            "RuntimeError: bad state\n"
        )
        result = ManimErrorParser.parse(stderr, "/tmp/scene.py")
        assert result.summary == "RuntimeError on line 5: bad state"

    def test_summary_without_line_number(self):
        stderr = (
            "Traceback (most recent call last):\n"
            "RuntimeError: bad state\n"
        )
        result = ManimErrorParser.parse(stderr, None)
        # No File/line frame → line_number is None
        assert result.summary == "RuntimeError: bad state"
