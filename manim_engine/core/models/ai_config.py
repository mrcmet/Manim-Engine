from dataclasses import dataclass


@dataclass
class AIProviderConfig:
    provider_name: str  # "anthropic", "openai", "gemini", "ollama"
    api_key: str | None = None
    model_name: str = ""
    base_url: str | None = None  # for Ollama
    max_tokens: int = 4096
    temperature: float = 0.7

    def to_dict(self) -> dict:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            # API key NOT serialized — stored in keyring
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AIProviderConfig":
        return cls(
            provider_name=data["provider_name"],
            api_key=data.get("api_key"),
            model_name=data.get("model_name", ""),
            base_url=data.get("base_url"),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
        )
