"""Video player widget for playing rendered Manim videos."""

from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl


class VideoPlayerWidget(QWidget):
    """Widget for playing video files with standard playback controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Video display widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        layout.addWidget(self.video_widget, stretch=1)

        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # Play/Pause button
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setCheckable(True)
        self.play_pause_button.setMaximumWidth(80)
        controls_layout.addWidget(self.play_pause_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setMaximumWidth(60)
        controls_layout.addWidget(self.stop_button)

        # Loop toggle
        self.loop_checkbox = QPushButton("Loop")
        self.loop_checkbox.setCheckable(True)
        self.loop_checkbox.setChecked(True)
        self.loop_checkbox.setMaximumWidth(60)
        controls_layout.addWidget(self.loop_checkbox)

        # Time slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 0)
        controls_layout.addWidget(self.time_slider, stretch=1)

        # Time label
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setMinimumWidth(100)
        self.time_label.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.time_label)

        layout.addLayout(controls_layout)

    def _setup_connections(self):
        """Connect signals and slots."""
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        self.stop_button.clicked.connect(self._stop_playback)
        self.time_slider.sliderMoved.connect(self._seek_to_position)

        self.media_player.positionChanged.connect(self._update_position)
        self.media_player.durationChanged.connect(self._update_duration)
        self.media_player.mediaStatusChanged.connect(self._handle_media_status)
        self.media_player.playbackStateChanged.connect(self._update_play_button)

    def load_video(self, path: Path):
        """Load a video file for playback.

        Args:
            path: Path to the video file
        """
        if not path.exists():
            return

        # Stop and clear so QMediaPlayer reloads even when URL is unchanged
        self.media_player.stop()
        self.media_player.setSource(QUrl())

        url = QUrl.fromLocalFile(str(path.resolve()))
        self.media_player.setSource(url)
        self.media_player.play()
        self.play_pause_button.setChecked(True)

    def clear(self):
        """Clear the current video and reset the player."""
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.time_slider.setValue(0)
        self.time_slider.setRange(0, 0)
        self.time_label.setText("0:00 / 0:00")
        self.play_pause_button.setChecked(False)
        self.play_pause_button.setText("Play")

    def _toggle_play_pause(self):
        """Toggle between play and pause states."""
        if self.play_pause_button.isChecked():
            self.media_player.play()
        else:
            self.media_player.pause()

    def _stop_playback(self):
        """Stop playback and reset to beginning."""
        self.media_player.stop()
        self.play_pause_button.setChecked(False)

    def _seek_to_position(self, position: int):
        """Seek to a specific position in the video.

        Args:
            position: Position in milliseconds
        """
        self.media_player.setPosition(position)

    def _update_position(self, position: int):
        """Update slider and time label when position changes.

        Args:
            position: Current position in milliseconds
        """
        if not self.time_slider.isSliderDown():
            self.time_slider.setValue(position)

        duration = self.media_player.duration()
        current_time = self._format_time(position)
        total_time = self._format_time(duration)
        self.time_label.setText(f"{current_time} / {total_time}")

    def _update_duration(self, duration: int):
        """Update slider range when duration is known.

        Args:
            duration: Video duration in milliseconds
        """
        self.time_slider.setRange(0, duration)

    def _handle_media_status(self, status):
        """Handle media status changes for looping.

        Args:
            status: QMediaPlayer.MediaStatus value
        """
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.loop_checkbox.isChecked():
                self.media_player.setPosition(0)
                self.media_player.play()

    def _update_play_button(self, state):
        """Update play/pause button text based on playback state.

        Args:
            state: QMediaPlayer.PlaybackState value
        """
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setText("Pause")
            self.play_pause_button.setChecked(True)
        else:
            self.play_pause_button.setText("Play")
            self.play_pause_button.setChecked(False)

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        """Format time in milliseconds as m:ss.

        Args:
            milliseconds: Time in milliseconds

        Returns:
            Formatted time string
        """
        if milliseconds < 0:
            milliseconds = 0

        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60

        return f"{minutes}:{seconds:02d}"
