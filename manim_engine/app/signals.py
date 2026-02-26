from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    # AI workflow
    prompt_submitted = Signal(str, bool)         # (prompt_text, include_code)
    ai_generation_started = Signal()
    ai_generation_finished = Signal(str)         # generated_code
    ai_generation_failed = Signal(str)           # error_message

    # Code editor
    code_changed = Signal(str)                   # current_code
    code_run_requested = Signal(str)             # code_to_render
    variables_extracted = Signal(list)            # list[VariableInfo]

    # Rendering
    render_started = Signal()
    render_progress = Signal(int)                # percent 0-100
    render_finished = Signal(str)                # output_video_path
    render_image_finished = Signal(str)          # output_image_path
    render_failed = Signal(str)                  # error_message
    render_failed_detail = Signal(object, str, str)  # (ParsedError, stdout, stderr)

    # Version timeline
    version_created = Signal(str)                # version_id
    version_selected = Signal(str)               # version_id
    version_loaded = Signal(str, str)            # (version_id, code)

    # Project
    project_opened = Signal(str)                 # project_id
    project_created = Signal(str)                # project_id
    project_list_changed = Signal()

    # Variable explorer
    variable_changed = Signal(str, object)       # (var_name, new_value)

    # Settings
    theme_changed = Signal(dict)                 # theme_dict
    settings_changed = Signal()


_bus_instance = None


def get_signal_bus() -> SignalBus:
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = SignalBus()
    return _bus_instance
