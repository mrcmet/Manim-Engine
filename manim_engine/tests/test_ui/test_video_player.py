"""Tests for video player widget."""

import pytest
from PySide6.QtWidgets import QApplication
from ui.panels.preview_viewer.video_player_widget import VideoPlayerWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_video_player_instantiation(qapp):
    """Test that VideoPlayerWidget can be instantiated."""
    player = VideoPlayerWidget()
    assert player is not None
    assert player.media_player is not None
    assert player.video_widget is not None
    assert player.play_pause_button is not None
    assert player.stop_button is not None
    assert player.loop_checkbox is not None
    assert player.time_slider is not None
    assert player.time_label is not None


def test_time_label_formatting(qapp):
    """Test time formatting for the time label."""
    player = VideoPlayerWidget()

    # Test various time values
    assert player._format_time(0) == "0:00"
    assert player._format_time(1000) == "0:01"
    assert player._format_time(59000) == "0:59"
    assert player._format_time(60000) == "1:00"
    assert player._format_time(61000) == "1:01"
    assert player._format_time(125000) == "2:05"
    assert player._format_time(3661000) == "61:01"

    # Test negative values (should be treated as 0)
    assert player._format_time(-1000) == "0:00"


def test_initial_state(qapp):
    """Test initial widget state."""
    player = VideoPlayerWidget()

    # Check initial button states
    assert player.play_pause_button.text() == "Play"
    assert not player.play_pause_button.isChecked()
    assert player.loop_checkbox.isChecked()  # Loop enabled by default

    # Check initial slider and label
    assert player.time_slider.value() == 0
    assert player.time_slider.minimum() == 0
    assert player.time_slider.maximum() == 0
    assert player.time_label.text() == "0:00 / 0:00"


def test_clear_method(qapp):
    """Test that clear method resets widget state."""
    player = VideoPlayerWidget()

    # Simulate some state changes
    player.time_slider.setRange(0, 100000)
    player.time_slider.setValue(50000)
    player.play_pause_button.setChecked(True)

    # Clear and verify reset
    player.clear()

    assert player.time_slider.value() == 0
    assert player.time_slider.maximum() == 0
    assert player.time_label.text() == "0:00 / 0:00"
    assert not player.play_pause_button.isChecked()
    assert player.play_pause_button.text() == "Play"
