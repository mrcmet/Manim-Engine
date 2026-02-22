# Agent 5: Preview Viewer & Prompt Panel

## Scope
Build the video preview player with playback controls and scrubbing, the render status overlay, and the prompt input panel with AI model selector and include-code toggle.

## Files to Create

```
manim_engine/
└── ui/
    └── panels/
        ├── preview_viewer/
        │   ├── __init__.py
        │   ├── preview_panel.py
        │   ├── video_player_widget.py
        │   └── render_status_overlay.py
        └── prompt_panel/
            ├── __init__.py
            ├── prompt_panel.py
            ├── prompt_input_widget.py
            └── prompt_history_widget.py
└── tests/
    └── test_ui/
        ├── test_video_player.py
        └── test_prompt_panel.py
```

---

## Detailed Specifications

### Preview Viewer

#### `video_player_widget.py`

```python
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PySide6.QtCore import Qt, QUrl, Signal
from pathlib import Path

class VideoPlayerWidget(QWidget):
    """Video player with play/pause, scrub slider, and time display."""

    def __init__(self):
        super().__init__()
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._video_widget = QVideoWidget()
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video_widget)
        self._audio.setVolume(0.5)

        # Controls
        self._play_btn = QPushButton("Play")
        self._stop_btn = QPushButton("Stop")
        self._loop_btn = QPushButton("Loop")  # toggleable
        self._loop_btn.setCheckable(True)
        self._loop_btn.setChecked(True)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 0)

        self._time_label = QLabel("0:00 / 0:00")

        # Layout
        controls = QHBoxLayout()
        controls.addWidget(self._play_btn)
        controls.addWidget(self._stop_btn)
        controls.addWidget(self._slider, stretch=1)
        controls.addWidget(self._time_label)
        controls.addWidget(self._loop_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._video_widget, stretch=1)
        layout.addLayout(controls)

        # Connections
        self._play_btn.clicked.connect(self._toggle_play)
        self._stop_btn.clicked.connect(self._stop)
        self._slider.sliderMoved.connect(self._seek)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.mediaStatusChanged.connect(self._on_status_changed)

    def load_video(self, path: Path):
        self._player.setSource(QUrl.fromLocalFile(str(path)))
        self._player.play()

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
            self._play_btn.setText("Play")
        else:
            self._player.play()
            self._play_btn.setText("Pause")

    def _stop(self):
        self._player.stop()
        self._play_btn.setText("Play")

    def _seek(self, position):
        self._player.setPosition(position)

    def _on_position_changed(self, position):
        if not self._slider.isSliderDown():
            self._slider.setValue(position)
        self._update_time_label(position, self._player.duration())

    def _on_duration_changed(self, duration):
        self._slider.setRange(0, duration)
        self._update_time_label(self._player.position(), duration)

    def _on_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia and self._loop_btn.isChecked():
            self._player.setPosition(0)
            self._player.play()

    def _update_time_label(self, pos_ms, dur_ms):
        def fmt(ms):
            s = ms // 1000
            return f"{s // 60}:{s % 60:02d}"
        self._time_label.setText(f"{fmt(pos_ms)} / {fmt(dur_ms)}")

    def clear(self):
        self._player.stop()
        self._player.setSource(QUrl())
        self._time_label.setText("0:00 / 0:00")
```

#### `render_status_overlay.py`

```python
class RenderStatusOverlay(QWidget):
    """Semi-transparent overlay shown on top of the video widget during rendering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._spinner_label = QLabel()  # Use QMovie with a loading GIF, or custom painted
        self._status_label = QLabel("Rendering...")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: white; font-size: 16px;")

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # indeterminate

        layout.addWidget(self._spinner_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_bar)

    def show_loading(self, message="Rendering..."):
        self._status_label.setText(message)
        self._progress_bar.setRange(0, 0)
        self.setVisible(True)

    def show_error(self, message: str):
        self._status_label.setText(f"Error: {message}")
        self._status_label.setStyleSheet("color: #ff6b6b; font-size: 14px;")
        self._progress_bar.setVisible(False)
        self.setVisible(True)

    def hide_overlay(self):
        self.setVisible(False)
        self._progress_bar.setVisible(True)
        self._status_label.setStyleSheet("color: white; font-size: 16px;")

    def paintEvent(self, event):
        """Paint semi-transparent dark background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        super().paintEvent(event)
```

#### `preview_panel.py`

```python
class PreviewPanel(QDockWidget):
    """Dockable preview viewer panel."""

    def __init__(self):
        super().__init__("Preview")
        self.setObjectName("preview_panel")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._player = VideoPlayerWidget()
        self._overlay = RenderStatusOverlay(self._player)

        layout.addWidget(self._player)
        self.setWidget(container)

    # Public interface:
    def load_video(self, path: Path):
        self._overlay.hide_overlay()
        self._player.load_video(path)

    def show_loading(self):
        self._overlay.show_loading()

    def show_error(self, message: str):
        self._overlay.show_error(message)

    def clear(self):
        self._player.clear()
        self._overlay.hide_overlay()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep overlay matching player size
        self._overlay.setGeometry(self._player.geometry())
```

---

### Prompt Panel

#### `prompt_input_widget.py`

```python
class PromptInputWidget(QWidget):
    """Text input area with send button, AI provider selector, and include-code toggle."""

    prompt_submitted = Signal(str, bool)  # (prompt_text, include_code)

    def __init__(self):
        super().__init__()

        # AI provider selector
        self._provider_combo = QComboBox()
        self._provider_combo.setToolTip("Select AI provider")

        # Include code toggle
        self._include_code_toggle = QCheckBox("Include current code")
        self._include_code_toggle.setChecked(False)
        self._include_code_toggle.setToolTip(
            "When checked, the current code is sent along with your prompt "
            "for the AI to modify. This creates a new version."
        )

        # Text input
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Describe the animation you want to create...")
        self._text_edit.setMaximumHeight(120)

        # Send button
        self._send_btn = QPushButton("Generate")
        self._send_btn.setShortcut(QKeySequence("Ctrl+Return"))
        self._send_btn.clicked.connect(self._on_send)

        # Layout
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("AI Provider:"))
        top_row.addWidget(self._provider_combo)
        top_row.addStretch()
        top_row.addWidget(self._include_code_toggle)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self._text_edit, stretch=1)
        bottom_row.addWidget(self._send_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

    def _on_send(self):
        text = self._text_edit.toPlainText().strip()
        if text:
            self.prompt_submitted.emit(text, self._include_code_toggle.isChecked())

    def set_providers(self, providers: list[str], active: str):
        self._provider_combo.clear()
        self._provider_combo.addItems(providers)
        idx = self._provider_combo.findText(active)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)

    def get_selected_provider(self) -> str:
        return self._provider_combo.currentText()

    def set_loading(self, loading: bool):
        self._send_btn.setEnabled(not loading)
        self._text_edit.setEnabled(not loading)
        self._send_btn.setText("Generating..." if loading else "Generate")

    def clear_input(self):
        self._text_edit.clear()
```

#### `prompt_history_widget.py`

```python
class PromptHistoryWidget(QScrollArea):
    """Scrollable history of prompt/response pairs for the current session."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.addStretch()
        self.setWidget(self._container)

    def add_entry(self, prompt: str, status: str = "pending"):
        """Add a prompt entry. Status: 'pending', 'success', 'error'."""
        entry = PromptHistoryEntry(prompt, status)
        # Insert before the stretch
        self._layout.insertWidget(self._layout.count() - 1, entry)
        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def update_last_entry(self, status: str, response_summary: str = ""):
        """Update the most recent entry's status."""

class PromptHistoryEntry(QFrame):
    """Single prompt entry with icon, text, and status indicator."""
    def __init__(self, prompt: str, status: str):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(self)
        self._status_icon = QLabel()  # colored dot
        self._prompt_label = QLabel(prompt)
        self._prompt_label.setWordWrap(True)
        layout.addWidget(self._status_icon)
        layout.addWidget(self._prompt_label, stretch=1)
        self.set_status(status)

    def set_status(self, status: str):
        colors = {"pending": "#fab387", "success": "#a6e3a1", "error": "#f38ba8"}
        self._status_icon.setStyleSheet(
            f"background: {colors.get(status, '#ccc')}; "
            f"border-radius: 5px; min-width: 10px; max-width: 10px; "
            f"min-height: 10px; max-height: 10px;"
        )
```

#### `prompt_panel.py`

```python
class PromptPanel(QDockWidget):
    """Dockable prompt panel with input and history."""

    def __init__(self):
        super().__init__("Prompt")
        self.setObjectName("prompt_panel")

        container = QWidget()
        layout = QVBoxLayout(container)

        self._history = PromptHistoryWidget()
        self._input = PromptInputWidget()

        layout.addWidget(self._history, stretch=1)
        layout.addWidget(self._input)
        self.setWidget(container)

    # Public interface:
    @property
    def prompt_submitted(self): return self._input.prompt_submitted

    def set_providers(self, providers, active):
        self._input.set_providers(providers, active)

    def get_selected_provider(self) -> str:
        return self._input.get_selected_provider()

    def set_loading(self, loading: bool):
        self._input.set_loading(loading)

    def add_history_entry(self, prompt, status="pending"):
        self._history.add_entry(prompt, status)

    def update_last_history(self, status, summary=""):
        self._history.update_last_entry(status, summary)

    def is_include_code_enabled(self) -> bool:
        return self._input._include_code_toggle.isChecked()
```

---

## Tests

**`test_video_player.py`**:
- Test VideoPlayerWidget instantiation (no crash)
- Test load_video with non-existent file (graceful handling)
- Test time label formatting

**`test_prompt_panel.py`**:
- Test PromptInputWidget emits prompt_submitted with correct args
- Test set_loading disables send button
- Test PromptHistoryWidget adds entries
- Test provider selector

## Verification

```bash
python -m pytest tests/test_ui/test_video_player.py tests/test_ui/test_prompt_panel.py -v

# Visual test - Preview:
python -c "
import sys
from PySide6.QtWidgets import QApplication
from ui.panels.preview_viewer.preview_panel import PreviewPanel
app = QApplication(sys.argv)
panel = PreviewPanel()
panel.show()
panel.resize(640, 480)
panel.show_loading()
app.exec()
"

# Visual test - Prompt:
python -c "
import sys
from PySide6.QtWidgets import QApplication
from ui.panels.prompt_panel.prompt_panel import PromptPanel
app = QApplication(sys.argv)
panel = PromptPanel()
panel.set_providers(['anthropic', 'openai', 'gemini', 'ollama'], 'anthropic')
panel.show()
panel.resize(400, 500)
app.exec()
"
```

## Dependencies on Other Agents
- None directly. Uses PySide6 QtMultimedia for video.

## What Other Agents Need From You
- Agent 7: `PreviewPanel` with `load_video()`, `show_loading()`, `show_error()`, `clear()`
- Agent 7: `PromptPanel` with `prompt_submitted` signal, `set_providers()`, `set_loading()`, `get_selected_provider()`
