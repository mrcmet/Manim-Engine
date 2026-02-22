import hashlib
import os

from core.services.settings_service import SettingsService


class AuthService:
    def __init__(self, settings_service: SettingsService):
        self._settings = settings_service

    def is_pin_set(self) -> bool:
        settings = self._settings.load()
        return settings.pin_hash is not None

    def set_pin(self, pin: str) -> None:
        salt = os.urandom(16).hex()
        pin_hash = self._hash_pin(pin, salt)
        settings = self._settings.load()
        settings.pin_hash = pin_hash
        settings.pin_salt = salt
        self._settings.save(settings)

    def verify_pin(self, pin: str) -> bool:
        settings = self._settings.load()
        if not settings.pin_hash or not settings.pin_salt:
            return False
        computed = self._hash_pin(pin, settings.pin_salt)
        return computed == settings.pin_hash

    def authenticate(self) -> bool:
        if not self.is_pin_set():
            # No PIN set — ask if user wants to set one
            return self._show_pin_setup()
        return self._show_pin_entry()

    def remove_pin(self) -> None:
        settings = self._settings.load()
        settings.pin_hash = None
        settings.pin_salt = None
        self._settings.save(settings)

    def _hash_pin(self, pin: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", pin.encode(), bytes.fromhex(salt), 100000
        ).hex()

    def _show_pin_setup(self) -> bool:
        from PySide6.QtWidgets import QMessageBox

        result = QMessageBox.question(
            None,
            "PIN Setup",
            "Would you like to set a PIN to protect your API keys?\n"
            "You can always set one later in Settings.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            from ui.dialogs.pin_dialog import PinDialog

            dialog = PinDialog(is_setup=True)
            if dialog.exec():
                pin = dialog.get_pin()
                if len(pin) >= 4:
                    self.set_pin(pin)
                    return True
                dialog.show_error("PIN must be at least 4 digits")
                return self._show_pin_setup()
            return False
        return True  # Skip PIN setup

    def _show_pin_entry(self) -> bool:
        from ui.dialogs.pin_dialog import PinDialog

        for _ in range(3):  # 3 attempts
            dialog = PinDialog(is_setup=False)
            if dialog.exec():
                if self.verify_pin(dialog.get_pin()):
                    return True
                dialog.show_error("Incorrect PIN")
            else:
                return False
        return False
