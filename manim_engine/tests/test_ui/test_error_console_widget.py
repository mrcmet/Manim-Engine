"""Tests for ErrorConsoleWidget."""
import pytest
from PySide6.QtWidgets import QApplication

from renderer.error_parser import ParsedError
from ui.panels.code_editor.error_console_widget import ErrorConsoleWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _make_parsed_error(
    error_type="NameError",
    message="name 'Circl' is not defined",
    line_number=8,
    summary="NameError on line 8: name 'Circl' is not defined",
    cleaned_stderr="NameError: name 'Circl' is not defined\n",
) -> ParsedError:
    return ParsedError(
        error_type=error_type,
        message=message,
        line_number=line_number,
        cleaned_stderr=cleaned_stderr,
        summary=summary,
    )


class TestErrorConsoleWidget:
    def test_hidden_by_default(self, qapp):
        widget = ErrorConsoleWidget()
        assert not widget.isVisible()

    def test_visible_after_show_error(self, qapp):
        widget = ErrorConsoleWidget()
        widget.show_error(_make_parsed_error(), "", "")
        assert widget.isVisible()

    def test_hidden_after_clear(self, qapp):
        widget = ErrorConsoleWidget()
        widget.show_error(_make_parsed_error(), "", "")
        widget.clear()
        assert not widget.isVisible()

    def test_dismiss_button_hides_widget(self, qapp):
        widget = ErrorConsoleWidget()
        widget.show_error(_make_parsed_error(), "", "")
        widget._dismiss_btn.click()
        assert not widget.isVisible()

    def test_dismiss_emits_signal(self, qapp):
        widget = ErrorConsoleWidget()
        widget.show_error(_make_parsed_error(), "", "")
        received = []
        widget.dismissed.connect(lambda: received.append(True))
        widget._dismiss_btn.click()
        assert received == [True]

    def test_text_area_contains_summary(self, qapp):
        widget = ErrorConsoleWidget()
        pe = _make_parsed_error()
        widget.show_error(pe, "", "")
        text = widget._text_area.toPlainText()
        assert pe.summary in text
