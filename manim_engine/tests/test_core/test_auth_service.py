from core.services.settings_service import SettingsService
from core.services.auth_service import AuthService


class TestAuthService:
    def _make_service(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        ss = SettingsService(settings_file=settings_file)
        return AuthService(ss), ss

    def test_no_pin_by_default(self, tmp_path):
        auth, _ = self._make_service(tmp_path)
        assert auth.is_pin_set() is False

    def test_set_and_verify_pin(self, tmp_path):
        auth, _ = self._make_service(tmp_path)
        auth.set_pin("1234")
        assert auth.is_pin_set() is True
        assert auth.verify_pin("1234") is True
        assert auth.verify_pin("0000") is False

    def test_remove_pin(self, tmp_path):
        auth, _ = self._make_service(tmp_path)
        auth.set_pin("5678")
        assert auth.is_pin_set() is True
        auth.remove_pin()
        assert auth.is_pin_set() is False

    def test_different_pins_different_hashes(self, tmp_path):
        auth, ss = self._make_service(tmp_path)
        auth.set_pin("1111")
        hash1 = ss.load().pin_hash
        auth.set_pin("2222")
        hash2 = ss.load().pin_hash
        assert hash1 != hash2
