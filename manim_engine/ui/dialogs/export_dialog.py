from PySide6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QDialogButtonBox,
)


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Animation")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        self._quality = QComboBox()
        self._quality.addItems(["Low (480p)", "Medium (720p)", "High (1080p)", "4K (2160p)"])
        self._quality.setCurrentIndex(2)

        self._format = QComboBox()
        self._format.addItems(["mp4", "gif", "webm"])

        layout.addRow("Quality:", self._quality)
        layout.addRow("Format:", self._format)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> tuple[str, str]:
        quality_map = {0: "l", 1: "m", 2: "h", 3: "k"}
        return quality_map[self._quality.currentIndex()], self._format.currentText()
