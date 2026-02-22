from unittest.mock import MagicMock, patch

from renderer.render_config import RenderConfig


class TestRenderConfig:
    def test_defaults(self):
        config = RenderConfig()
        assert config.quality == "l"
        assert config.format == "mp4"
        assert config.timeout == 30
        assert config.disable_caching is True

    def test_quality_flag(self):
        config = RenderConfig(quality="h")
        assert config.quality_flag == "h"
